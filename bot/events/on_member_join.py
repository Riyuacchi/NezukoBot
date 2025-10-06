import discord
from discord.ext import commands
from sqlalchemy import select
from database.connection import AsyncSessionLocal
from database.models import AutoRole
from bot.utils.database import ensure_guild, ensure_member
from bot.utils.embeds import info_embed
import config


class OnMemberJoin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        async with AsyncSessionLocal() as session:
            guild_record, created = await ensure_guild(session, member.guild)
            if created and guild_record.prefix != config.DEFAULT_PREFIX:
                guild_record.prefix = config.DEFAULT_PREFIX
            autorole_ids = []
            result = await session.execute(
                select(AutoRole).where(
                    AutoRole.guild_id == member.guild.id,
                    AutoRole.enabled == True
                )
            )
            autorole_ids = [entry.role_id for entry in result.scalars().all()]
            await ensure_member(session, member.guild.id, member)
            welcome_enabled = guild_record.welcome_enabled
            welcome_channel_id = guild_record.welcome_channel_id
            welcome_message = guild_record.welcome_message
            await session.commit()

        if welcome_enabled and welcome_channel_id:
            await self._send_welcome(member, welcome_channel_id, welcome_message)

        if autorole_ids:
            await self._assign_roles(member, autorole_ids)

    async def _send_welcome(self, member: discord.Member, channel_id: int, template: str | None):
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return
        message = template or "Welcome {user} to {server}!"
        message = message.replace("{user}", member.mention)
        message = message.replace("{username}", member.name)
        message = message.replace("{server}", member.guild.name)
        message = message.replace("{membercount}", str(member.guild.member_count))
        embed = info_embed(message, "Welcome")
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    async def _assign_roles(self, member: discord.Member, role_ids: list[int]):
        roles = [member.guild.get_role(role_id) for role_id in role_ids]
        roles = [role for role in roles if role]
        if not roles:
            return
        try:
            await member.add_roles(*roles, reason="Auto role on join")
        except discord.Forbidden:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(OnMemberJoin(bot))
