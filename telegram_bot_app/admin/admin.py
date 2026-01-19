# app/admin/admin.py
from sqladmin import Admin
from fastapi import FastAPI

# Импортируем все Admin классы
from .models_admin.user_admin import UserAdmin
from .models_admin.salon_admin import SalonAdmin
from .models_admin.service_admin import ServiceAdmin
from .models_admin.master_admin import MasterAdmin
from .models_admin.master_service_admin import MasterServiceAdmin
from .models_admin.master_schedule_admin import MasterScheduleAdmin
from .models_admin.appointment_admin import AppointmentAdmin


def setup_admin(app: FastAPI, engine):
    admin = Admin(
        app=app,
        engine=engine,
        title="Beauty Admin"
    )

    # Регистрируем все модели
    admin.add_view(UserAdmin)
    admin.add_view(SalonAdmin)
    admin.add_view(ServiceAdmin)
    admin.add_view(MasterAdmin)
    # admin.add_view(MasterServiceAdmin)
    admin.add_view(MasterScheduleAdmin)
    admin.add_view(AppointmentAdmin)

    return admin
