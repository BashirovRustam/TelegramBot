#!/usr/bin/env python3

try:
    from telegram_bot_app.models.user import UserRoleEnum
    from telegram_bot_app.models.appointment import AppointmentStatusEnum
    from telegram_bot_app.schemas.user import UserCreate
    from telegram_bot_app.schemas.appointment import AppointmentCreate
    print("✅ All imports successful!")
    print(f"UserRoleEnum: {list(UserRoleEnum)}")
    print(f"AppointmentStatusEnum: {list(AppointmentStatusEnum)}")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
