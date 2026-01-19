from datetime import time
from sqlalchemy import Integer, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from telegram_bot_app.db.base import Base


class MasterSchedule(Base):
    __tablename__ = "master_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    master_id: Mapped[int] = mapped_column(Integer, ForeignKey("masters.id"), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-6 (Monday=0, Sunday=6)
    time_from: Mapped[time] = mapped_column(Time, nullable=False)
    time_to: Mapped[time] = mapped_column(Time, nullable=False)

    # Relationships
    master: Mapped["Master"] = relationship("Master", back_populates="schedules")
    
    @property
    def master_name(self):
        # Простой fallback - показываем ID мастера
        return f"Мастер #{self.master_id}"

    def __repr__(self) -> str:
        return f"MasterSchedule(id={self.id}, master_id={self.master_id}, weekday={self.weekday}, {self.time_from}-{self.time_to})"
