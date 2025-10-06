from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.connection import Base
import enum


class LogType(enum.Enum):
    MESSAGE_DELETE = "message_delete"
    MESSAGE_EDIT = "message_edit"
    MEMBER_JOIN = "member_join"
    MEMBER_LEAVE = "member_leave"
    MEMBER_BAN = "member_ban"
    MEMBER_UNBAN = "member_unban"
    MEMBER_KICK = "member_kick"
    ROLE_CREATE = "role_create"
    ROLE_DELETE = "role_delete"
    ROLE_UPDATE = "role_update"
    CHANNEL_CREATE = "channel_create"
    CHANNEL_DELETE = "channel_delete"
    CHANNEL_UPDATE = "channel_update"
    VOICE_JOIN = "voice_join"
    VOICE_LEAVE = "voice_leave"
    VOICE_MOVE = "voice_move"
    WARN = "warn"
    MUTE = "mute"
    UNMUTE = "unmute"


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)

    log_type: Mapped[LogType] = mapped_column(Enum(LogType), nullable=False)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    moderator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="logs")