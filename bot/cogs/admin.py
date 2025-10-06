import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional
import random
from sqlalchemy import select, delete
from database.connection import AsyncSessionLocal
from database.models import Guild, Ticket, TicketStatus, Giveaway, AutoRole, VoiceChannel
from bot.utils.embeds import info_embed, success_embed, error_embed
from bot.utils.checks import is_admin
from bot.utils.database import ensure_guild
import config


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_embed(self, ctx: commands.Context, embed: discord.Embed, *, ephemeral: bool = False):
        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(embed=embed, ephemeral=ephemeral)
            else:
                await ctx.interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await ctx.send(embed=embed)

    @commands.hybrid_group(name="setup", description="Configure bot")
    @is_admin()
    async def setup(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await self._send_overview(ctx)

    async def _send_overview(self, ctx: commands.Context):
        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, ctx.guild)
            autoroles = await session.execute(
                select(AutoRole).where(
                    AutoRole.guild_id == ctx.guild.id,
                    AutoRole.enabled == True
                )
            )
            autorole_count = len(autoroles.scalars().all())
            await session.commit()

        embed = info_embed(f"Current configuration for {ctx.guild.name}", "Configuration")
        embed.add_field(name="Prefix", value=guild_record.prefix or config.DEFAULT_PREFIX, inline=True)
        embed.add_field(name="Language", value=guild_record.language.upper(), inline=True)
        embed.add_field(name="Autoroles", value=str(autorole_count), inline=True)
        embed.add_field(name="Welcome", value="Enabled" if guild_record.welcome_enabled else "Disabled", inline=True)
        embed.add_field(name="Goodbye", value="Enabled" if guild_record.goodbye_enabled else "Disabled", inline=True)
        embed.add_field(name="Moderation", value="Enabled" if guild_record.moderation_enabled else "Disabled", inline=True)
        embed.add_field(name="Tickets", value="Enabled" if guild_record.tickets_enabled else "Disabled", inline=True)
        embed.add_field(name="Temporary Voice", value="Enabled" if guild_record.voice_channels_enabled else "Disabled", inline=True)
        await self.send_embed(ctx, embed)

    @setup.command(name="general", description="Update prefix or language")
    @is_admin()
    async def setup_general(self, ctx: commands.Context, prefix: Optional[str] = None, language: Optional[str] = None):
        if not prefix and not language:
            await self.send_embed(ctx, error_embed("Provide at least one option."), ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, ctx.guild)
            changed = False
            if prefix:
                if len(prefix) > 10:
                    await self.send_embed(ctx, error_embed("Prefix must be 10 characters or fewer."), ephemeral=True)
                    return
                guild_record.prefix = prefix
                self.bot.set_guild_prefix(ctx.guild.id, prefix)
                changed = True
            if language:
                language = language.lower()
                if language not in {"en", "fr"}:
                    await self.send_embed(ctx, error_embed("Invalid language. Choose 'en' or 'fr'."), ephemeral=True)
                    return
                guild_record.language = language
                changed = True
            if not changed:
                await self.send_embed(ctx, info_embed("No changes detected."), ephemeral=True)
                return
            await session.commit()

        await self.send_embed(ctx, success_embed("General settings updated."), ephemeral=True)

    @setup.command(name="welcome", description="Configure welcome message automatically")
    @is_admin()
    async def setup_welcome(self, ctx: commands.Context):
        channel = await ctx.guild.create_text_channel("welcome", overwrites={
            ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=True)
        })

        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, ctx.guild)
            guild_record.welcome_enabled = True
            guild_record.welcome_channel_id = channel.id
            guild_record.welcome_message = "Welcome {user} to {server}!"
            await session.commit()

        await self.send_embed(ctx, success_embed(f"Welcome system configured. Channel: {channel.mention}"))

    @setup.command(name="goodbye", description="Configure goodbye message automatically")
    @is_admin()
    async def setup_goodbye(self, ctx: commands.Context):
        channel = await ctx.guild.create_text_channel("goodbye", overwrites={
            ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=True)
        })

        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, ctx.guild)
            guild_record.goodbye_enabled = True
            guild_record.goodbye_channel_id = channel.id
            guild_record.goodbye_message = "Goodbye {user}!"
            await session.commit()

        await self.send_embed(ctx, success_embed(f"Goodbye system configured. Channel: {channel.mention}"))

    @setup.command(name="voice", description="Set up temporary voice channels automatically")
    @is_admin()
    async def setup_voice(self, ctx: commands.Context):
        guild = ctx.guild
        if not guild.me.guild_permissions.manage_channels:
            await self.send_embed(ctx, error_embed("I need the Manage Channels permission."), ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, guild)

            category = await guild.create_category("🎙️ Temporary Voice")

            overwrites = {guild.default_role: discord.PermissionOverwrite(connect=True)}
            lobby_channel = await guild.create_voice_channel("➕ Create a channel", category=category, overwrites=overwrites)

            session.add(VoiceChannel(guild_id=guild.id, channel_id=lobby_channel.id, owner_id=0, name=lobby_channel.name))

            guild_record.voice_channels_enabled = True
            guild_record.voice_channels_category_id = category.id
            guild_record.voice_channels_template = "Voice room - {username}"
            await session.commit()

        embed = success_embed("Temporary voice channels configured automatically.")
        embed.add_field(name="Category", value=category.mention, inline=True)
        embed.add_field(name="Lobby channel", value=lobby_channel.mention, inline=True)
        await self.send_embed(ctx, embed)

    @setup.command(name="voice_disable", description="Disable temporary voice channels")
    @is_admin()
    async def setup_voice_disable(self, ctx: commands.Context):
        guild = ctx.guild
        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, guild)
            result = await session.execute(
                select(VoiceChannel).where(VoiceChannel.guild_id == guild.id)
            )
            entries = result.scalars().all()
            for entry in entries:
                channel = guild.get_channel(entry.channel_id)
                if channel:
                    try:
                        await channel.delete(reason="Temporary voice cleanup")
                    except discord.Forbidden:
                        pass
                    except discord.HTTPException:
                        pass
                await session.delete(entry)
            guild_record.voice_channels_enabled = False
            guild_record.voice_channels_category_id = None
            guild_record.voice_channels_template = None
            await session.commit()

        await self.send_embed(ctx, success_embed("Temporary voice channels disabled."), ephemeral=True)

    @commands.hybrid_command(name="automod", description="Toggle automatic moderation")
    @is_admin()
    async def automod(self, ctx: commands.Context, enabled: bool):
        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, ctx.guild)
            guild_record.moderation_enabled = enabled
            await session.commit()
        status = "enabled" if enabled else "disabled"
        await self.send_embed(ctx, success_embed(f"Auto moderation {status}."))

    @setup.command(name="tickets", description="Set up ticket system automatically")
    @is_admin()
    async def setup_tickets(self, ctx: commands.Context):
        category = await ctx.guild.create_category("📩 Tickets")
        log_channel = await ctx.guild.create_text_channel("ticket-logs", category=category, overwrites={
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)
        })

        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, ctx.guild)
            guild_record.tickets_enabled = True
            guild_record.tickets_category_id = category.id
            guild_record.tickets_log_channel_id = log_channel.id
            await session.commit()

        await self.send_embed(ctx, success_embed(f"Ticket system configured. Category: {category.mention}, Logs: {log_channel.mention}"))

    @commands.hybrid_command(name="ticket", description="Manage tickets")
    @is_admin()
    async def ticket(self, ctx: commands.Context, action: str):
        async with AsyncSessionLocal() as session:
            if action == "close":
                if not isinstance(ctx.channel, discord.TextChannel):
                    return
                result = await session.execute(
                    select(Ticket).where(Ticket.channel_id == ctx.channel.id)
                )
                ticket = result.scalar_one_or_none()
                if not ticket:
                    await self.send_embed(ctx, error_embed("This channel is not tracked as a ticket."), ephemeral=True)
                    return
                ticket.status = TicketStatus.CLOSED
                ticket.closed_by = ctx.author.id
                ticket.closed_at = datetime.utcnow()
                await session.commit()
                await self.send_embed(ctx, success_embed("Ticket closed. This channel will be deleted in 5 seconds."))
                await discord.utils.sleep_until(datetime.utcnow() + timedelta(seconds=5))
                await ctx.channel.delete()
                return
            await self.send_embed(ctx, error_embed("Unknown action."), ephemeral=True)

    @commands.hybrid_command(name="giveaway", description="Create a giveaway")
    @is_admin()
    async def giveaway(self, ctx: commands.Context, duration_minutes: int, winners: int, *, prize: str):
        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        embed = discord.Embed(
            title="🎉 Giveaway",
            description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(end_time.timestamp())}:R>",
            color=discord.Color.gold(),
            timestamp=end_time
        )
        embed.set_footer(text="React with 🎉 to join")
        message = await ctx.send(embed=embed)
        await message.add_reaction("🎉")

        async with AsyncSessionLocal() as session:
            giveaway = Giveaway(
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                message_id=message.id,
                prize=prize,
                winners_count=winners,
                host_id=ctx.author.id,
                participants=[],
                winners=[],
                active=True,
                end_time=end_time
            )
            session.add(giveaway)
            await session.commit()

    @commands.hybrid_command(name="autorole", description="Manage autoroles")
    @is_admin()
    async def autorole(self, ctx: commands.Context, action: str, role: Optional[discord.Role] = None):
        async with AsyncSessionLocal() as session:
            if action == "add":
                if not role:
                    await self.send_embed(ctx, error_embed("Select a role."), ephemeral=True)
                    return
                existing = await session.execute(
                    select(AutoRole).where(
                        AutoRole.guild_id == ctx.guild.id,
                        AutoRole.role_id == role.id
                    )
                )
                if existing.scalar_one_or_none():
                    await self.send_embed(ctx, error_embed("This role is already configured."), ephemeral=True)
                    return
                session.add(AutoRole(guild_id=ctx.guild.id, role_id=role.id))
                await session.commit()
                await self.send_embed(ctx, success_embed(f"{role.mention} added to autoroles."))
                return
            if action == "remove":
                if not role:
                    await self.send_embed(ctx, error_embed("Select a role."), ephemeral=True)
                    return
                await session.execute(
                    delete(AutoRole).where(
                        AutoRole.guild_id == ctx.guild.id,
                        AutoRole.role_id == role.id
                    )
                )
                await session.commit()
                await self.send_embed(ctx, success_embed(f"{role.mention} removed from autoroles."))
                return
            if action == "list":
                result = await session.execute(
                    select(AutoRole).where(
                        AutoRole.guild_id == ctx.guild.id,
                        AutoRole.enabled == True
                    )
                )
                roles = []
                for autorole in result.scalars().all():
                    role_obj = ctx.guild.get_role(autorole.role_id)
                    if role_obj:
                        roles.append(role_obj.mention)
                description = "\n".join(roles) if roles else "No roles configured."
                await self.send_embed(ctx, info_embed(description, "Autoroles"))
                return
            await self.send_embed(ctx, error_embed("Unknown action."), ephemeral=True)

    @setup.command(name="logs", description="Configure logging automatically")
    @is_admin()
    async def setup_logs(self, ctx: commands.Context):
        channel = await ctx.guild.create_text_channel("bot-logs", overwrites={
            ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False)
        })

        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, ctx.guild)
            guild_record.log_channel_id = channel.id
            guild_record.log_events = {
                "message_delete": True,
                "message_edit": True,
                "member_join": True,
                "member_leave": True,
                "member_ban": True,
                "member_unban": True,
                "channel_create": True,
                "channel_delete": True,
                "role_create": True,
                "role_delete": True
            }
            await session.commit()

        await self.send_embed(ctx, success_embed(f"Logging enabled in {channel.mention}."))


async def setup(bot):
    await bot.add_cog(Admin(bot))
