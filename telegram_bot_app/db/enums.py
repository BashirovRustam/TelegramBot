from enum import Enum


class RolesEnum(str, Enum):
    ADMIN = "ADMIN"
    EXECUTOR = "EXECUTOR"


class TaskStatusEnum(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"