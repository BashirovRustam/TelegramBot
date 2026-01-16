# Import all CRUD classes for easy access
from .user import UserCRUD, get_user_crud
from .salon import SalonCRUD, get_salon_crud
from .service import ServiceCRUD, get_service_crud
from .master import MasterCRUD, get_master_crud
from .master_service import MasterServiceCRUD, get_master_service_crud
from .master_schedule import MasterScheduleCRUD, get_master_schedule_crud
from .appointment import AppointmentCRUD, get_appointment_crud

# List of all CRUD classes and dependency functions
__all__ = [
    # CRUD classes
    "UserCRUD",
    "SalonCRUD",
    "ServiceCRUD",
    "MasterCRUD",
    "MasterServiceCRUD",
    "MasterScheduleCRUD",
    "AppointmentCRUD",
    
    # Dependency functions
    "get_user_crud",
    "get_salon_crud",
    "get_service_crud",
    "get_master_crud",
    "get_master_service_crud",
    "get_master_schedule_crud",
    "get_appointment_crud",
]
