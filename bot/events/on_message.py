import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
from collections import defaultdict
from database.connection import AsyncSessionLocal
from bot.utils.database import ensure_guild, ensure_member
from bot.utils.embeds import warning_embed, success_embed
from bot.utils.helpers import calculate_level
import config


class OnMessage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_window = defaultdict(list)

    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        async with AsyncSessionLocal() as session:
            guild_record, created = await ensure_guild(session, message.guild)
            if created and guild_record.prefix != config.DEFAULT_PREFIX:
                guild_record.prefix = config.DEFAULT_PREFIX
            moderation_blocked = False
            if guild_record.moderation_enabled and self._is_spam(message.author.id):
                moderation_blocked = True
            if moderation_blocked:
                await session.commit()
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                await self._send_rate_limit_warning(message)
                return
            member_record, member_created = await ensure_member(session, message.guild.id, message.author)
            leveled_up = False
            xp_gain = 0
            new_level_value = member_record.level
            if guild_record.level_enabled:
                xp_gain = random.randint(15, 25)
                member_record.xp += xp_gain
                new_level = calculate_level(member_record.xp)
                if new_level > member_record.level:
                    member_record.level = new_level
                    new_level_value = new_level
                    leveled_up = True
            member_record.messages_count += 1
            await session.commit()

        await self.bot.process_commands(message)

        if leveled_up:
            await self._announce_level_up(message, new_level_value, xp_gain)

    def _is_spam(self, user_id: int) -> bool:
        now = datetime.utcnow()
        window = timedelta(seconds=6)
        records = [stamp for stamp in self.message_window[user_id] if now - stamp <= window]
        records.append(now)
        self.message_window[user_id] = records
        return len(records) >= 5

    async def _send_rate_limit_warning(self, message: discord.Message):
        embed = warning_embed("You are sending messages too quickly. Please slow down!", "Moderation")
        try:
            await message.channel.send(message.author.mention, embed=embed, delete_after=6)
        except discord.Forbidden:
            pass

    async def _announce_level_up(self, message: discord.Message, level: int, xp_gain: int):
        embed = success_embed(f"You just earned {xp_gain} XP and reached level {level}!", "Level Up")
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        try:
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(OnMessage(bot))
