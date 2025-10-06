import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional
import config
from database.connection import AsyncSessionLocal
from database.models import Member
from bot.utils.embeds import success_embed, error_embed, info_embed
from sqlalchemy import select, func


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show command list")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def help(self, ctx: commands.Context, category: str = None):
        if category:
            cog = self.bot.get_cog(category.capitalize())
            if not cog:
                await ctx.send(embed=error_embed("Category not found"))
                return

            embed = discord.Embed(
                title=f"📚 Commands - {category.capitalize()}",
                color=config.EMBED_COLOR,
                timestamp=datetime.utcnow()
            )

            for command in cog.get_commands():
                if not command.hidden:
                    embed.add_field(
                        name=f"`/{command.name}`",
                        value=command.description or "No description",
                        inline=False
                    )
        else:
            embed = discord.Embed(
                title="📚 Help Menu",
                description="Here are all available command categories",
                color=config.EMBED_COLOR,
                timestamp=datetime.utcnow()
            )

            categories = {
                "Admin": "⚙️ Administration commands",
                "Moderation": "🛡️ Moderation commands",
                "Economy": "💰 Economy system",
                "Music": "🎵 Music commands",
                "Fun": "🎉 Fun commands",
                "Utility": "🔧 Utility commands"
            }

            for cog_name, description in categories.items():
                cog = self.bot.get_cog(cog_name)
                if cog:
                    commands_list = [cmd.name for cmd in cog.get_commands() if not cmd.hidden]
                    if commands_list:
                        embed.add_field(
                            name=f"{description}",
                            value=f"`/help {cog_name.lower()}` to view the commands",
                            inline=False
                        )

            embed.set_footer(text=f"Use /help <category> for more information")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ping", description="Show bot latency")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx: commands.Context):
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green() if latency < 100 else discord.Color.orange() if latency < 200 else discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="Status", value="Excellent" if latency < 100 else "Good" if latency < 200 else "Slow", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="invite", description="Get the bot invite link")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def invite(self, ctx: commands.Context):
        embed = discord.Embed(
            title="📨 Invite the bot",
            description=f"Use the link below to invite **{self.bot.user.name}** to your server!",
            color=config.EMBED_COLOR,
            timestamp=datetime.utcnow()
        )

        permissions = discord.Permissions(
            manage_channels=True,
            manage_roles=True,
            kick_members=True,
            ban_members=True,
            manage_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            add_reactions=True,
            connect=True,
            speak=True,
            moderate_members=True
        )

        invite_link = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=["bot", "applications.commands"]
        )

        embed.add_field(
            name="Invite link",
            value=f"[Click here]({invite_link})",
            inline=False
        )

        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="vote", description="Vote for the bot")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def vote(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🗳️ Vote for us!",
            description="Support the bot by voting on these platforms",
            color=config.EMBED_COLOR,
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="Top.gg",
            value="[Vote here](https://top.gg/)",
            inline=False
        )
        embed.add_field(
            name="Discord Bot List",
            value="[Vote here](https://discordbotlist.com/)",
            inline=False
        )

        embed.set_footer(text="Thanks for your support!")

        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", description="Show user information")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=f"👤 Information about {member}",
            color=member.color if member.color != discord.Color.default() else config.EMBED_COLOR,
            timestamp=datetime.utcnow()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Display name", value=member.display_name, inline=True)
        embed.add_field(name="Bot", value="✅" if member.bot else "❌", inline=True)

        embed.add_field(
            name="Account created",
            value=f"<t:{int(member.created_at.timestamp())}:F>\n<t:{int(member.created_at.timestamp())}:R>",
            inline=False
        )

        embed.add_field(
            name="Joined on",
            value=f"<t:{int(member.joined_at.timestamp())}:F>\n<t:{int(member.joined_at.timestamp())}:R>",
            inline=False
        )

        roles = [role.mention for role in member.roles[1:]]
        embed.add_field(
            name=f"Roles ({len(roles)})",
            value=" ".join(roles) if roles else "No roles",
            inline=False
        )

        if member.premium_since:
            embed.add_field(
                name="Boosting since",
                value=f"<t:{int(member.premium_since.timestamp())}:R>",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", description="Show server information")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def serverinfo(self, ctx: commands.Context):
        guild = ctx.guild

        embed = discord.Embed(
            title=f"📊 Information about {guild.name}",
            color=config.EMBED_COLOR,
            timestamp=datetime.utcnow()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)

        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)

        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        embed.add_field(name="Boost level", value=guild.premium_tier, inline=True)

        embed.add_field(
            name="Verification level",
            value=str(guild.verification_level).replace("_", " ").capitalize(),
            inline=True
        )

        if guild.description:
            embed.add_field(name="Description", value=guild.description, inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", description="Show a user's avatar")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=f"🖼️ Avatar for {member}",
            color=member.color if member.color != discord.Color.default() else config.EMBED_COLOR,
            timestamp=datetime.utcnow()
        )

        embed.set_image(url=member.display_avatar.url)

        embed.add_field(
            name="Links",
            value=f"[PNG]({member.display_avatar.replace(format='png', size=1024).url}) | "
                  f"[JPG]({member.display_avatar.replace(format='jpg', size=1024).url}) | "
                  f"[WEBP]({member.display_avatar.replace(format='webp', size=1024).url})",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rank", description="Show your rank or another member's")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Member).where(
                    Member.guild_id == ctx.guild.id,
                    Member.user_id == member.id
                )
            )
            db_member = result.scalar_one_or_none()

            if not db_member:
                await ctx.send(embed=error_embed("No data found for this member"))
                return

            rank_result = await session.execute(
                select(func.count(Member.id)).where(
                    Member.guild_id == ctx.guild.id,
                    Member.xp > db_member.xp
                )
            )
            rank = rank_result.scalar() + 1

            xp_for_next = (db_member.level + 1) ** 2 * 100
            xp_progress = db_member.xp - (db_member.level ** 2 * 100)
            xp_needed = xp_for_next - (db_member.level ** 2 * 100)

            embed = discord.Embed(
                title=f"📊 Rank of {member.display_name}",
                color=member.color if member.color != discord.Color.default() else config.EMBED_COLOR,
                timestamp=datetime.utcnow()
            )

            embed.set_thumbnail(url=member.display_avatar.url)

            embed.add_field(name="Rank", value=f"#{rank}", inline=True)
            embed.add_field(name="Level", value=db_member.level, inline=True)
            embed.add_field(name="XP", value=f"{db_member.xp:,}", inline=True)

            progress_bar = self.create_progress_bar(xp_progress, xp_needed)
            embed.add_field(
                name="Progress",
                value=f"{progress_bar}\n{xp_progress}/{xp_needed} XP",
                inline=False
            )

            embed.add_field(name="Messages", value=f"{db_member.messages_count:,}", inline=True)
            embed.add_field(name="Voice time", value=f"{db_member.voice_time // 60}h {db_member.voice_time % 60}m", inline=True)

            await ctx.send(embed=embed)

    @commands.hybrid_command(name="leaderboard", description="Show the server leaderboard")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def leaderboard(self, ctx: commands.Context, page: int = 1):
        if page < 1:
            page = 1

        per_page = 10
        offset = (page - 1) * per_page

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Member).where(
                    Member.guild_id == ctx.guild.id
                ).order_by(Member.xp.desc()).limit(per_page).offset(offset)
            )
            members = result.scalars().all()

            if not members:
                await ctx.send(embed=error_embed("No members in the leaderboard"))
                return

            embed = discord.Embed(
                title=f"🏆 Leaderboard for {ctx.guild.name}",
                description=f"Page {page}",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )

            for i, db_member in enumerate(members, start=offset + 1):
                member = ctx.guild.get_member(db_member.user_id)
                if member:
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
                    embed.add_field(
                        name=f"{medal} {member.display_name}",
                        value=f"Level {db_member.level} - {db_member.xp:,} XP\n{db_member.messages_count} messages",
                        inline=False
                    )

            total_count = await session.execute(
                select(func.count(Member.id)).where(Member.guild_id == ctx.guild.id)
            )
            total = total_count.scalar()
            total_pages = (total + per_page - 1) // per_page

            embed.set_footer(text=f"Page {page}/{total_pages} - Total: {total} members")

            await ctx.send(embed=embed)

    def create_progress_bar(self, current: int, total: int, length: int = 10) -> str:
        if total == 0:
            percentage = 0
        else:
            percentage = min(current / total, 1.0)

        filled = int(length * percentage)
        bar = "█" * filled + "░" * (length - filled)
        return f"`{bar}`"


async def setup(bot):
    await bot.add_cog(Utility(bot))
