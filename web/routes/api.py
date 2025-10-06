from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from web.routes.auth import get_current_user
from database.connection import AsyncSessionLocal
from database.models import Guild, Member, Warning, Ticket, Giveaway, AutoRole, LevelRole
from sqlalchemy import select, func
from loguru import logger


router = APIRouter()


class GuildSettingsUpdate(BaseModel):
    prefix: Optional[str] = Field(None, min_length=1, max_length=10)
    language: Optional[str] = Field(None, pattern="^(fr|en)$")
    welcome_enabled: Optional[bool] = None
    welcome_channel_id: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_enabled: Optional[bool] = None
    goodbye_channel_id: Optional[int] = None
    goodbye_message: Optional[str] = None
    log_channel_id: Optional[int] = None
    log_events: Optional[Dict[str, bool]] = None
    level_enabled: Optional[bool] = None
    level_channel_id: Optional[int] = None
    level_message: Optional[str] = None
    moderation_enabled: Optional[bool] = None
    mute_role_id: Optional[int] = None
    tickets_enabled: Optional[bool] = None
    tickets_category_id: Optional[int] = None
    tickets_log_channel_id: Optional[int] = None
    voice_channels_enabled: Optional[bool] = None
    voice_channels_category_id: Optional[int] = None
    voice_channels_template: Optional[str] = None


async def check_guild_permission(guild_id: str, user: dict):
    user_guilds = user.get("guilds", [])
    guild = next((g for g in user_guilds if g["id"] == guild_id), None)

    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")

    permissions = int(guild.get("permissions", 0))
    is_admin = (permissions & 0x8) == 0x8 or (permissions & 0x20) == 0x20

    if not is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to manage this guild")

    return True


@router.get("/guilds")
async def get_guilds(request: Request, user: dict = Depends(get_current_user)):
    user_guilds = user.get("guilds", [])

    return JSONResponse(content={
        "guilds": [
            {
                "id": guild["id"],
                "name": guild["name"],
                "icon": f"https://cdn.discordapp.com/icons/{guild['id']}/{guild['icon']}.png" if guild.get("icon") else None,
                "owner": guild.get("owner", False),
                "permissions": guild.get("permissions", 0)
            }
            for guild in user_guilds
        ]
    })


@router.get("/guilds/{guild_id}")
async def get_guild(
    guild_id: str,
    user: dict = Depends(get_current_user)
):
    await check_guild_permission(guild_id, user)

    async with AsyncSessionLocal() as session:
        guild = await session.get(Guild, int(guild_id))

        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found in database")

        return JSONResponse(content={
            "id": str(guild.id),
            "name": guild.name,
            "prefix": guild.prefix,
            "language": guild.language,
            "welcome_enabled": guild.welcome_enabled,
            "welcome_channel_id": str(guild.welcome_channel_id) if guild.welcome_channel_id else None,
            "welcome_message": guild.welcome_message,
            "goodbye_enabled": guild.goodbye_enabled,
            "goodbye_channel_id": str(guild.goodbye_channel_id) if guild.goodbye_channel_id else None,
            "goodbye_message": guild.goodbye_message,
            "log_channel_id": str(guild.log_channel_id) if guild.log_channel_id else None,
            "log_events": guild.log_events,
            "level_enabled": guild.level_enabled,
            "level_channel_id": str(guild.level_channel_id) if guild.level_channel_id else None,
            "level_message": guild.level_message,
            "moderation_enabled": guild.moderation_enabled,
            "mute_role_id": str(guild.mute_role_id) if guild.mute_role_id else None,
            "tickets_enabled": guild.tickets_enabled,
            "tickets_category_id": str(guild.tickets_category_id) if guild.tickets_category_id else None,
            "tickets_log_channel_id": str(guild.tickets_log_channel_id) if guild.tickets_log_channel_id else None,
            "voice_channels_enabled": guild.voice_channels_enabled,
            "voice_channels_category_id": str(guild.voice_channels_category_id) if guild.voice_channels_category_id else None,
            "voice_channels_template": guild.voice_channels_template
        })


