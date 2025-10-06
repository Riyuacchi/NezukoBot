from discord.ext import commands
import discord

def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

def is_moderator():
    async def predicate(ctx):
        perms = ctx.author.guild_permissions
        return perms.administrator or perms.ban_members or perms.kick_members
    return commands.check(predicate)

def in_voice():
    async def predicate(ctx):
        return ctx.author.voice is not None
    return commands.check(predicate)

def bot_in_voice():
    async def predicate(ctx):
        return ctx.guild.voice_client is not None
    return commands.check(predicate)