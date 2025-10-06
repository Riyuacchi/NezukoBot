import discord
from discord.ext import commands, tasks
from discord import ui
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta
from typing import Optional, List
import random
from bot.database import AsyncSessionLocal
from bot.models import Giveaway, GiveawayEntry


class GiveawayView(ui.View):
    def __init__(self, giveaway_system, giveaway_id: int):
        super().__init__(timeout=None)
        self.giveaway_system = giveaway_system
        self.giveaway_id = giveaway_id

    @ui.button(label="Enter", emoji="🎉", style=discord.ButtonStyle.primary, custom_id="giveaway_enter")
    async def enter_giveaway(self, interaction: discord.Interaction, button: ui.Button):
        await self.giveaway_system.enter_giveaway(interaction, self.giveaway_id)


class GiveawaySystem:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_giveaways.start()

    async def get_giveaway(self, giveaway_id: int) -> Optional[Giveaway]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Giveaway).where(Giveaway.id == giveaway_id)
            )
            return result.scalar_one_or_none()

    async def get_active_giveaways(self) -> List[Giveaway]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Giveaway).where(Giveaway.ended == False)
            )
            return result.scalars().all()

    async def create_giveaway(
        self,
        guild: discord.Guild,
        channel: discord.TextChannel,
        prize: str,
        duration: timedelta,
        winners_count: int,
        host_id: int,
        required_role_id: Optional[int] = None,
        required_level: Optional[int] = None,
        description: Optional[str] = None
    ) -> Giveaway:
        end_time = datetime.utcnow() + duration

        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prize:** {prize}\n\n{description if description else 'Good luck everyone!'}",
            color=discord.Color.gold(),
            timestamp=end_time
        )
        embed.add_field(name="Winners", value=f"{winners_count} winner(s)", inline=True)
        embed.add_field(name="Hosted by", value=f"<@{host_id}>", inline=True)
        embed.set_footer(text="Ends")

        if required_role_id:
            embed.add_field(name="Required role", value=f"<@&{required_role_id}>", inline=False)
        if required_level:
            embed.add_field(name="Required level", value=f"Level {required_level}", inline=False)

        async with AsyncSessionLocal() as session:
            giveaway = Giveaway(
                guild_id=guild.id,
                channel_id=channel.id,
                message_id=0,
                prize=prize,
                winners_count=winners_count,
                end_time=end_time,
                host_id=host_id,
                required_role_id=required_role_id,
                required_level=required_level,
                ended=False
            )
            session.add(giveaway)
            await session.commit()
            await session.refresh(giveaway)

            view = GiveawayView(self, giveaway.id)
            message = await channel.send(embed=embed, view=view)

            giveaway.message_id = message.id
            await session.commit()
            await session.refresh(giveaway)

            return giveaway

    async def enter_giveaway(self, interaction: discord.Interaction, giveaway_id: int):
        giveaway = await self.get_giveaway(giveaway_id)
        if not giveaway:
            await interaction.response.send_message("This giveaway no longer exists.", ephemeral=True)
            return

        if giveaway.ended:
            await interaction.response.send_message("This giveaway has ended.", ephemeral=True)
            return

        if giveaway.required_role_id:
            member = interaction.guild.get_member(interaction.user.id)
            if not member.get_role(giveaway.required_role_id):
                await interaction.response.send_message(
                    f"You must have the role <@&{giveaway.required_role_id}> to participate.",
                    ephemeral=True
                )
                return

        if giveaway.required_level:
            from bot.systems.levels import LevelSystem
            level_system = LevelSystem(self.bot)
            user_level = await level_system.get_user_level(interaction.guild_id, interaction.user.id)
            if not user_level or user_level.level < giveaway.required_level:
                await interaction.response.send_message(
                    f"You must be level {giveaway.required_level} to participate.",
                    ephemeral=True
                )
                return

        async with AsyncSessionLocal() as session:
            existing = await session.execute(
                select(GiveawayEntry).where(
                    GiveawayEntry.giveaway_id == giveaway_id,
                    GiveawayEntry.user_id == interaction.user.id
                )
            )
            if existing.scalar_one_or_none():
                await session.execute(
                    delete(GiveawayEntry).where(
                        GiveawayEntry.giveaway_id == giveaway_id,
                        GiveawayEntry.user_id == interaction.user.id
                    )
                )
                await session.commit()
                await interaction.response.send_message("You left the giveaway.", ephemeral=True)
            else:
                entry = GiveawayEntry(
                    giveaway_id=giveaway_id,
                    user_id=interaction.user.id,
                    entered_at=datetime.utcnow()
                )
                session.add(entry)
                await session.commit()
                await interaction.response.send_message("You are entered in the giveaway! 🎉", ephemeral=True)

        await self.update_giveaway_embed(giveaway)

    async def get_entries_count(self, giveaway_id: int) -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GiveawayEntry).where(GiveawayEntry.giveaway_id == giveaway_id)
            )
            return len(result.scalars().all())

    async def update_giveaway_embed(self, giveaway: Giveaway):
        try:
            guild = self.bot.get_guild(giveaway.guild_id)
            if not guild:
                return

            channel = guild.get_channel(giveaway.channel_id)
            if not channel:
                return

            message = await channel.fetch_message(giveaway.message_id)
            if not message:
                return

            entries_count = await self.get_entries_count(giveaway.id)

            embed = message.embeds[0]

            for i, field in enumerate(embed.fields):
                if field.name == "Participants":
                    embed.set_field_at(i, name="Participants", value=f"{entries_count} participant(s)", inline=True)
                    break
            else:
                embed.add_field(name="Participants", value=f"{entries_count} participant(s)", inline=True)

            await message.edit(embed=embed)
        except:
            pass

    async def end_giveaway(self, giveaway: Giveaway):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GiveawayEntry).where(GiveawayEntry.giveaway_id == giveaway.id)
            )
            entries = result.scalars().all()

            if not entries:
                await self.announce_no_winners(giveaway)
                await session.execute(
                    update(Giveaway).where(Giveaway.id == giveaway.id).values(ended=True)
                )
                await session.commit()
                return

            winners_count = min(giveaway.winners_count, len(entries))
            winners = random.sample(entries, winners_count)

            winner_ids = [winner.user_id for winner in winners]

            await session.execute(
                update(Giveaway)
                .where(Giveaway.id == giveaway.id)
                .values(ended=True, winner_ids=winner_ids)
            )
            await session.commit()

            await self.announce_winners(giveaway, winner_ids)

    async def announce_winners(self, giveaway: Giveaway, winner_ids: List[int]):
        try:
            guild = self.bot.get_guild(giveaway.guild_id)
            if not guild:
                return

            channel = guild.get_channel(giveaway.channel_id)
            if not channel:
                return

            message = await channel.fetch_message(giveaway.message_id)
            if not message:
                return

            winners_mentions = [f"<@{winner_id}>" for winner_id in winner_ids]

            embed = discord.Embed(
                title="🎉 GIVEAWAY ENDED 🎉",
                description=f"**Prize:** {giveaway.prize}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="Winners",
                value="\n".join(winners_mentions),
                inline=False
            )
            embed.set_footer(text="Finished")

            await message.edit(embed=embed, view=None)

            await channel.send(
                f"🎉 Congratulations {', '.join(winners_mentions)}! You won **{giveaway.prize}**!"
            )
        except:
            pass

    async def announce_no_winners(self, giveaway: Giveaway):
        try:
            guild = self.bot.get_guild(giveaway.guild_id)
            if not guild:
                return

            channel = guild.get_channel(giveaway.channel_id)
            if not channel:
                return

            message = await channel.fetch_message(giveaway.message_id)
            if not message:
                return

            embed = discord.Embed(
                title="🎉 GIVEAWAY ENDED 🎉",
                description=f"**Prize:** {giveaway.prize}\n\nNo valid participants.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Finished")

            await message.edit(embed=embed, view=None)
            await channel.send("The giveaway ended without valid participants.")
        except:
            pass

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        try:
            giveaways = await self.get_active_giveaways()
            current_time = datetime.utcnow()

            for giveaway in giveaways:
                if current_time >= giveaway.end_time and not giveaway.ended:
                    await self.end_giveaway(giveaway)
        except Exception as e:
            print(f"Error checking giveaways: {e}")

    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()

    async def reroll_giveaway(self, giveaway: Giveaway) -> Optional[int]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(GiveawayEntry).where(GiveawayEntry.giveaway_id == giveaway.id)
            )
            entries = result.scalars().all()

            if not entries:
                return None

            excluded_ids = giveaway.winner_ids or []
            available_entries = [e for e in entries if e.user_id not in excluded_ids]

            if not available_entries:
                available_entries = entries

            winner = random.choice(available_entries)

            new_winner_ids = (giveaway.winner_ids or []) + [winner.user_id]
            await session.execute(
                update(Giveaway)
                .where(Giveaway.id == giveaway.id)
                .values(winner_ids=new_winner_ids)
            )
            await session.commit()

            return winner.user_id
