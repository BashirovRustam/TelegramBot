from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from telegram_bot_app.db.base import Base


class Salon(Base):
    __tablename__ = "salons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    services: Mapped[list["Service"]] = relationship("Service", back_populates="salon")
    masters: Mapped[list["Master"]] = relationship("Master", back_populates="salon")
    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="salon")

    def __repr__(self) -> str:
        return f"Salon(id={self.id}, name='{self.name}', address='{self.address}')"

    def __str__(self):
        return f"{self.name}"