@router.patch("/guilds/{guild_id}")
async def update_guild_settings(
    guild_id: str,
    settings: GuildSettingsUpdate,
    user: dict = Depends(get_current_user)
):
    await check_guild_permission(guild_id, user)

    async with AsyncSessionLocal() as session:
        guild = await session.get(Guild, int(guild_id))

        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found in database")

        update_data = settings.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if hasattr(guild, key):
                setattr(guild, key, value)

        await session.commit()
        await session.refresh(guild)

        logger.info(f"Guild {guild_id} settings updated by user {user['id']}")

        return JSONResponse(content={
            "success": True,
            "message": "Guild settings updated successfully"
        })


@router.get("/guilds/{guild_id}/stats")
async def get_guild_stats(
    guild_id: str,
    user: dict = Depends(get_current_user)
):
    await check_guild_permission(guild_id, user)

    async with AsyncSessionLocal() as session:
        guild = await session.get(Guild, int(guild_id))

        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found in database")

        total_members = await session.scalar(
            select(func.count(Member.id)).where(Member.guild_id == int(guild_id))
        )

        total_warnings = await session.scalar(
            select(func.count(Warning.id)).where(Warning.guild_id == int(guild_id))
        )

        total_tickets = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.guild_id == int(guild_id))
        )

        total_giveaways = await session.scalar(
            select(func.count(Giveaway.id)).where(Giveaway.guild_id == int(guild_id))
        )
        total_autoroles = await session.scalar(
            select(func.count(AutoRole.id)).where(AutoRole.guild_id == int(guild_id))
        )
        total_level_roles = await session.scalar(
            select(func.count(LevelRole.id)).where(LevelRole.guild_id == int(guild_id))
        )

        return JSONResponse(content={
            "total_members": total_members or 0,
            "total_warnings": total_warnings or 0,
            "total_tickets": total_tickets or 0,
            "total_giveaways": total_giveaways or 0,
            "total_autoroles": total_autoroles or 0,
            "total_level_roles": total_level_roles or 0
        })


@router.get("/guilds/{guild_id}/members")
async def get_guild_members(
    guild_id: str,
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    await check_guild_permission(guild_id, user)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Member)
            .where(Member.guild_id == int(guild_id))
            .order_by(Member.xp.desc())
            .limit(limit)
            .offset(offset)
        )

        members = result.scalars().all()

        return JSONResponse(content={
            "members": [
                {
                    "id": str(member.id),
                    "guild_id": str(member.guild_id),
                    "xp": member.xp,
                    "level": member.level,
                    "coins": member.coins,
                    "messages_count": member.messages_count
                }
                for member in members
            ],
            "limit": limit,
            "offset": offset
        })


@router.delete("/guilds/{guild_id}/reset")
async def reset_guild_settings(
    guild_id: str,
    user: dict = Depends(get_current_user)
):
    await check_guild_permission(guild_id, user)

    async with AsyncSessionLocal() as session:
        guild = await session.get(Guild, int(guild_id))

        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found in database")

        guild.prefix = "!"
        guild.language = "fr"
        guild.welcome_enabled = False
        guild.welcome_channel_id = None
        guild.welcome_message = None
        guild.goodbye_enabled = False
        guild.goodbye_channel_id = None
        guild.goodbye_message = None
        guild.log_channel_id = None
        guild.log_events = None
        guild.level_enabled = True
        guild.level_channel_id = None
        guild.level_message = None
        guild.moderation_enabled = True
        guild.mute_role_id = None
        guild.tickets_enabled = False
        guild.tickets_category_id = None
        guild.tickets_log_channel_id = None
        guild.voice_channels_enabled = False
        guild.voice_channels_category_id = None
        guild.voice_channels_template = None

        await session.commit()

        logger.info(f"Guild {guild_id} settings reset by user {user['id']}")

        return JSONResponse(content={
            "success": True,
            "message": "Guild settings reset to default"
        })