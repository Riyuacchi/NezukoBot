from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import config


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "bot_invite": f"https://discord.com/api/oauth2/authorize?client_id={config.CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
        }
    )


@router.get("/features", response_class=HTMLResponse)
async def features(request: Request):
    user = request.session.get("user")

    features_list = [
        {
            "name": "Moderation",
            "description": "Complete moderation system with warnings, kicks, bans, and mutes",
            "icon": "shield"
        },
        {
            "name": "Leveling",
            "description": "XP and leveling system with customizable rewards",
            "icon": "star"
        },
        {
            "name": "Economy",
            "description": "Virtual currency system with daily rewards and gambling",
            "icon": "coins"
        },
        {
            "name": "Music",
            "description": "High-quality music playback from YouTube, Spotify, and more",
            "icon": "music"
        },
        {
            "name": "Tickets",
            "description": "Support ticket system for user assistance",
            "icon": "ticket"
        },
        {
            "name": "Giveaways",
            "description": "Create and manage giveaways with automatic winner selection",
            "icon": "gift"
        },
        {
            "name": "Welcome/Goodbye",
            "description": "Customizable welcome and goodbye messages",
            "icon": "wave"
        },
        {
            "name": "Logging",
            "description": "Comprehensive logging system for all server events",
            "icon": "file"
        },
        {
            "name": "Auto Moderation",
            "description": "Automatic spam, link, and profanity detection",
            "icon": "robot"
        },
        {
            "name": "Voice Channels",
            "description": "Temporary voice channels that are created on demand",
            "icon": "microphone"
        }
    ]

    return templates.TemplateResponse(
        "features.html",
        {
            "request": request,
            "user": user,
            "features": features_list
        }
    )


@router.get("/invite", response_class=HTMLResponse)
async def invite(request: Request):
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={config.CLIENT_ID}&permissions=8&scope=bot%20applications.commands"

    return templates.TemplateResponse(
        "invite.html",
        {
            "request": request,
            "user": request.session.get("user"),
            "invite_url": invite_url
        }
    )


@router.get("/status", response_class=JSONResponse)
async def status():
    try:
        from main import bot

        if bot and bot.is_ready():
            return JSONResponse(content={
                "status": "online",
                "guilds": len(bot.guilds),
                "users": sum(guild.member_count for guild in bot.guilds),
                "latency": round(bot.latency * 1000, 2)
            })
        else:
            return JSONResponse(content={
                "status": "offline",
                "guilds": 0,
                "users": 0,
                "latency": 0
            })
    except Exception:
        return JSONResponse(content={
            "status": "offline",
            "guilds": 0,
            "users": 0,
            "latency": 0
        })