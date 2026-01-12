from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import TaskStatusEnum


class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"),
        nullable=False,
    )

    old_status: Mapped[TaskStatusEnum | None] = mapped_column(
        Enum(TaskStatusEnum)
    )

    new_status: Mapped[TaskStatusEnum] = mapped_column(
        Enum(TaskStatusEnum),
        nullable=False,
    )

    changed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    task: Mapped["Task"] = relationship(
        back_populates="status_history"
    )

    user: Mapped["User"] = relationship(
        back_populates="status_changes",
        foreign_keys=[changed_by],
    )
