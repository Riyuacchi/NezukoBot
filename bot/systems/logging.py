import discord
from discord.ext import commands
from sqlalchemy import select
from datetime import datetime
from typing import Optional
from bot.database import AsyncSessionLocal
from bot.models import LoggingConfig


class LoggingSystem:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_config(self, guild_id: int) -> Optional[LoggingConfig]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(LoggingConfig).where(LoggingConfig.guild_id == guild_id)
            )
            return result.scalar_one_or_none()

    async def create_default_config(self, guild_id: int) -> LoggingConfig:
        async with AsyncSessionLocal() as session:
            config = LoggingConfig(
                guild_id=guild_id,
                enabled=True,
                log_channel_id=None,
                log_messages=True,
                log_members=True,
                log_roles=True,
                log_channels=True,
                log_voice=True,
                log_moderation=True,
                log_server=True,
                ignored_channels=[],
                ignored_users=[]
            )
            session.add(config)
            await session.commit()
            await session.refresh(config)
            return config

    async def should_log(self, guild_id: int, log_type: str) -> tuple[bool, Optional[int]]:
        config = await self.get_config(guild_id)
        if not config or not config.enabled or not config.log_channel_id:
            return False, None

        log_enabled = getattr(config, f"log_{log_type}", False)
        return log_enabled, config.log_channel_id

    async def send_log(self, guild: discord.Guild, embed: discord.Embed, log_type: str):
        should_log, channel_id = await self.should_log(guild.id, log_type)
        if not should_log or not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        try:
            await channel.send(embed=embed)
        except:
            pass

    async def log_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        config = await self.get_config(message.guild.id)
        if config and message.channel.id in config.ignored_channels:
            return
        if config and message.author.id in config.ignored_users:
            return

        embed = discord.Embed(
            title="Message Deleted",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Author", value=message.author.mention, inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)

        content = message.content[:1024] if message.content else "*No text content*"
        embed.add_field(name="Content", value=content, inline=False)

        if message.attachments:
            embed.add_field(
                name="Attachments",
                value="\n".join([att.filename for att in message.attachments]),
                inline=False
            )

        embed.set_footer(text=f"ID: {message.id}")

        await self.send_log(message.guild, embed, "messages")

    async def log_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot or not after.guild or before.content == after.content:
            return

        config = await self.get_config(after.guild.id)
        if config and after.channel.id in config.ignored_channels:
            return
        if config and after.author.id in config.ignored_users:
            return

        embed = discord.Embed(
            title="Message Edited",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Author", value=after.author.mention, inline=True)
        embed.add_field(name="Channel", value=after.channel.mention, inline=True)

        before_content = before.content[:512] if before.content else "*No content*"
        after_content = after.content[:512] if after.content else "*No content*"

        embed.add_field(name="Before", value=before_content, inline=False)
        embed.add_field(name="After", value=after_content, inline=False)
        embed.add_field(name="Link", value=f"[Jump to message]({after.jump_url})", inline=False)

        embed.set_footer(text=f"ID: {after.id}")

        await self.send_log(after.guild, embed, "messages")

    async def log_member_join(self, member: discord.Member):
        embed = discord.Embed(
            title="Member Joined",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Member", value=f"{member.mention}\n{member}", inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(
            name="Account created",
            value=f"<t:{int(member.created_at.timestamp())}:R>",
            inline=False
        )
        embed.set_footer(text=f"Members: {member.guild.member_count}")

        await self.send_log(member.guild, embed, "members")

    async def log_member_remove(self, member: discord.Member):
        embed = discord.Embed(
            title="Member Left",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Member", value=f"{member.mention}\n{member}", inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)

        if member.joined_at:
            embed.add_field(
                name="Joined",
                value=f"<t:{int(member.joined_at.timestamp())}:R>",
                inline=False
            )

        roles = [role.mention for role in member.roles[1:]]
        if roles:
            embed.add_field(name="Roles", value=", ".join(roles), inline=False)

        embed.set_footer(text=f"Members: {member.guild.member_count}")

        await self.send_log(member.guild, embed, "members")

    async def log_member_update(self, before: discord.Member, after: discord.Member):
        embed = None

        if before.nick != after.nick:
            embed = discord.Embed(
                title="Nickname Updated",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.add_field(name="Member", value=after.mention, inline=False)
            embed.add_field(name="Before", value=before.nick or before.name, inline=True)
            embed.add_field(name="After", value=after.nick or after.name, inline=True)

        elif before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="Roles Updated",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url=after.display_avatar.url)
            embed.add_field(name="Member", value=after.mention, inline=False)

                if added_roles:
                    embed.add_field(
                        name="Roles Added",
                        value=", ".join([role.mention for role in added_roles]),
                        inline=False
                    )

                if removed_roles:
                    embed.add_field(
                        name="Roles Removed",
                        value=", ".join([role.mention for role in removed_roles]),
                        inline=False
                    )

        if embed:
            embed.set_footer(text=f"ID: {after.id}")
            await self.send_log(after.guild, embed, "roles")

    async def log_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        embed = None

        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="Joined Voice Channel",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Channel", value=after.channel.mention, inline=True)

        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="Left Voice Channel",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Channel", value=before.channel.mention, inline=True)

        elif before.channel != after.channel:
            embed = discord.Embed(
                title="Moved Voice Channel",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Member", value=member.mention, inline=False)
            embed.add_field(name="Before", value=before.channel.mention, inline=True)
            embed.add_field(name="After", value=after.channel.mention, inline=True)

        if embed:
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            await self.send_log(member.guild, embed, "voice")

    async def log_channel_create(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(
            title="Channel Created",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Name", value=channel.name, inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        embed.add_field(name="ID", value=str(channel.id), inline=True)

        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Category", value=channel.category.name, inline=True)

        embed.set_footer(text=f"Channel ID: {channel.id}")

        await self.send_log(channel.guild, embed, "channels")

    async def log_channel_delete(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(
            title="Channel Deleted",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Name", value=channel.name, inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)
        embed.add_field(name="ID", value=str(channel.id), inline=True)

        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Category", value=channel.category.name, inline=True)

        embed.set_footer(text=f"Channel ID: {channel.id}")

        await self.send_log(channel.guild, embed, "channels")

    async def log_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        changes = []

        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")

        if hasattr(before, 'topic') and hasattr(after, 'topic') and before.topic != after.topic:
            changes.append(f"**Topic:** {before.topic or '*None*'} → {after.topic or '*None*'}")

        if hasattr(before, 'nsfw') and hasattr(after, 'nsfw') and before.nsfw != after.nsfw:
            changes.append(f"**NSFW:** {before.nsfw} → {after.nsfw}")

        if hasattr(before, 'slowmode_delay') and hasattr(after, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
            changes.append(f"**Slowmode:** {before.slowmode_delay}s → {after.slowmode_delay}s")

        if not changes:
            return

        embed = discord.Embed(
            title="Channel Updated",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Channel", value=after.mention, inline=True)
        embed.add_field(name="Type", value=str(after.type), inline=True)
        embed.add_field(name="Changes", value="\n".join(changes), inline=False)
        embed.set_footer(text=f"ID: {after.id}")

        await self.send_log(after.guild, embed, "channels")

    async def log_guild_update(self, before: discord.Guild, after: discord.Guild):
        changes = []

        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")

        if before.description != after.description:
            changes.append(f"**Description:** {before.description or '*None*'} → {after.description or '*None*'}")

        if before.verification_level != after.verification_level:
            changes.append(f"**Verification level:** {before.verification_level} → {after.verification_level}")

        if before.explicit_content_filter != after.explicit_content_filter:
            changes.append(f"**Content filter:** {before.explicit_content_filter} → {after.explicit_content_filter}")

        if not changes:
            return

        embed = discord.Embed(
            title="Server Updated",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Changes", value="\n".join(changes), inline=False)
        embed.set_footer(text=f"Server ID: {after.id}")

        if after.icon:
            embed.set_thumbnail(url=after.icon.url)

        await self.send_log(after, embed, "server")

    async def log_ban(self, guild: discord.Guild, user: discord.User):
        embed = discord.Embed(
            title="Member Banned",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user.mention}\n{user}", inline=True)
        embed.add_field(name="ID", value=str(user.id), inline=True)
        embed.set_footer(text=f"User ID: {user.id}")

        await self.send_log(guild, embed, "moderation")

    async def log_unban(self, guild: discord.Guild, user: discord.User):
        embed = discord.Embed(
            title="Member Unbanned",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User", value=f"{user.mention}\n{user}", inline=True)
        embed.add_field(name="ID", value=str(user.id), inline=True)
        embed.set_footer(text=f"User ID: {user.id}")

        await self.send_log(guild, embed, "moderation")
