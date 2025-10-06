import discord
from discord.ext import commands
from loguru import logger
import config
from pathlib import Path
from database.connection import AsyncSessionLocal
from bot.utils.database import ensure_guild


class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        intents.voice_states = True
        intents.guilds = True

        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            owner_id=config.OWNER_ID,
            strip_after_prefix=True
        )

        self.color = config.EMBED_COLOR
        self.guild_prefix_cache: dict[int, str] = {}
        self._synced_once = False
        self.bot_name = None

    async def get_prefix(self, message):
        if not message.guild:
            return commands.when_mentioned_or(config.DEFAULT_PREFIX)(self, message)

        cached = self.guild_prefix_cache.get(message.guild.id)
        if cached:
            return commands.when_mentioned_or(cached)(self, message)

        async with AsyncSessionLocal() as session:
            guild, created = await ensure_guild(session, message.guild)
            if created and guild.prefix != config.DEFAULT_PREFIX:
                guild.prefix = config.DEFAULT_PREFIX
            await session.commit()
            prefix = guild.prefix or config.DEFAULT_PREFIX

        self.guild_prefix_cache[message.guild.id] = prefix
        return commands.when_mentioned_or(prefix)(self, message)

    async def setup_hook(self):
        logger.info("Loading cogs")
        cogs_path = Path(__file__).parent / "cogs"

        for cog_file in cogs_path.glob("*.py"):
            if cog_file.name.startswith("_"):
                continue
            try:
                await self.load_extension(f"bot.cogs.{cog_file.stem}")
                logger.success(f"Loaded cog: {cog_file.stem}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog_file.stem}: {e}")

        logger.info("Loading events")
        events_path = Path(__file__).parent / "events"

        for event_file in events_path.glob("*.py"):
            if event_file.name.startswith("_"):
                continue
            try:
                await self.load_extension(f"bot.events.{event_file.stem}")
                logger.success(f"Loaded event: {event_file.stem}")
            except Exception as e:
                logger.error(f"Failed to load event {event_file.stem}: {e}")

        logger.info("Syncing global commands")
        try:
            await self.tree.sync()
            logger.success("Commands synced")
        except Exception as e:
            logger.error(f"Command sync failed: {e}")

    async def on_ready(self):
        self.bot_name = self.user.name

        from bot.utils import embeds
        embeds.set_bot_instance(self)

        logger.success(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")

        if not self._synced_once:
            for guild in self.guilds:
                try:
                    await self.tree.sync(guild=guild)
                    logger.info(f"Commands synced for guild {guild.id}")
                except Exception as e:
                    logger.error(f"Failed to sync commands for guild {guild.id}: {e}")
            self._synced_once = True

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers"
            ),
            status=discord.Status.online
        )

    async def on_guild_join(self, guild):
        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, guild)
            if guild_record.prefix != config.DEFAULT_PREFIX:
                guild_record.prefix = config.DEFAULT_PREFIX
            guild_record.name = guild.name
            await session.commit()
            self.guild_prefix_cache[guild.id] = guild_record.prefix

        try:
            await self.tree.sync(guild=guild)
            logger.info(f"Commands synced for new guild: {guild.name} ({guild.id})")
        except Exception as e:
            logger.error(f"Failed to sync commands for new guild {guild.id}: {e}")

        logger.info(f"Created or updated database entry for guild: {guild.name} ({guild.id})")

    async def on_guild_remove(self, guild):
        self.guild_prefix_cache.pop(guild.id, None)
        logger.info(f"Removed from guild: {guild.name} ({guild.id})")

    def set_guild_prefix(self, guild_id: int, prefix: str):
        self.guild_prefix_cache[guild_id] = prefix

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=discord.Embed(
                description="❌ You don't have permission to use this command.",
                color=discord.Color.red()
            ))
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(
                description="❌ I don't have the required permissions to execute this command.",
                color=discord.Color.red()
            ))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=discord.Embed(
                description=f"❌ Missing required argument: `{error.param.name}`",
                color=discord.Color.red()
            ))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=discord.Embed(
                description=f"⏰ This command is on cooldown. Try again in {error.retry_after:.1f}s",
                color=discord.Color.orange()
            ))
        else:
            logger.error(f"Command error in {ctx.command}: {error}")
            await ctx.send(embed=discord.Embed(
                description="❌ An error occurred while executing this command.",
                color=discord.Color.red()
            ))
