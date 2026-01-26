from datetime import datetime, date, time
from sqlalchemy import String, Integer, ForeignKey, DateTime, Date, Time, Enum, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from telegram_bot_app.db.base import Base
from enum import Enum as PyEnum


class AppointmentStatusEnum(str, PyEnum):
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    salon_id: Mapped[int] = mapped_column(Integer, ForeignKey("salons.id"), nullable=False)
    master_id: Mapped[int] = mapped_column(Integer, ForeignKey("masters.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time_start: Mapped[time] = mapped_column(Time, nullable=False)
    time_end: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[AppointmentStatusEnum] = mapped_column(Enum(AppointmentStatusEnum), nullable=False, default=AppointmentStatusEnum.BOOKED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # Relationships с lazy='joined' для автоматической загрузки
    client: Mapped["User"] = relationship("User", back_populates="appointments_as_client", foreign_keys=[client_id], lazy="joined")
    salon: Mapped["Salon"] = relationship("Salon", back_populates="appointments", lazy="joined")
    master: Mapped["Master"] = relationship("Master", back_populates="appointments", lazy="joined")
    service: Mapped["Service"] = relationship("Service", back_populates="appointments", lazy="joined")

    @property
    def client_name(self):
        if self.client and hasattr(self.client, 'full_name'):
            return self.client.full_name
        return "БЕЗ ИМЕНИ"

    def __repr__(self) -> str:
        return f"Appointment(id={self.id}, client_id={self.client_id}, date={self.date}, status={self.status})"