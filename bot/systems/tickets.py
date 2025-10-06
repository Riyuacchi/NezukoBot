import discord
from discord.ext import commands
from discord import ui
from sqlalchemy import select, update
from datetime import datetime
from typing import Optional
from bot.database import AsyncSessionLocal
from bot.models import TicketConfig, Ticket


class TicketControlView(ui.View):
    def __init__(self, ticket_system):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system

    @ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await self.ticket_system.close_ticket(interaction)

    @ui.button(label="Claim", style=discord.ButtonStyle.primary, custom_id="ticket_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await self.ticket_system.claim_ticket(interaction)

    @ui.button(label="Add Member", style=discord.ButtonStyle.secondary, custom_id="ticket_add")
    async def add_member(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(AddMemberModal(self.ticket_system))

    @ui.button(label="Remove Member", style=discord.ButtonStyle.secondary, custom_id="ticket_remove")
    async def remove_member(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RemoveMemberModal(self.ticket_system))


class TicketCreateView(ui.View):
    def __init__(self, ticket_system, category_name: str):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.category_name = category_name

    @ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="ticket_create")
    async def create_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await self.ticket_system.create_ticket(interaction, self.category_name)


class AddMemberModal(ui.Modal, title="Add Member"):
    member_id = ui.TextInput(
        label="Member ID",
        placeholder="123456789012345678",
        required=True
    )

    def __init__(self, ticket_system):
        super().__init__()
        self.ticket_system = ticket_system

    async def on_submit(self, interaction: discord.Interaction):
        try:
            member_id = int(self.member_id.value)
            member = interaction.guild.get_member(member_id)
            if not member:
                await interaction.response.send_message("Member not found.", ephemeral=True)
                return

            await interaction.channel.set_permissions(member, read_messages=True, send_messages=True)
            await interaction.response.send_message(f"{member.mention} was added to the ticket.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid ID.", ephemeral=True)


class RemoveMemberModal(ui.Modal, title="Remove Member"):
    member_id = ui.TextInput(
        label="Member ID",
        placeholder="123456789012345678",
        required=True
    )

    def __init__(self, ticket_system):
        super().__init__()
        self.ticket_system = ticket_system

    async def on_submit(self, interaction: discord.Interaction):
        try:
            member_id = int(self.member_id.value)
            member = interaction.guild.get_member(member_id)
            if not member:
                await interaction.response.send_message("Member not found.", ephemeral=True)
                return

            await interaction.channel.set_permissions(member, overwrite=None)
            await interaction.response.send_message(f"{member.mention} was removed from the ticket.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid ID.", ephemeral=True)


class TicketSystem:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(TicketControlView(self))

    async def get_config(self, guild_id: int) -> Optional[TicketConfig]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TicketConfig).where(TicketConfig.guild_id == guild_id)
            )
            return result.scalar_one_or_none()

    async def create_default_config(self, guild_id: int) -> TicketConfig:
        async with AsyncSessionLocal() as session:
            config = TicketConfig(
                guild_id=guild_id,
                enabled=True,
                category_id=None,
                support_role_id=None,
                log_channel_id=None,
                ticket_counter=0,
                welcome_message="Thanks for opening a ticket. A staff member will respond shortly.",
                categories={"Support": "🎫", "Report": "🚨", "Other": "📝"}
            )
            session.add(config)
            await session.commit()
            await session.refresh(config)
            return config

    async def get_ticket(self, channel_id: int) -> Optional[Ticket]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Ticket).where(Ticket.channel_id == channel_id)
            )
            return result.scalar_one_or_none()

    async def create_ticket(self, interaction: discord.Interaction, category_name: str):
        config = await self.get_config(interaction.guild_id)
        if not config or not config.enabled:
            await interaction.response.send_message("The ticket system is disabled.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            existing = await session.execute(
                select(Ticket).where(
                    Ticket.guild_id == interaction.guild_id,
                    Ticket.user_id == interaction.user.id,
                    Ticket.status == "open"
                )
            )
            if existing.scalar_one_or_none():
                await interaction.response.send_message("You already have an open ticket.", ephemeral=True)
                return

            config.ticket_counter += 1
            ticket_number = config.ticket_counter

            category = interaction.guild.get_channel(config.category_id) if config.category_id else None

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            if config.support_role_id:
                support_role = interaction.guild.get_role(config.support_role_id)
                if support_role:
                    overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            emoji = config.categories.get(category_name, "🎫")
            channel = await interaction.guild.create_text_channel(
                name=f"{emoji}ticket-{ticket_number:04d}",
                category=category,
                overwrites=overwrites
            )

            ticket = Ticket(
                guild_id=interaction.guild_id,
                channel_id=channel.id,
                user_id=interaction.user.id,
                ticket_number=ticket_number,
                category=category_name,
                status="open",
                created_at=datetime.utcnow()
            )
            session.add(ticket)

            await session.execute(
                update(TicketConfig)
                .where(TicketConfig.guild_id == interaction.guild_id)
                .values(ticket_counter=ticket_number)
            )

            await session.commit()

        embed = discord.Embed(
            title=f"Ticket #{ticket_number:04d}",
            description=config.welcome_message,
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Category", value=category_name, inline=True)
        embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"Ticket ID: {ticket_number}")

        await channel.send(content=interaction.user.mention, embed=embed, view=TicketControlView(self))
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

    async def close_ticket(self, interaction: discord.Interaction):
        ticket = await self.get_ticket(interaction.channel_id)
        if not ticket:
            await interaction.response.send_message("This channel is not registered as a ticket.", ephemeral=True)
            return

        if ticket.status == "closed":
            await interaction.response.send_message("This ticket is already closed.", ephemeral=True)
            return

        config = await self.get_config(interaction.guild_id)

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Ticket)
                .where(Ticket.channel_id == interaction.channel_id)
                .values(status="closed", closed_at=datetime.utcnow(), closed_by=interaction.user.id)
            )
            await session.commit()

        embed = discord.Embed(
            title="Ticket Closed",
            description=f"This ticket was closed by {interaction.user.mention}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        await interaction.response.send_message(embed=embed)

        if config and config.log_channel_id:
            log_channel = interaction.guild.get_channel(config.log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title=f"Ticket #{ticket.ticket_number:04d} Closed",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                log_embed.add_field(name="Created by", value=f"<@{ticket.user_id}>", inline=True)
                log_embed.add_field(name="Closed by", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="Category", value=ticket.category, inline=True)
                await log_channel.send(embed=log_embed)

        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")

    async def claim_ticket(self, interaction: discord.Interaction):
        ticket = await self.get_ticket(interaction.channel_id)
        if not ticket:
            await interaction.response.send_message("This channel is not registered as a ticket.", ephemeral=True)
            return

        if ticket.claimed_by:
            claimed_user = interaction.guild.get_member(ticket.claimed_by)
            await interaction.response.send_message(
                f"This ticket is already claimed by {claimed_user.mention if claimed_user else 'another member'}.",
                ephemeral=True
            )
            return

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Ticket)
                .where(Ticket.channel_id == interaction.channel_id)
                .values(claimed_by=interaction.user.id, claimed_at=datetime.utcnow())
            )
            await session.commit()

        embed = discord.Embed(
            title="Ticket Claim",
            description=f"This ticket was claimed by {interaction.user.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        await interaction.response.send_message(embed=embed)

    async def setup_panel(self, channel: discord.TextChannel, category_name: str):
        config = await self.get_config(channel.guild.id)
        if not config:
            config = await self.create_default_config(channel.guild.id)

        emoji = config.categories.get(category_name, "🎫")

        embed = discord.Embed(
            title=f"{emoji} Ticket System - {category_name}",
            description=f"Click the button below to create a ticket in the **{category_name}** category.\n\nOur team will respond as soon as possible.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Server: {channel.guild.name}")

        view = TicketCreateView(self, category_name)
        await channel.send(embed=embed, view=view)
