import discord
from discord.ext import commands
from discord import ui
from sqlalchemy import select, update, delete
from datetime import datetime
from typing import Optional, Dict
from bot.database import AsyncSessionLocal
from bot.models import VoiceConfig, TemporaryVoiceChannel


class VoiceControlView(ui.View):
    def __init__(self, voice_manager):
        super().__init__(timeout=None)
        self.voice_manager = voice_manager

    @ui.button(label="Lock", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="voice_lock")
    async def lock_channel(self, interaction: discord.Interaction, button: ui.Button):
        await self.voice_manager.lock_channel(interaction)

    @ui.button(label="Unlock", emoji="🔓", style=discord.ButtonStyle.secondary, custom_id="voice_unlock")
    async def unlock_channel(self, interaction: discord.Interaction, button: ui.Button):
        await self.voice_manager.unlock_channel(interaction)

    @ui.button(label="Hide", emoji="👁️", style=discord.ButtonStyle.secondary, custom_id="voice_hide")
    async def hide_channel(self, interaction: discord.Interaction, button: ui.Button):
        await self.voice_manager.hide_channel(interaction)

    @ui.button(label="Reveal", emoji="👀", style=discord.ButtonStyle.secondary, custom_id="voice_reveal")
    async def reveal_channel(self, interaction: discord.Interaction, button: ui.Button):
        await self.voice_manager.reveal_channel(interaction)

    @ui.button(label="Rename", emoji="✏️", style=discord.ButtonStyle.secondary, custom_id="voice_rename")
    async def rename_channel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RenameChannelModal(self.voice_manager))

    @ui.button(label="Limit", emoji="👥", style=discord.ButtonStyle.secondary, custom_id="voice_limit")
    async def limit_channel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(LimitChannelModal(self.voice_manager))

    @ui.button(label="Claim", emoji="👑", style=discord.ButtonStyle.primary, custom_id="voice_claim")
    async def claim_channel(self, interaction: discord.Interaction, button: ui.Button):
        await self.voice_manager.claim_channel(interaction)

    @ui.button(label="Permit", emoji="✅", style=discord.ButtonStyle.success, custom_id="voice_permit")
    async def permit_user(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(PermitUserModal(self.voice_manager))

    @ui.button(label="Reject", emoji="❌", style=discord.ButtonStyle.danger, custom_id="voice_reject")
    async def reject_user(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RejectUserModal(self.voice_manager))


class RenameChannelModal(ui.Modal, title="Rename Channel"):
    new_name = ui.TextInput(
        label="New Name",
        placeholder="My Voice Channel",
        required=True,
        max_length=100
    )

    def __init__(self, voice_manager):
        super().__init__()
        self.voice_manager = voice_manager

    async def on_submit(self, interaction: discord.Interaction):
        await self.voice_manager.rename_channel(interaction, self.new_name.value)


class LimitChannelModal(ui.Modal, title="User Limit"):
    limit = ui.TextInput(
        label="Limit (0 = unlimited)",
        placeholder="5",
        required=True,
        max_length=2
    )

    def __init__(self, voice_manager):
        super().__init__()
        self.voice_manager = voice_manager

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit_value = int(self.limit.value)
            if limit_value < 0 or limit_value > 99:
                await interaction.response.send_message("The limit must be between 0 and 99.", ephemeral=True)
                return
            await self.voice_manager.limit_channel(interaction, limit_value)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)


class PermitUserModal(ui.Modal, title="Permit User"):
    user_id = ui.TextInput(
        label="User ID",
        placeholder="123456789012345678",
        required=True
    )

    def __init__(self, voice_manager):
        super().__init__()
        self.voice_manager = voice_manager

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id_value = int(self.user_id.value)
            member = interaction.guild.get_member(user_id_value)
            if not member:
                await interaction.response.send_message("User not found.", ephemeral=True)
                return
            await self.voice_manager.permit_user(interaction, member)
        except ValueError:
            await interaction.response.send_message("Invalid ID.", ephemeral=True)


