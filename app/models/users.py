from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import RolesEnum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    role: Mapped[RolesEnum] = mapped_column(
        Enum(RolesEnum),
        default=RolesEnum.EXECUTOR,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # ✅ Relationships (SQLAlchemy 2.0 style)
    tasks_created: Mapped[list["Task"]] = relationship(
        back_populates="creator",
        foreign_keys="Task.created_by",
    )

    status_changes: Mapped[list["TaskStatusHistory"]] = relationship(
        back_populates="user",
    )

    tasks_assigned: Mapped[list["Task"]] = relationship(
        back_populates="executor",
        foreign_keys="Task.executor_id",
    )
