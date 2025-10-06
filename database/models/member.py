from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.connection import Base


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)

    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    messages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voice_time: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_daily: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_weekly: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_work: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    warnings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="members")
    economy: Mapped["Economy"] = relationship("Economy", back_populates="member", uselist=False, cascade="all, delete-orphan")