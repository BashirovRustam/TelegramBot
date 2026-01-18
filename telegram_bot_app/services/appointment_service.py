from datetime import datetime, time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_bot_app.crud.appointment import AppointmentCRUD
from telegram_bot_app.crud.service import ServiceCRUD
from telegram_bot_app.models.appointment import AppointmentStatusEnum
from telegram_bot_app.schemas.appointment import AppointmentCreate


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.appointment_crud = AppointmentCRUD(db)
        self.service_crud = ServiceCRUD(db)

    async def create_appointment(
            self,
            client_id: int,
            salon_id: int,
            master_id: int,
            service_id: int,
            appointment_date: str,
            appointment_time: str
    ) -> Optional[dict]:
        """Создать новую запись на услугу."""
        try:
            print(
                f"DEBUG: Creating appointment - client_id={client_id}, salon_id={salon_id}, master_id={master_id}, service_id={service_id}, date={appointment_date}, time={appointment_time}")

            # ПРОВЕРКА: время должно быть передано
            if not appointment_time:
                print("ERROR: appointment_time is None or empty!")
                return None

            # Получаем информацию об услуге
            service = await self.service_crud.get(service_id)
            if not service:
                print("DEBUG: Service not found")
                return None

            print(
                f"DEBUG: Service found - name={service.name}, duration={service.duration_minutes}, price={service.price}")

            # Конвертируем строки в datetime/time объекты
            from datetime import datetime
            date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()

            # Парсим время начала
            print(f"DEBUG: Parsing time: {appointment_time}")
            if ":" in appointment_time:
                hour, minute = map(int, appointment_time.split(":"))
            else:
                time_obj = datetime.strptime(appointment_time, "%H:%M").time()
                hour, minute = time_obj.hour, time_obj.minute

            time_start = time(hour=hour, minute=minute)

            # Вычисляем время окончания
            total_minutes = hour * 60 + minute + service.duration_minutes
            end_hour = total_minutes // 60
            end_minute = total_minutes % 60

            if end_hour >= 24:
                print("DEBUG: End time exceeds 24 hours")
                return None

            time_end = time(hour=end_hour, minute=end_minute)

            print(f"DEBUG: Time range - start={time_start}, end={time_end}")

            # Проверяем конфликт времени
            has_conflict = await self.appointment_crud.check_time_conflict(
                master_id=master_id,
                appointment_date=date_obj,
                time_start=time_start,
                time_end=time_end
            )

            print(f"DEBUG: Time conflict check result={has_conflict}")

            if has_conflict:
                print("DEBUG: Conflict detected, returning None")
                return None

            # Создаем запись
            appointment_data = AppointmentCreate(
                client_id=client_id,
                salon_id=salon_id,
                master_id=master_id,
                service_id=service_id,
                date=date_obj,
                time_start=time_start,
                time_end=time_end,
                status=AppointmentStatusEnum.BOOKED
            )

            print(f"DEBUG: Creating appointment with data={appointment_data}")

            created_appointment = await self.appointment_crud.create(appointment_data)

            print(f"DEBUG: Appointment created successfully - id={created_appointment.id}")

            # Возвращаем информацию о созданной записи
            return {
                "id": created_appointment.id,
                "client_id": created_appointment.client_id,
                "salon_id": created_appointment.salon_id,
                "master_id": created_appointment.master_id,
                "service_id": created_appointment.service_id,
                "date": created_appointment.date,
                "time_start": created_appointment.time_start,
                "time_end": created_appointment.time_end,
                "status": created_appointment.status,
                "service_name": service.name,
                "service_duration": service.duration_minutes,
                "service_price": service.price
            }

        except Exception as e:
            print(f"ERROR: Error creating appointment: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def get_client_appointments(self, client_id: int) -> list:
        """
        Получить все записи клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            list: Список записей клиента
        """
        return await self.appointment_crud.get_by_client_id(client_id)

    async def cancel_appointment(self, appointment_id: int, client_id: int) -> bool:
        """
        Отменить запись (только если она принадлежит клиенту).
        
        Args:
            appointment_id: ID записи
            client_id: ID клиента
            
        Returns:
            bool: True если запись отменена
        """
        appointment = await self.appointment_crud.get(appointment_id)
        
        if not appointment or appointment.client_id != client_id:
            return False
        
        if appointment.status != AppointmentStatusEnum.BOOKED:
            return False  # Нельзя отменить уже завершенную или отмененную запись
        
        await self.appointment_crud.cancel(appointment_id)
        return True
