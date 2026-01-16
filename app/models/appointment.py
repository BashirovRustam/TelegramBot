from datetime import datetime, date, time
from sqlalchemy import String, Integer, ForeignKey, DateTime, Date, Time, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AppointmentStatusEnum(str, Enum):
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    salon_id: Mapped[int] = mapped_column(Integer, ForeignKey("salons.id"), nullable=False)
    master_id: Mapped[int] = mapped_column(Integer, ForeignKey("masters.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time_start: Mapped[time] = mapped_column(Time, nullable=False)
    time_end: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[AppointmentStatusEnum] = mapped_column(Enum(AppointmentStatusEnum), nullable=False, default=AppointmentStatusEnum.BOOKED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    client: Mapped["User"] = relationship("User", back_populates="appointments_as_client", foreign_keys=[client_id])
    salon: Mapped["Salon"] = relationship("Salon", back_populates="appointments")
    master: Mapped["Master"] = relationship("Master", back_populates="appointments")
    service: Mapped["Service"] = relationship("Service", back_populates="appointments")

    def __repr__(self) -> str:
        return f"Appointment(id={self.id}, client_id={self.client_id}, date={self.date}, status={self.status})"
