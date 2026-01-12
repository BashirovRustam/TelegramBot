from datetime import datetime, date

from sqlalchemy import (
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import TaskStatusEnum


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[TaskStatusEnum] = mapped_column(
        Enum(TaskStatusEnum),
        default=TaskStatusEnum.NEW,
        nullable=False,
    )

    start_date: Mapped[date | None] = mapped_column(Date)
    deadline: Mapped[date | None] = mapped_column(Date)

    executor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    executor: Mapped["User | None"] = relationship(
        back_populates="tasks_assigned",
        foreign_keys=[executor_id],
    )

    creator: Mapped["User"] = relationship(
        back_populates="tasks_created",
        foreign_keys=[created_by],
    )

    attachments: Mapped[list["TaskAttachment"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )

    status_history: Mapped[list["TaskStatusHistory"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskStatusHistory.changed_at",
    )
