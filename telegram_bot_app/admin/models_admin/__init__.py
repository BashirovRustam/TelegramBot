# Импортируем все Admin классы для удобства
from .user_admin import UserAdmin
from .salon_admin import SalonAdmin
from .service_admin import ServiceAdmin
from .master_admin import MasterAdmin
from .master_service_admin import MasterServiceAdmin
from .master_schedule_admin import MasterScheduleAdmin
from .appointment_admin import AppointmentAdmin

__all__ = [
    "UserAdmin",
    "SalonAdmin", 
    "ServiceAdmin",
    "MasterAdmin",
    "MasterServiceAdmin",
    "MasterScheduleAdmin",
    "AppointmentAdmin"
]