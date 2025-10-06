from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from web.routes.auth import get_current_user
from database.connection import AsyncSessionLocal
from database.models import Guild
from loguru import logger
import config


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


async def get_bot_guilds():
    try:
        from bot.client import ElainaBot
        from main import bot

        if bot and bot.guilds:
            return [
                {
                    "id": str(guild.id),
                    "name": guild.name,
                    "icon": guild.icon.url if guild.icon else None,
                    "member_count": guild.member_count,
                    "owner": guild.owner_id
                }
                for guild in bot.guilds
            ]
        return []
    except Exception as e:
        logger.error(f"Failed to get bot guilds: {e}")
        return []


async def get_user_manageable_guilds(user: dict):
    user_guilds = user.get("guilds", [])
    bot_guilds = await get_bot_guilds()
    bot_guild_ids = {g["id"] for g in bot_guilds}

    manageable = []
    for guild in user_guilds:
        permissions = int(guild.get("permissions", 0))
        is_admin = (permissions & 0x8) == 0x8 or (permissions & 0x20) == 0x20

        guild_info = {
            "id": guild["id"],
            "name": guild["name"],
            "icon": f"https://cdn.discordapp.com/icons/{guild['id']}/{guild['icon']}.png" if guild.get("icon") else None,
            "is_admin": is_admin,
            "bot_in_guild": guild["id"] in bot_guild_ids
        }

        manageable.append(guild_info)

    return manageable


@router.get("", response_class=HTMLResponse)
async def dashboard_home(request: Request, user: dict = Depends(get_current_user)):
    guilds = await get_user_manageable_guilds(user)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "guilds": guilds
        }
    )


@router.get("/{guild_id}", response_class=HTMLResponse)
async def guild_settings(
    request: Request,
    guild_id: str,
    user: dict = Depends(get_current_user)
):
    guilds = await get_user_manageable_guilds(user)
    guild = next((g for g in guilds if g["id"] == guild_id), None)

    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")

    if not guild["is_admin"]:
        raise HTTPException(status_code=403, detail="You don't have permission to manage this guild")

    if not guild["bot_in_guild"]:
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={config.CLIENT_ID}&permissions=8&scope=bot%20applications.commands&guild_id={guild_id}"
        return templates.TemplateResponse(
            "invite_bot.html",
            {
                "request": request,
                "user": user,
                "guild": guild,
                "invite_url": invite_url
            }
        )

    async with AsyncSessionLocal() as session:
        db_guild = await session.get(Guild, int(guild_id))

        if not db_guild:
            db_guild = Guild(id=int(guild_id), name=guild["name"])
            session.add(db_guild)
            await session.commit()
            await session.refresh(db_guild)

        guild_settings = {
            "id": str(db_guild.id),
            "name": db_guild.name,
            "prefix": db_guild.prefix,
            "language": db_guild.language,
            "welcome": {
                "enabled": db_guild.welcome_enabled,
                "channel_id": str(db_guild.welcome_channel_id) if db_guild.welcome_channel_id else None,
                "message": db_guild.welcome_message
            },
            "goodbye": {
                "enabled": db_guild.goodbye_enabled,
                "channel_id": str(db_guild.goodbye_channel_id) if db_guild.goodbye_channel_id else None,
                "message": db_guild.goodbye_message
            },
            "logging": {
                "channel_id": str(db_guild.log_channel_id) if db_guild.log_channel_id else None,
                "events": db_guild.log_events or {}
            },
            "levels": {
                "enabled": db_guild.level_enabled,
                "channel_id": str(db_guild.level_channel_id) if db_guild.level_channel_id else None,
                "message": db_guild.level_message
            },
            "moderation": {
                "enabled": db_guild.moderation_enabled,
                "mute_role_id": str(db_guild.mute_role_id) if db_guild.mute_role_id else None
            },
            "tickets": {
                "enabled": db_guild.tickets_enabled,
                "category_id": str(db_guild.tickets_category_id) if db_guild.tickets_category_id else None,
                "log_channel_id": str(db_guild.tickets_log_channel_id) if db_guild.tickets_log_channel_id else None
            },
            "voice": {
                "enabled": db_guild.voice_channels_enabled,
                "category_id": str(db_guild.voice_channels_category_id) if db_guild.voice_channels_category_id else None,
                "template": db_guild.voice_channels_template
            }
        }

    return templates.TemplateResponse(
        "guild_settings.html",
        {
            "request": request,
            "user": user,
            "guild": guild,
            "settings": guild_settings
        }
    )