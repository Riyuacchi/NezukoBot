from sqlalchemy import Integer, BigInteger, JSON, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.connection import Base


class Economy(Base):
    __tablename__ = "economy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, unique=True)

    inventory: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    total_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    daily_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    work_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    member: Mapped["Member"] = relationship("Member", back_populates="economy")