import discord
import config
from datetime import datetime

_bot_instance = None

def set_bot_instance(bot):
    global _bot_instance
    _bot_instance = bot

def _get_bot_name():
    if _bot_instance and hasattr(_bot_instance, 'user') and _bot_instance.user:
        return _bot_instance.user.name
    return "Bot"

def _styled_embed(description: str, title: str | None, color: discord.Color, prefix: str | None = None) -> discord.Embed:
    text = f"{prefix} {description}" if prefix else description
    embed = discord.Embed(title=title, description=text, color=color, timestamp=datetime.utcnow())
    embed.set_footer(text=_get_bot_name())
    return embed


def success_embed(description: str, title: str | None = None) -> discord.Embed:
    return _styled_embed(description, title, discord.Color.from_str("#57F287"), "✅")


def error_embed(description: str, title: str | None = None) -> discord.Embed:
    return _styled_embed(description, title, discord.Color.from_str("#ED4245"), "❌")


def info_embed(description: str, title: str | None = None) -> discord.Embed:
    return _styled_embed(description, title, discord.Color.from_str("#5865F2"))


def warning_embed(description: str, title: str | None = None) -> discord.Embed:
    return _styled_embed(description, title, discord.Color.from_str("#FEE75C"), "⚠️")


def music_embed(title: str, description: str) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.from_str("#1E90FF"),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=_get_bot_name())
    return embed
