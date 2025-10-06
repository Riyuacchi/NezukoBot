import discord
from discord.ext import commands
from sqlalchemy import select, update
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import random
from bot.database import AsyncSessionLocal
from bot.models import LevelConfig, UserLevel, LevelRole


class LevelSystem:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {}

    async def get_config(self, guild_id: int) -> Optional[LevelConfig]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(LevelConfig).where(LevelConfig.guild_id == guild_id)
            )
            return result.scalar_one_or_none()

    async def create_default_config(self, guild_id: int) -> LevelConfig:
        async with AsyncSessionLocal() as session:
            config = LevelConfig(
                guild_id=guild_id,
                enabled=True,
                xp_min=15,
                xp_max=25,
                xp_cooldown=60,
                level_up_message="Congratulations {user}! You reached level {level}!",
                level_up_channel_id=None,
                announcement_enabled=True,
                stack_roles=False,
                xp_multiplier=1.0,
                voice_xp_enabled=True,
                voice_xp_min=5,
                voice_xp_max=10,
                voice_xp_interval=300,
                blacklisted_channels=[],
                blacklisted_roles=[],
                bonus_roles={}
            )
            session.add(config)
            await session.commit()
            await session.refresh(config)
            return config

    async def get_user_level(self, guild_id: int, user_id: int) -> Optional[UserLevel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserLevel).where(
                    UserLevel.guild_id == guild_id,
                    UserLevel.user_id == user_id
                )
            )
            return result.scalar_one_or_none()

    async def create_user_level(self, guild_id: int, user_id: int) -> UserLevel:
        async with AsyncSessionLocal() as session:
            user_level = UserLevel(
                guild_id=guild_id,
                user_id=user_id,
                xp=0,
                level=0,
                total_xp=0,
                messages_sent=0,
                voice_time=0,
                last_xp_time=datetime.utcnow()
            )
            session.add(user_level)
            await session.commit()
            await session.refresh(user_level)
            return user_level

    def calculate_xp_for_level(self, level: int) -> int:
        return int(5 * (level ** 2) + 50 * level + 100)

    def calculate_level_from_xp(self, xp: int) -> int:
        level = 0
        total_xp_needed = 0
        while total_xp_needed <= xp:
            level += 1
            total_xp_needed += self.calculate_xp_for_level(level)
        return level - 1

    async def check_cooldown(self, guild_id: int, user_id: int, cooldown_seconds: int) -> bool:
        key = f"{guild_id}_{user_id}"
        if key in self.cooldowns:
            last_time = self.cooldowns[key]
            if datetime.utcnow() - last_time < timedelta(seconds=cooldown_seconds):
                return False
        self.cooldowns[key] = datetime.utcnow()
        return True

    async def add_xp(
        self,
        guild: discord.Guild,
        user: discord.Member,
        channel: discord.TextChannel,
        xp_amount: Optional[int] = None
    ) -> Tuple[bool, int, int]:
        if user.bot:
            return False, 0, 0

        config = await self.get_config(guild.id)
        if not config or not config.enabled:
            return False, 0, 0

        if channel.id in config.blacklisted_channels:
            return False, 0, 0

        user_role_ids = [role.id for role in user.roles]
        if any(role_id in config.blacklisted_roles for role_id in user_role_ids):
            return False, 0, 0

        if not await self.check_cooldown(guild.id, user.id, config.xp_cooldown):
            return False, 0, 0

        user_level = await self.get_user_level(guild.id, user.id)
        if not user_level:
            user_level = await self.create_user_level(guild.id, user.id)

        if xp_amount is None:
            xp_amount = random.randint(config.xp_min, config.xp_max)

        multiplier = config.xp_multiplier
        for role_id, bonus in config.bonus_roles.items():
            if role_id in user_role_ids:
                multiplier += bonus

        xp_amount = int(xp_amount * multiplier)

        old_level = user_level.level
        new_xp = user_level.xp + xp_amount
        new_total_xp = user_level.total_xp + xp_amount

        xp_needed = self.calculate_xp_for_level(user_level.level + 1)

        leveled_up = False
        new_level = old_level

        while new_xp >= xp_needed:
            new_xp -= xp_needed
            new_level += 1
            xp_needed = self.calculate_xp_for_level(new_level + 1)
            leveled_up = True

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(UserLevel)
                .where(
                    UserLevel.guild_id == guild.id,
                    UserLevel.user_id == user.id
                )
                .values(
                    xp=new_xp,
                    level=new_level,
                    total_xp=new_total_xp,
                    messages_sent=UserLevel.messages_sent + 1,
                    last_xp_time=datetime.utcnow()
                )
            )
            await session.commit()

        if leveled_up:
            await self.handle_level_up(guild, user, channel, new_level, config)

        return leveled_up, new_level, xp_amount

    async def add_voice_xp(self, guild: discord.Guild, user: discord.Member, minutes: int):
        if user.bot:
            return

        config = await self.get_config(guild.id)
        if not config or not config.enabled or not config.voice_xp_enabled:
            return

        user_role_ids = [role.id for role in user.roles]
        if any(role_id in config.blacklisted_roles for role_id in user_role_ids):
            return

        xp_amount = random.randint(config.voice_xp_min, config.voice_xp_max)

        multiplier = config.xp_multiplier
        for role_id, bonus in config.bonus_roles.items():
            if role_id in user_role_ids:
                multiplier += bonus

        xp_amount = int(xp_amount * multiplier)

        user_level = await self.get_user_level(guild.id, user.id)
        if not user_level:
            user_level = await self.create_user_level(guild.id, user.id)

        old_level = user_level.level
        new_xp = user_level.xp + xp_amount
        new_total_xp = user_level.total_xp + xp_amount

        xp_needed = self.calculate_xp_for_level(user_level.level + 1)

        leveled_up = False
        new_level = old_level

        while new_xp >= xp_needed:
            new_xp -= xp_needed
            new_level += 1
            xp_needed = self.calculate_xp_for_level(new_level + 1)
            leveled_up = True

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(UserLevel)
                .where(
                    UserLevel.guild_id == guild.id,
                    UserLevel.user_id == user.id
                )
                .values(
                    xp=new_xp,
                    level=new_level,
                    total_xp=new_total_xp,
                    voice_time=UserLevel.voice_time + minutes,
                    last_xp_time=datetime.utcnow()
                )
            )
            await session.commit()

        if leveled_up:
            await self.handle_level_up(guild, user, None, new_level, config)

    async def handle_level_up(
        self,
        guild: discord.Guild,
        user: discord.Member,
        channel: Optional[discord.TextChannel],
        new_level: int,
        config: LevelConfig
    ):
        await self.assign_level_roles(guild, user, new_level, config)

        if config.announcement_enabled:
            message = config.level_up_message.format(user=user.mention, level=new_level)

            target_channel = channel
            if config.level_up_channel_id:
                target_channel = guild.get_channel(config.level_up_channel_id)

            if target_channel:
                embed = discord.Embed(
                    title="Level Up!",
                    description=message,
                    color=discord.Color.gold()
                )
                embed.set_thumbnail(url=user.display_avatar.url)
                embed.add_field(name="Niveau", value=str(new_level), inline=True)

                try:
                    await target_channel.send(embed=embed)
                except:
                    pass

    async def assign_level_roles(
        self,
        guild: discord.Guild,
        user: discord.Member,
        level: int,
        config: LevelConfig
    ):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(LevelRole).where(
                    LevelRole.guild_id == guild.id,
                    LevelRole.level <= level
                ).order_by(LevelRole.level.desc())
            )
            level_roles = result.scalars().all()

            if not level_roles:
                return

            roles_to_add = []
            roles_to_remove = []

            if config.stack_roles:
                for level_role in level_roles:
                    role = guild.get_role(level_role.role_id)
                    if role and role not in user.roles:
                        roles_to_add.append(role)
            else:
                highest_role_entry = level_roles[0]
                highest_role = guild.get_role(highest_role_entry.role_id)

                if highest_role and highest_role not in user.roles:
                    roles_to_add.append(highest_role)

                for level_role in level_roles[1:]:
                    role = guild.get_role(level_role.role_id)
                    if role and role in user.roles:
                        roles_to_remove.append(role)

            try:
                if roles_to_add:
                    await user.add_roles(*roles_to_add, reason="Level up reward")
                if roles_to_remove:
                    await user.remove_roles(*roles_to_remove, reason="Higher level role obtained")
            except discord.Forbidden:
                pass

    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[UserLevel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserLevel)
                .where(UserLevel.guild_id == guild_id)
                .order_by(UserLevel.total_xp.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def get_user_rank(self, guild_id: int, user_id: int) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserLevel)
                .where(UserLevel.guild_id == guild_id)
                .order_by(UserLevel.total_xp.desc())
            )
            all_users = result.scalars().all()

            for rank, user in enumerate(all_users, start=1):
                if user.user_id == user_id:
                    return rank

            return 0

    async def set_xp(self, guild_id: int, user_id: int, xp: int):
        user_level = await self.get_user_level(guild_id, user_id)
        if not user_level:
            user_level = await self.create_user_level(guild_id, user_id)

        new_level = self.calculate_level_from_xp(xp)
        remaining_xp = xp

        for lvl in range(new_level):
            remaining_xp -= self.calculate_xp_for_level(lvl + 1)

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(UserLevel)
                .where(
                    UserLevel.guild_id == guild_id,
                    UserLevel.user_id == user_id
                )
                .values(
                    xp=remaining_xp,
                    level=new_level,
                    total_xp=xp
                )
            )
            await session.commit()

    async def set_level(self, guild_id: int, user_id: int, level: int):
        total_xp = sum(self.calculate_xp_for_level(lvl + 1) for lvl in range(level))
        await self.set_xp(guild_id, user_id, total_xp)

    async def reset_user(self, guild_id: int, user_id: int):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(UserLevel)
                .where(
                    UserLevel.guild_id == guild_id,
                    UserLevel.user_id == user_id
                )
                .values(
                    xp=0,
                    level=0,
                    total_xp=0,
                    messages_sent=0,
                    voice_time=0
                )
            )
            await session.commit()

    async def reset_guild(self, guild_id: int):
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(UserLevel)
                .where(UserLevel.guild_id == guild_id)
                .values(
                    xp=0,
                    level=0,
                    total_xp=0,
                    messages_sent=0,
                    voice_time=0
                )
            )
            await session.commit()