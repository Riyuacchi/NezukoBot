import discord
from discord.ext import commands
from database.connection import AsyncSessionLocal
from bot.utils.database import ensure_guild
from bot.utils.embeds import info_embed
import config


class OnMemberRemove(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        async with AsyncSessionLocal() as session:
            guild_record, created = await ensure_guild(session, member.guild)
            if created and guild_record.prefix != config.DEFAULT_PREFIX:
                guild_record.prefix = config.DEFAULT_PREFIX
            goodbye_enabled = guild_record.goodbye_enabled
            goodbye_channel_id = guild_record.goodbye_channel_id
            goodbye_message = guild_record.goodbye_message
            await session.commit()

        if goodbye_enabled and goodbye_channel_id:
            await self._send_goodbye(member, goodbye_channel_id, goodbye_message)

    async def _send_goodbye(self, member: discord.Member, channel_id: int, template: str | None):
        channel = member.guild.get_channel(channel_id)
        if not channel:
            return
        message = template or "{username} left {server}."
        message = message.replace("{user}", member.name)
        message = message.replace("{username}", member.name)
        message = message.replace("{server}", member.guild.name)
        message = message.replace("{membercount}", str(member.guild.member_count))
        embed = info_embed(message, "Goodbye")
        embed.set_footer(text=f"ID: {member.id}")
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(OnMemberRemove(bot))
