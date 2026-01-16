from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class UserRoleEnum(str, Enum):
    CLIENT = "CLIENT"
    MASTER = "MASTER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRoleEnum] = mapped_column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.CLIENT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    master_profile: Mapped["Master"] = relationship("Master", back_populates="user", uselist=False)
    appointments_as_client: Mapped[list["Appointment"]] = relationship("Appointment", back_populates="client", foreign_keys="Appointment.client_id")

    def __repr__(self) -> str:
        return f"User(id={self.id}, telegram_id={self.telegram_id}, full_name='{self.full_name}', role={self.role})"
