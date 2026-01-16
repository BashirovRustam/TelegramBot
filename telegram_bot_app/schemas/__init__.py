# Import all schemas for easy access
from .user import UserCreate, UserUpdate, UserRead
from .salon import SalonCreate, SalonUpdate, SalonRead
from .service import ServiceCreate, ServiceUpdate, ServiceRead
from .master import MasterCreate, MasterUpdate, MasterRead
from .master_service import MasterServiceCreate, MasterServiceUpdate, MasterServiceRead
from .master_schedule import MasterScheduleCreate, MasterScheduleUpdate, MasterScheduleRead
from .appointment import AppointmentCreate, AppointmentUpdate, AppointmentRead

# List of all schemas
__all__ = [
    # User schemas
    "UserCreate",
    "UserUpdate", 
    "UserRead",
    
    # Salon schemas
    "SalonCreate",
    "SalonUpdate",
    "SalonRead",
    
    # Service schemas
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceRead",
    
    # Master schemas
    "MasterCreate",
    "MasterUpdate",
    "MasterRead",
    
    # MasterService schemas
    "MasterServiceCreate",
    "MasterServiceUpdate",
    "MasterServiceRead",
    
    # MasterSchedule schemas
    "MasterScheduleCreate",
    "MasterScheduleUpdate",
    "MasterScheduleRead",
    
    # Appointment schemas
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentRead",
]