class RejectUserModal(ui.Modal, title="Reject User"):
    user_id = ui.TextInput(
        label="User ID",
        placeholder="123456789012345678",
        required=True
    )

    def __init__(self, voice_manager):
        super().__init__()
        self.voice_manager = voice_manager

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id_value = int(self.user_id.value)
            member = interaction.guild.get_member(user_id_value)
            if not member:
                await interaction.response.send_message("User not found.", ephemeral=True)
                return
            await self.voice_manager.reject_user(interaction, member)
        except ValueError:
            await interaction.response.send_message("Invalid ID.", ephemeral=True)


class VoiceManager:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_sessions: Dict[int, datetime] = {}
        self.bot.add_view(VoiceControlView(self))

    async def get_config(self, guild_id: int) -> Optional[VoiceConfig]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(VoiceConfig).where(VoiceConfig.guild_id == guild_id)
            )
            return result.scalar_one_or_none()

    async def create_default_config(self, guild_id: int) -> VoiceConfig:
        async with AsyncSessionLocal() as session:
            config = VoiceConfig(
                guild_id=guild_id,
                enabled=True,
                create_channel_id=None,
                category_id=None,
                channel_name_template="{username}'s voice channel",
                default_user_limit=0,
                control_message_id=None,
                control_channel_id=None
            )
            session.add(config)
            await session.commit()
            await session.refresh(config)
            return config

    async def get_temp_channel(self, channel_id: int) -> Optional[TemporaryVoiceChannel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TemporaryVoiceChannel).where(TemporaryVoiceChannel.channel_id == channel_id)
            )
            return result.scalar_one_or_none()

    async def get_user_temp_channel(self, guild_id: int, user_id: int) -> Optional[TemporaryVoiceChannel]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TemporaryVoiceChannel).where(
                    TemporaryVoiceChannel.guild_id == guild_id,
                    TemporaryVoiceChannel.owner_id == user_id
                )
            )
            return result.scalar_one_or_none()

    async def create_temp_channel(
        self,
        guild: discord.Guild,
        member: discord.Member,
        config: VoiceConfig
    ) -> Optional[discord.VoiceChannel]:
        existing = await self.get_user_temp_channel(guild.id, member.id)
        if existing:
            channel = guild.get_channel(existing.channel_id)
            if channel:
                return channel

        category = guild.get_channel(config.category_id) if config.category_id else None

        channel_name = config.channel_name_template.format(
            username=member.display_name,
            user=member.name
        )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True),
            member: discord.PermissionOverwrite(
                connect=True,
                manage_channels=True,
                move_members=True,
                mute_members=True,
                deafen_members=True
            )
        }

        try:
            channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                user_limit=config.default_user_limit
            )

            async with AsyncSessionLocal() as session:
                temp_channel = TemporaryVoiceChannel(
                    guild_id=guild.id,
                    channel_id=channel.id,
                    owner_id=member.id,
                    created_at=datetime.utcnow()
                )
                session.add(temp_channel)
                await session.commit()

            return channel
        except discord.Forbidden:
            return None

    async def delete_temp_channel(self, channel_id: int):
        temp_channel = await self.get_temp_channel(channel_id)
        if not temp_channel:
            return

        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.delete(reason="Temporary voice channel cleanup")
        except:
            pass

        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(TemporaryVoiceChannel).where(TemporaryVoiceChannel.channel_id == channel_id)
            )
            await session.commit()

    async def handle_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        config = await self.get_config(member.guild.id)
        if not config or not config.enabled:
            return

        if after.channel and after.channel.id == config.create_channel_id:
            new_channel = await self.create_temp_channel(member.guild, member, config)
            if new_channel:
                try:
                    await member.move_to(new_channel)
                except discord.Forbidden:
                    pass

        if before.channel:
            temp_channel = await self.get_temp_channel(before.channel.id)
            if temp_channel and len(before.channel.members) == 0:
                await self.delete_temp_channel(before.channel.id)

    async def check_ownership(self, interaction: discord.Interaction) -> bool:
        temp_channel = await self.get_temp_channel(interaction.channel_id)
        if not temp_channel:
            await interaction.response.send_message("This is not a temporary voice channel.", ephemeral=True)
            return False

        if temp_channel.owner_id != interaction.user.id:
            await interaction.response.send_message("You are not the owner of this channel.", ephemeral=True)
            return False

        return True

    async def lock_channel(self, interaction: discord.Interaction):
        if not await self.check_ownership(interaction):
            return

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            connect=False
        )
        await interaction.response.send_message("Channel locked. 🔒", ephemeral=True)

    async def unlock_channel(self, interaction: discord.Interaction):
        if not await self.check_ownership(interaction):
            return

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            connect=True
        )
        await interaction.response.send_message("Channel unlocked. 🔓", ephemeral=True)

    async def hide_channel(self, interaction: discord.Interaction):
        if not await self.check_ownership(interaction):
            return

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            view_channel=False
        )
        await interaction.response.send_message("Channel hidden. 👁️", ephemeral=True)

    async def reveal_channel(self, interaction: discord.Interaction):
        if not await self.check_ownership(interaction):
            return

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            view_channel=True
        )
        await interaction.response.send_message("Channel revealed. 👀", ephemeral=True)

    async def rename_channel(self, interaction: discord.Interaction, new_name: str):
        if not await self.check_ownership(interaction):
            return

        try:
            await interaction.channel.edit(name=new_name)
            await interaction.response.send_message(f"Channel renamed to: {new_name}", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Unable to rename the channel.", ephemeral=True)

    async def limit_channel(self, interaction: discord.Interaction, limit: int):
        if not await self.check_ownership(interaction):
            return

        try:
            await interaction.channel.edit(user_limit=limit)
            limit_text = f"{limit} users" if limit > 0 else "unlimited"
            await interaction.response.send_message(f"Limit set to: {limit_text}", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Unable to change the limit.", ephemeral=True)

    async def claim_channel(self, interaction: discord.Interaction):
        temp_channel = await self.get_temp_channel(interaction.channel_id)
        if not temp_channel:
            await interaction.response.send_message("This is not a temporary voice channel.", ephemeral=True)
            return

        owner = interaction.guild.get_member(temp_channel.owner_id)
        if owner and owner in interaction.channel.members:
            await interaction.response.send_message("The current owner is still in the channel.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(TemporaryVoiceChannel)
                .where(TemporaryVoiceChannel.channel_id == interaction.channel_id)
                .values(owner_id=interaction.user.id)
            )
            await session.commit()

        await interaction.channel.set_permissions(
            interaction.user,
            connect=True,
            manage_channels=True,
            move_members=True,
            mute_members=True,
            deafen_members=True
        )

        await interaction.response.send_message(f"{interaction.user.mention} is now the owner. 👑", ephemeral=False)

    async def permit_user(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.check_ownership(interaction):
            return

        await interaction.channel.set_permissions(
            member,
            connect=True,
            view_channel=True
        )
        await interaction.response.send_message(f"{member.mention} can now join the channel. ✅", ephemeral=True)

    async def reject_user(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.check_ownership(interaction):
            return

        await interaction.channel.set_permissions(
            member,
            connect=False,
            view_channel=False
        )

        if member in interaction.channel.members:
            try:
                await member.move_to(None)
            except:
                pass

        await interaction.response.send_message(f"{member.mention} can no longer join the channel. ❌", ephemeral=True)

    async def setup_control_panel(self, channel: discord.TextChannel):
        embed = discord.Embed(
            title="Temporary Voice Channel Controls",
            description="Use the buttons below to manage your temporary voice channel.",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="🔒 Lock/Unlock",
            value="Lock or unlock channel access",
            inline=False
        )
        embed.add_field(
            name="👁️ Hide/Reveal",
            value="Hide or reveal the channel",
            inline=False
        )
        embed.add_field(
            name="✏️ Rename",
            value="Rename your channel",
            inline=False
        )
        embed.add_field(
            name="👥 Limit",
            value="Set a user limit",
            inline=False
        )
        embed.add_field(
            name="👑 Claim",
            value="Claim ownership if the previous owner left",
            inline=False
        )
        embed.add_field(
            name="✅ Permit / ❌ Reject",
            value="Allow or reject specific users",
            inline=False
        )

        view = VoiceControlView(self)
        message = await channel.send(embed=embed, view=view)

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(VoiceConfig)
                .where(VoiceConfig.guild_id == channel.guild.id)
                .values(control_message_id=message.id, control_channel_id=channel.id)
            )
            await session.commit()
