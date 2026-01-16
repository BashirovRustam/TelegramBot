# Import all models for easy access
from .user import User, UserRoleEnum
from .salon import Salon
from .service import Service
from .master import Master
from .master_service import MasterService
from .master_schedule import MasterSchedule
from .appointment import Appointment, AppointmentStatusEnum

# List of all models for Alembic auto-generation
__all__ = [
    "User",
    "UserRoleEnum",
    "Salon", 
    "Service",
    "Master",
    "MasterService",
    "MasterSchedule",
    "Appointment",
    "AppointmentStatusEnum",
]
