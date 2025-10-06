import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import random
from typing import Optional
from database.connection import AsyncSessionLocal
from database.models import Member, Economy
from bot.utils.embeds import success_embed, error_embed, info_embed
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shop_items = {
            "vip": {"name": "VIP Pass", "price": 10000, "description": "VIP role for 30 days", "emoji": "⭐"},
            "color": {"name": "Custom Color", "price": 5000, "description": "Role with a custom color", "emoji": "🎨"},
            "boost": {"name": "XP Boost x2", "price": 3000, "description": "Double XP for 24 hours", "emoji": "⚡"},
            "coins": {"name": "Coin Pack", "price": 1000, "description": "Bonus 1,000 coins", "emoji": "💰"},
        }

    async def get_or_create_member(self, session, guild_id: int, user_id: int, username: str):
        result = await session.execute(
            select(Member).options(selectinload(Member.economy)).where(
                Member.guild_id == guild_id,
                Member.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            member = Member(
                guild_id=guild_id,
                user_id=user_id,
                username=username,
                coins=0,
                bank=0
            )
            session.add(member)
            await session.flush()

            economy = Economy(member_id=member.id, inventory={})
            session.add(economy)
            await session.flush()
            member.economy = economy

        if not member.economy:
            economy = Economy(member_id=member.id, inventory={})
            session.add(economy)
            await session.flush()
            member.economy = economy

        return member

    @commands.hybrid_command(name="balance", description="Show your balance or another member's")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author

        async with AsyncSessionLocal() as session:
            db_member = await self.get_or_create_member(session, ctx.guild.id, member.id, str(member))
            await session.commit()

            embed = discord.Embed(
                title=f"💰 Balance for {member.display_name}",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="💵 Wallet", value=f"{db_member.coins:,}", inline=True)
            embed.add_field(name="🏦 Bank", value=f"{db_member.bank:,}", inline=True)
            embed.add_field(name="💎 Total", value=f"{db_member.coins + db_member.bank:,}", inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="work", description="Work to earn coins")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        async with AsyncSessionLocal() as session:
            member = await self.get_or_create_member(session, ctx.guild.id, ctx.author.id, str(ctx.author))

            if member.last_work and datetime.utcnow() - member.last_work < timedelta(hours=1):
                remaining = timedelta(hours=1) - (datetime.utcnow() - member.last_work)
                minutes = int(remaining.total_seconds() // 60)
                await ctx.send(embed=error_embed(f"You already worked recently. Try again in {minutes} minute(s)"))
                return

            jobs = [
                "developer", "doctor", "lawyer", "teacher", "engineer",
                "artist", "musician", "chef", "architect", "scientist"
            ]
            job = random.choice(jobs)
            earned = random.randint(100, 500)

            member.coins += earned
            member.last_work = datetime.utcnow()

            if member.economy:
                member.economy.total_earned += earned
                member.economy.work_streak += 1

            await session.commit()

            embed = success_embed(f"You worked as **{job}** and earned **{earned}** coins")
            embed.set_footer(text=f"Work streak: {member.economy.work_streak if member.economy else 0}")
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily", description="Claim your daily reward")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        async with AsyncSessionLocal() as session:
            member = await self.get_or_create_member(session, ctx.guild.id, ctx.author.id, str(ctx.author))

            if member.last_daily and datetime.utcnow() - member.last_daily < timedelta(days=1):
                remaining = timedelta(days=1) - (datetime.utcnow() - member.last_daily)
                hours = int(remaining.total_seconds() // 3600)
                await ctx.send(embed=error_embed(f"You already claimed your daily reward. Come back in {hours} hour(s)"))
                return

            base_reward = 500
            streak_bonus = 0

            if member.economy:
                if member.last_daily and datetime.utcnow() - member.last_daily <= timedelta(days=2):
                    member.economy.daily_streak += 1
                else:
                    member.economy.daily_streak = 1

                streak_bonus = min(member.economy.daily_streak * 50, 500)

            total_reward = base_reward + streak_bonus
            member.coins += total_reward
            member.last_daily = datetime.utcnow()

            if member.economy:
                member.economy.total_earned += total_reward

            await session.commit()

            embed = success_embed(f"You received your daily reward of **{total_reward}** coins")
            if streak_bonus > 0:
                embed.add_field(
                    name="🔥 Streak",
                    value=f"{member.economy.daily_streak} day(s) - Bonus: {streak_bonus} coins",
                    inline=False
                )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="shop", description="Show the shop")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def shop(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🛒 Shop",
            description="Use `/buy <item>` to purchase an item",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        for item_id, item_data in self.shop_items.items():
            embed.add_field(
                name=f"{item_data['emoji']} {item_data['name']}",
                value=f"{item_data['description']}\n**Price:** {item_data['price']:,} 💰\n**ID:** `{item_id}`",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy", description="Purchase an item from the shop")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def buy(self, ctx: commands.Context, item: str):
        if item not in self.shop_items:
            await ctx.send(embed=error_embed("Item not found in the shop"))
            return

        item_data = self.shop_items[item]

        async with AsyncSessionLocal() as session:
            member = await self.get_or_create_member(session, ctx.guild.id, ctx.author.id, str(ctx.author))

            if member.coins < item_data["price"]:
                await ctx.send(embed=error_embed(f"You do not have enough coins. Cost: {item_data['price']:,} 💰"))
                return

            member.coins -= item_data["price"]

            if member.economy:
                member.economy.total_spent += item_data["price"]
                if not member.economy.inventory:
                    member.economy.inventory = {}
                inventory = member.economy.inventory
                inventory[item] = inventory.get(item, 0) + 1
                member.economy.inventory = inventory

            await session.commit()

            embed = success_embed(f"You purchased **{item_data['name']}** {item_data['emoji']}")
            embed.add_field(name="Price", value=f"{item_data['price']:,} 💰", inline=True)
            embed.add_field(name="Remaining balance", value=f"{member.coins:,} 💰", inline=True)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="inventory", description="Show your inventory")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def inventory(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author

        async with AsyncSessionLocal() as session:
            db_member = await self.get_or_create_member(session, ctx.guild.id, member.id, str(member))
            await session.commit()

            embed = discord.Embed(
                title=f"🎒 Inventory for {member.display_name}",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )

            if not db_member.economy or not db_member.economy.inventory or len(db_member.economy.inventory) == 0:
                embed.description = "Inventory empty"
            else:
                for item_id, quantity in db_member.economy.inventory.items():
                    if item_id in self.shop_items:
                        item_data = self.shop_items[item_id]
                        embed.add_field(
                            name=f"{item_data['emoji']} {item_data['name']}",
                            value=f"Quantity: {quantity}",
                            inline=True
                        )

            embed.set_thumbnail(url=member.display_avatar.url)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="transfer", description="Transfer coins to another member")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def transfer(self, ctx: commands.Context, member: discord.Member, amount: int):
        if member.bot:
            await ctx.send(embed=error_embed("You cannot transfer coins to a bot"))
            return

        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot transfer coins to yourself"))
            return

        if amount <= 0:
            await ctx.send(embed=error_embed("Amount must be greater than 0"))
            return

        async with AsyncSessionLocal() as session:
            sender = await self.get_or_create_member(session, ctx.guild.id, ctx.author.id, str(ctx.author))
            receiver = await self.get_or_create_member(session, ctx.guild.id, member.id, str(member))

            if sender.coins < amount:
                await ctx.send(embed=error_embed(f"You do not have enough coins. Balance: {sender.coins:,} 💰"))
                return

            sender.coins -= amount
            receiver.coins += amount

            await session.commit()

            embed = success_embed(f"You transferred **{amount:,}** coins to {member.mention}")
            embed.add_field(name="Your new balance", value=f"{sender.coins:,} 💰", inline=True)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="gamble", description="Gamble coins (50% chance to double)")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def gamble(self, ctx: commands.Context, amount: int):
        if amount <= 0:
            await ctx.send(embed=error_embed("Amount must be greater than 0"))
            return

        async with AsyncSessionLocal() as session:
            member = await self.get_or_create_member(session, ctx.guild.id, ctx.author.id, str(ctx.author))

            if member.coins < amount:
                await ctx.send(embed=error_embed(f"You do not have enough coins. Balance: {member.coins:,} 💰"))
                return

            win = random.choice([True, False])

            if win:
                member.coins += amount
                await session.commit()
                embed = discord.Embed(
                    title="🎰 You won!",
                    description=f"You gambled **{amount:,}** coins and won **{amount:,}** coins",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="New balance", value=f"{member.coins:,} 💰", inline=True)
            else:
                member.coins -= amount
                await session.commit()
                embed = discord.Embed(
                    title="🎰 You lost!",
                    description=f"You gambled **{amount:,}** coins and lost everything",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="New balance", value=f"{member.coins:,} 💰", inline=True)

            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EconomyCog(bot))