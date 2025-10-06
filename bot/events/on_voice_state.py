import discord
from discord.ext import commands
from datetime import datetime
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import VoiceChannel
from bot.utils.database import ensure_guild, ensure_member
from bot.utils.helpers import calculate_level
from bot.utils.embeds import success_embed
import random
import config


class OnVoiceState(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_sessions: dict[int, datetime] = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot or not member.guild:
            return

        async with AsyncSessionLocal() as session:
            guild_record, _ = await ensure_guild(session, member.guild)
            voice_rows = await session.execute(
                select(VoiceChannel).where(VoiceChannel.guild_id == member.guild.id)
            )
            voice_entries = voice_rows.scalars().all()
            lobby_ids = {entry.channel_id for entry in voice_entries if entry.owner_id == 0}
            owner_entry = next((entry for entry in voice_entries if entry.owner_id == member.id), None)
            temp_entries = {entry.channel_id: entry for entry in voice_entries if entry.owner_id != 0}

            if guild_record.voice_channels_enabled and after.channel and after.channel.id in lobby_ids:
                await self._create_temp_voice(member, session, guild_record, owner_entry)

            if before.channel and before.channel.id in temp_entries and len(before.channel.members) == 0:
                await self._remove_temp_voice(before.channel, session, temp_entries[before.channel.id])

            await session.commit()

        should_stop = not after.channel or after.self_deaf or after.deaf
        if should_stop:
            started = self.voice_sessions.pop(member.id, None)
            if started:
                await self._grant_voice_xp(member, started)
        else:
            self.voice_sessions.setdefault(member.id, datetime.utcnow())

    async def _create_temp_voice(self, member: discord.Member, session: AsyncSessionLocal, guild_record, owner_entry: VoiceChannel | None):
        guild = member.guild
        category = guild.get_channel(guild_record.voice_channels_category_id) if guild_record.voice_channels_category_id else None
        if not isinstance(category, discord.CategoryChannel):
            if member.voice and member.voice.channel and member.voice.channel.category:
                category = member.voice.channel.category
            else:
                try:
                    category = await guild.create_category("🎙️ Temporary Voice")
                except discord.Forbidden:
                    category = None
            if category:
                guild_record.voice_channels_category_id = category.id

        if owner_entry:
            existing_channel = guild.get_channel(owner_entry.channel_id)
            if existing_channel:
                try:
                    await member.move_to(existing_channel)
                    self.voice_sessions.setdefault(member.id, datetime.utcnow())
                    return
                except discord.Forbidden:
                    pass
            await session.delete(owner_entry)

        template = guild_record.voice_channels_template or "Voice room - {username}"
        name = template.replace("{username}", member.display_name)
        name = name.replace("{user}", member.name)
        name = name.replace("{server}", guild.name)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True),
            member: discord.PermissionOverwrite(
                connect=True,
                manage_channels=True,
                move_members=True,
                mute_members=True,
                deafen_members=True
            )
        }

        try:
            channel = await guild.create_voice_channel(name, category=category, overwrites=overwrites)
        except discord.Forbidden:
            return

        session.add(VoiceChannel(guild_id=guild.id, channel_id=channel.id, owner_id=member.id, name=channel.name))
        try:
            await member.move_to(channel)
            self.voice_sessions.setdefault(member.id, datetime.utcnow())
        except discord.Forbidden:
            pass

    async def _remove_temp_voice(self, channel: discord.VoiceChannel, session: AsyncSessionLocal, entry: VoiceChannel):
        await session.delete(entry)
        try:
            await channel.delete(reason="Temporary voice channel cleaned up")
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

    async def _grant_voice_xp(self, member: discord.Member, started: datetime):
        elapsed = datetime.utcnow() - started
        minutes = int(elapsed.total_seconds() // 60)
        if minutes <= 0:
            return

        async with AsyncSessionLocal() as session:
            guild_record, created = await ensure_guild(session, member.guild)
            if created and guild_record.prefix != config.DEFAULT_PREFIX:
                guild_record.prefix = config.DEFAULT_PREFIX
            if not guild_record.level_enabled:
                await session.commit()
                return
            member_record, _ = await ensure_member(session, member.guild.id, member)
            xp_gain = random.randint(10, 16) * minutes
            member_record.voice_time += minutes
            member_record.xp += xp_gain
            new_level = calculate_level(member_record.xp)
            leveled_up = False
            if new_level > member_record.level:
                member_record.level = new_level
                leveled_up = True
            await session.commit()

        if leveled_up:
            embed = success_embed(f"{member.mention} reached level {member_record.level}", "Voice progression")
            embed.set_thumbnail(url=member.display_avatar.url)
            channel = member.guild.system_channel or self._fallback_channel(member.guild)
            if channel:
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    def _fallback_channel(self, guild: discord.Guild):
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                return channel
        return None


async def setup(bot: commands.Bot):
    await bot.add_cog(OnVoiceState(bot))
