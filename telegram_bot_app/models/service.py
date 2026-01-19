from sqlalchemy import String, Boolean, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from telegram_bot_app.db.base import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    salon_id: Mapped[int] = mapped_column(Integer, ForeignKey("salons.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    salon: Mapped["Salon"] = relationship("Salon", back_populates="services")
    master_services: Mapped[list["MasterService"]] = relationship("MasterService", back_populates="service")
    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="service")

    def __repr__(self) -> str:
        return f"Service(id={self.id}, name='{self.name}', duration={self.duration_minutes}min, price={self.price})"

    def __str__(self):
        return f"{self.name}"
