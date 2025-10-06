from sqlalchemy import String, Integer, BigInteger, Boolean, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.connection import Base


class Guild(Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    prefix: Mapped[str] = mapped_column(String(10), default="/", nullable=False)
    language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)

    welcome_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    welcome_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    goodbye_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    goodbye_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    goodbye_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    log_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    log_events: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    level_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    level_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    level_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    moderation_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mute_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    tickets_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tickets_category_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tickets_log_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    voice_channels_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voice_channels_category_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    voice_channels_template: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members: Mapped[list["Member"]] = relationship("Member", back_populates="guild", cascade="all, delete-orphan")
    warnings: Mapped[list["Warning"]] = relationship("Warning", back_populates="guild", cascade="all, delete-orphan")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="guild", cascade="all, delete-orphan")
    giveaways: Mapped[list["Giveaway"]] = relationship("Giveaway", back_populates="guild", cascade="all, delete-orphan")
    autoroles: Mapped[list["AutoRole"]] = relationship("AutoRole", back_populates="guild", cascade="all, delete-orphan")
    level_roles: Mapped[list["LevelRole"]] = relationship("LevelRole", back_populates="guild", cascade="all, delete-orphan")
    logs: Mapped[list["Log"]] = relationship("Log", back_populates="guild", cascade="all, delete-orphan")
    voice_channels: Mapped[list["VoiceChannel"]] = relationship("VoiceChannel", back_populates="guild", cascade="all, delete-orphan")