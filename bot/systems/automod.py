import discord
from discord.ext import commands
from sqlalchemy import select, update
from datetime import datetime, timedelta
from typing import Optional, List
import re
from bot.database import AsyncSessionLocal
from bot.models import AutoModConfig, ModerationLog


class AutoModSystem:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spam_tracker = {}
        self.repeated_messages = {}

    async def get_config(self, guild_id: int) -> Optional[AutoModConfig]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AutoModConfig).where(AutoModConfig.guild_id == guild_id)
            )
            return result.scalar_one_or_none()

    async def create_default_config(self, guild_id: int) -> AutoModConfig:
        async with AsyncSessionLocal() as session:
            config = AutoModConfig(
                guild_id=guild_id,
                spam_enabled=True,
                spam_threshold=5,
                spam_interval=5,
                caps_enabled=True,
                caps_threshold=70,
                caps_min_length=10,
                repeated_enabled=True,
                repeated_threshold=3,
                link_filter_enabled=False,
                invite_filter_enabled=True,
                word_filter_enabled=True,
                filtered_words=[],
                whitelisted_channels=[],
                whitelisted_roles=[],
                max_mentions=5,
                max_emojis=10,
                punishment_type="warn",
                punishment_duration=0
            )
            session.add(config)
            await session.commit()
            await session.refresh(config)
            return config

    async def check_whitelist(self, message: discord.Message, config: AutoModConfig) -> bool:
        if message.author.guild_permissions.administrator:
            return True

        if message.channel.id in config.whitelisted_channels:
            return True

        member_role_ids = [role.id for role in message.author.roles]
        if any(role_id in config.whitelisted_roles for role_id in member_role_ids):
            return True

        return False

    async def check_spam(self, message: discord.Message, config: AutoModConfig) -> bool:
        if not config.spam_enabled:
            return False

        user_id = message.author.id
        current_time = datetime.utcnow()

        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = []

        self.spam_tracker[user_id] = [
            msg_time for msg_time in self.spam_tracker[user_id]
            if current_time - msg_time < timedelta(seconds=config.spam_interval)
        ]

        self.spam_tracker[user_id].append(current_time)

        if len(self.spam_tracker[user_id]) >= config.spam_threshold:
            self.spam_tracker[user_id] = []
            return True

        return False

    async def check_caps(self, message: discord.Message, config: AutoModConfig) -> bool:
        if not config.caps_enabled:
            return False

        content = message.content
        if len(content) < config.caps_min_length:
            return False

        caps_count = sum(1 for c in content if c.isupper())
        total_letters = sum(1 for c in content if c.isalpha())

        if total_letters == 0:
            return False

        caps_percentage = (caps_count / total_letters) * 100
        return caps_percentage >= config.caps_threshold

    async def check_repeated_text(self, message: discord.Message, config: AutoModConfig) -> bool:
        if not config.repeated_enabled:
            return False

        user_id = message.author.id
        content = message.content.lower()

        if user_id not in self.repeated_messages:
            self.repeated_messages[user_id] = []

        self.repeated_messages[user_id].append(content)

        if len(self.repeated_messages[user_id]) > 5:
            self.repeated_messages[user_id].pop(0)

        if self.repeated_messages[user_id].count(content) >= config.repeated_threshold:
            self.repeated_messages[user_id] = []
            return True

        return False

    async def check_links(self, message: discord.Message, config: AutoModConfig) -> bool:
        if not config.link_filter_enabled:
            return False

        link_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        return bool(re.search(link_pattern, message.content))

    async def check_invites(self, message: discord.Message, config: AutoModConfig) -> bool:
        if not config.invite_filter_enabled:
            return False

        invite_pattern = r'(?:discord\.gg|discord\.com/invite)/[a-zA-Z0-9]+'
        return bool(re.search(invite_pattern, message.content))

    async def check_filtered_words(self, message: discord.Message, config: AutoModConfig) -> bool:
        if not config.word_filter_enabled or not config.filtered_words:
            return False

        content_lower = message.content.lower()
        return any(word.lower() in content_lower for word in config.filtered_words)

    async def check_mentions(self, message: discord.Message, config: AutoModConfig) -> bool:
        if config.max_mentions == 0:
            return False

        return len(message.mentions) > config.max_mentions

    async def check_emojis(self, message: discord.Message, config: AutoModConfig) -> bool:
        if config.max_emojis == 0:
            return False

        emoji_pattern = r'<a?:[a-zA-Z0-9_]+:[0-9]+>|[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
        emojis = re.findall(emoji_pattern, message.content)
        return len(emojis) > config.max_emojis

    async def apply_punishment(self, message: discord.Message, config: AutoModConfig, reason: str):
        member = message.author

        if config.punishment_type == "warn":
            await self.log_warning(member, message.guild, reason)

        elif config.punishment_type == "mute":
            try:
                duration = timedelta(minutes=config.punishment_duration) if config.punishment_duration > 0 else None
                await member.timeout(duration, reason=reason)
            except discord.Forbidden:
                pass

        elif config.punishment_type == "kick":
            try:
                await member.kick(reason=reason)
            except discord.Forbidden:
                pass

        elif config.punishment_type == "ban":
            try:
                await member.ban(reason=reason)
            except discord.Forbidden:
                pass

    async def log_warning(self, member: discord.Member, guild: discord.Guild, reason: str):
        async with AsyncSessionLocal() as session:
            log_entry = ModerationLog(
                guild_id=guild.id,
                user_id=member.id,
                moderator_id=self.bot.user.id,
                action_type="warn",
                reason=reason,
                timestamp=datetime.utcnow()
            )
            session.add(log_entry)
            await session.commit()

    async def process_message(self, message: discord.Message) -> Optional[str]:
        if message.author.bot or not message.guild:
            return None

        config = await self.get_config(message.guild.id)
        if not config:
            config = await self.create_default_config(message.guild.id)

        if await self.check_whitelist(message, config):
            return None

        violations = []

        if await self.check_spam(message, config):
            violations.append("spam")

        if await self.check_caps(message, config):
            violations.append("excessive capital letters")

        if await self.check_repeated_text(message, config):
            violations.append("repeated text")

        if await self.check_links(message, config):
            violations.append("forbidden links")

        if await self.check_invites(message, config):
            violations.append("discord invites")

        if await self.check_filtered_words(message, config):
            violations.append("filtered words")

        if await self.check_mentions(message, config):
            violations.append("too many mentions")

        if await self.check_emojis(message, config):
            violations.append("too many emojis")

        if violations:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            reason = f"AutoMod: {', '.join(violations)}"
            await self.apply_punishment(message, config, reason)

            return reason

        return None
