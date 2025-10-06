from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.connection import Base


class Giveaway(Base):
    __tablename__ = "giveaways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)

    prize: Mapped[str] = mapped_column(String(200), nullable=False)
    winners_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    host_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    participants: Mapped[list | None] = mapped_column(JSON, nullable=True)
    winners: Mapped[list | None] = mapped_column(JSON, nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    guild: Mapped["Guild"] = relationship("Guild", back_populates="giveaways")