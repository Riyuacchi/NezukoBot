from sqlalchemy import select
from database.models import Guild, Member


async def ensure_guild(session, discord_guild):
    created = False
    db_guild = await session.get(Guild, discord_guild.id)
    if not db_guild:
        db_guild = Guild(id=discord_guild.id, name=discord_guild.name)
        session.add(db_guild)
        created = True
    elif db_guild.name != discord_guild.name:
        db_guild.name = discord_guild.name
    return db_guild, created


async def ensure_member(session, guild_id, discord_member):
    created = False
    result = await session.execute(
        select(Member).where(
            Member.guild_id == guild_id,
            Member.user_id == discord_member.id
        )
    )
    db_member = result.scalar_one_or_none()
    if not db_member:
        db_member = Member(
            guild_id=guild_id,
            user_id=discord_member.id,
            username=str(discord_member)
        )
        session.add(db_member)
        created = True
    elif db_member.username != str(discord_member):
        db_member.username = str(discord_member)
    return db_member, created
