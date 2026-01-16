from sqlalchemy import Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    salon_id: Mapped[int] = mapped_column(Integer, ForeignKey("salons.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="master_profile")
    salon: Mapped["Salon"] = relationship("Salon", back_populates="masters")
    master_services: Mapped[list["MasterService"]] = relationship("MasterService", back_populates="master")
    schedules: Mapped[list["MasterSchedule"]] = relationship("MasterSchedule", back_populates="master")
    appointments: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="master")

    def __repr__(self) -> str:
        return f"Master(id={self.id}, user_id={self.user_id}, salon_id={self.salon_id})"
