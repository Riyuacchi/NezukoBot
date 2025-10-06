import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
from database.connection import AsyncSessionLocal
from database.models import Guild, Member, Warning
from bot.utils.embeds import success_embed, error_embed, info_embed
from bot.utils.checks import is_moderator
from sqlalchemy import select, delete


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ban", description="Ban a member from the server")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send(embed=error_embed("You cannot ban this member"))
            return

        if member.id == ctx.guild.owner_id:
            await ctx.send(embed=error_embed("You cannot ban the server owner"))
            return

        try:
            await member.ban(reason=f"{reason} - By {ctx.author}")
            await ctx.send(embed=success_embed(f"{member.mention} was banned\n**Reason:** {reason}"))
        except discord.Forbidden:
            await ctx.send(embed=error_embed("I don't have the required permissions to ban this member"))
        except discord.HTTPException:
            await ctx.send(embed=error_embed("An error occurred while banning the member"))

    @commands.hybrid_command(name="unban", description="Unban a user from the server")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def unban(self, ctx: commands.Context, user_id: str):
        try:
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(embed=success_embed(f"{user.mention} was unbanned"))
        except ValueError:
            await ctx.send(embed=error_embed("Invalid user ID"))
        except discord.NotFound:
            await ctx.send(embed=error_embed("User not found or not banned"))
        except discord.Forbidden:
            await ctx.send(embed=error_embed("I do not have permission to unban"))
        except discord.HTTPException:
            await ctx.send(embed=error_embed("An error occurred"))

    @commands.hybrid_command(name="kick", description="Kick a member from the server")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send(embed=error_embed("You cannot kick this member"))
            return

        if member.id == ctx.guild.owner_id:
            await ctx.send(embed=error_embed("You cannot kick the server owner"))
            return

        try:
            await member.kick(reason=f"{reason} - By {ctx.author}")
            await ctx.send(embed=success_embed(f"{member.mention} was kicked\n**Reason:** {reason}"))
        except discord.Forbidden:
            await ctx.send(embed=error_embed("I don't have the required permissions to kick this member"))
        except discord.HTTPException:
            await ctx.send(embed=error_embed("An error occurred"))

    @commands.hybrid_command(name="warn", description="Warn a member")
    @is_moderator()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        async with AsyncSessionLocal() as session:
            warning = Warning(
                guild_id=ctx.guild.id,
                user_id=member.id,
                moderator_id=ctx.author.id,
                reason=reason,
                active=True
            )
            session.add(warning)

            result = await session.execute(
                select(Member).where(
                    Member.guild_id == ctx.guild.id,
                    Member.user_id == member.id
                )
            )
            db_member = result.scalar_one_or_none()

            if db_member:
                db_member.warnings_count += 1
            else:
                db_member = Member(
                    guild_id=ctx.guild.id,
                    user_id=member.id,
                    username=str(member),
                    warnings_count=1
                )
                session.add(db_member)

            await session.commit()

            embed = success_embed(f"{member.mention} has been warned")
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Warning count", value=db_member.warnings_count, inline=False)
            await ctx.send(embed=embed)

            try:
                dm_embed = discord.Embed(
                    title="⚠️ Warning",
                    description=f"You received a warning in **{ctx.guild.name}**",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass

    @commands.hybrid_command(name="clearwarnings", description="Clear a member's warnings")
    @is_moderator()
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member):
        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(Warning).where(
                    Warning.guild_id == ctx.guild.id,
                    Warning.user_id == member.id
                )
            )

            result = await session.execute(
                select(Member).where(
                    Member.guild_id == ctx.guild.id,
                    Member.user_id == member.id
                )
            )
            db_member = result.scalar_one_or_none()

            if db_member:
                db_member.warnings_count = 0

            await session.commit()
            await ctx.send(embed=success_embed(f"All warnings for {member.mention} have been cleared"))

    @commands.hybrid_command(name="warnings", description="Show warnings for a member")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def warnings(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Warning).where(
                    Warning.guild_id == ctx.guild.id,
                    Warning.user_id == member.id,
                    Warning.active == True
                ).order_by(Warning.created_at.desc())
            )
            warnings = result.scalars().all()

            if not warnings:
                await ctx.send(embed=info_embed(f"{member.mention} has no warnings"))
                return

            embed = discord.Embed(
                title=f"⚠️ Warnings for {member}",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )

            for i, warn in enumerate(warnings[:10], 1):
                moderator = ctx.guild.get_member(warn.moderator_id)
                mod_name = moderator.mention if moderator else f"ID: {warn.moderator_id}"
                embed.add_field(
                    name=f"Warning #{i}",
                    value=f"**Moderator:** {mod_name}\n**Reason:** {warn.reason}\n**Date:** <t:{int(warn.created_at.timestamp())}:R>",
                    inline=False
                )

            embed.set_footer(text=f"Total: {len(warnings)} warning(s)")
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="mute", description="Mute a member (timeout)")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: int, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send(embed=error_embed("You cannot mute this member"))
            return

        try:
            await member.timeout(timedelta(minutes=duration), reason=reason)
            await ctx.send(embed=success_embed(f"{member.mention} was muted for {duration} minutes\n**Reason:** {reason}"))
        except discord.Forbidden:
            await ctx.send(embed=error_embed("I don't have the required permissions"))
        except discord.HTTPException:
            await ctx.send(embed=error_embed("An error occurred"))

    @commands.hybrid_command(name="unmute", description="Remove a member's mute")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        try:
            await member.timeout(None)
            await ctx.send(embed=success_embed(f"{member.mention} is no longer muted"))
        except discord.Forbidden:
            await ctx.send(embed=error_embed("I don't have the required permissions"))
        except discord.HTTPException:
            await ctx.send(embed=error_embed("An error occurred"))

    @commands.hybrid_command(name="timeout", description="Timeout a member")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def timeout(self, ctx: commands.Context, member: discord.Member, hours: int, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send(embed=error_embed("You cannot timeout this member"))
            return

        try:
            await member.timeout(timedelta(hours=hours), reason=reason)
            await ctx.send(embed=success_embed(f"{member.mention} was timed out for {hours} hour(s)\n**Reason:** {reason}"))
        except discord.Forbidden:
            await ctx.send(embed=error_embed("I don't have the required permissions"))
        except discord.HTTPException:
            await ctx.send(embed=error_embed("An error occurred"))

    @commands.hybrid_command(name="lock", description="Lock a channel")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=success_embed(f"{channel.mention} has been locked 🔒"))

    @commands.hybrid_command(name="unlock", description="Unlock a channel")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=success_embed(f"{channel.mention} has been unlocked 🔓"))

    @commands.hybrid_command(name="slowmode", description="Set slowmode for a channel")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def slowmode(self, ctx: commands.Context, seconds: int, channel: discord.TextChannel = None):
        channel = channel or ctx.channel

        if seconds < 0 or seconds > 21600:
            await ctx.send(embed=error_embed("Delay must be between 0 and 21600 seconds"))
            return

        await channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send(embed=success_embed(f"Slowmode disabled for {channel.mention}"))
        else:
            await ctx.send(embed=success_embed(f"Slowmode set to {seconds}s for {channel.mention}"))

    @commands.hybrid_command(name="purge", description="Delete messages")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def purge(self, ctx: commands.Context, amount: int):
        if amount < 1 or amount > 100:
            await ctx.send(embed=error_embed("You must provide a number between 1 and 100"), delete_after=5)
            return

        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(embed=success_embed(f"{len(deleted) - 1} message(s) deleted"))
        await msg.delete(delay=5)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
