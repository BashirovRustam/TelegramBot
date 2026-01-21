from datetime import datetime, time
from typing import Optional
import logging  # НОВОЕ
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_bot_app.crud.appointment import AppointmentCRUD
from telegram_bot_app.crud.service import ServiceCRUD
from telegram_bot_app.models.appointment import AppointmentStatusEnum
from telegram_bot_app.schemas.appointment import AppointmentCreate

# Создаем логгер для этого модуля
logger = logging.getLogger(__name__)


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

        # ============================================
        # 🟢 INFO - начало операции
        # ============================================
        logger.info(
            "Создание записи: client_id=%d, salon_id=%d, master_id=%d, service_id=%d, date=%s, time=%s",
            client_id, salon_id, master_id, service_id, appointment_date, appointment_time
        )

        try:
            # Проверка времени
            if not appointment_time:
                # ⚠️ WARNING - странная ситуация, но не критично
                logger.warning("Время записи не указано для клиента %d", client_id)
                return None

            # Получаем услугу
            service = await self.service_crud.get(service_id)
            if not service:
                # ⚠️ WARNING - услуга не найдена
                logger.warning("Услуга service_id=%d не найдена", service_id)
                return None

            logger.debug(
                "Услуга найдена: name=%s, duration=%d мин, price=%d тг",
                service.name, service.duration_minutes, service.price
            )

            # Парсим дату и время
            from datetime import datetime
            date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()

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
                # ⚠️ WARNING - время выходит за рамки дня
                logger.warning(
                    "Время окончания записи выходит за 24:00 для клиента %d (начало: %s, длительность: %d мин)",
                    client_id, time_start, service.duration_minutes
                )
                return None

            time_end = time(hour=end_hour, minute=end_minute)

            logger.debug("Временной слот: %s - %s", time_start, time_end)

            # Проверяем конфликт времени
            has_conflict = await self.appointment_crud.check_time_conflict(
                master_id=master_id,
                appointment_date=date_obj,
                time_start=time_start,
                time_end=time_end
            )

            if has_conflict:
                # ⚠️ WARNING - время занято
                logger.warning(
                    "Конфликт времени: master_id=%d, date=%s, time=%s-%s",
                    master_id, date_obj, time_start, time_end
                )
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

            created_appointment = await self.appointment_crud.create(appointment_data)

            # ============================================
            # 🟢 INFO - успешное создание
            # ============================================
            logger.info(
                "✅ Запись #%d успешно создана: client_id=%d, service=%s, date=%s %s",
                created_appointment.id, client_id, service.name, date_obj, time_start
            )

            # Возвращаем информацию
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
            # ============================================
            # 🔴 ERROR - ошибка при создании
            # ============================================
            logger.error(
                "Ошибка создания записи для client_id=%d: %s",
                client_id, e, exc_info=True  # exc_info=True добавит полный traceback
            )
            return None

    async def cancel_appointment(self, appointment_id: int, client_id: int) -> bool:
        """Отменить запись."""

        logger.info("Отмена записи #%d клиентом %d", appointment_id, client_id)

        try:
            appointment = await self.appointment_crud.get(appointment_id)

            if not appointment or appointment.client_id != client_id:
                logger.warning(
                    "Запись #%d не найдена или не принадлежит клиенту %d",
                    appointment_id, client_id
                )
                return False

            if appointment.status != AppointmentStatusEnum.BOOKED:
                logger.warning(
                    "Запись #%d уже отменена или завершена (status=%s)",
                    appointment_id, appointment.status
                )
                return False

            await self.appointment_crud.cancel(appointment_id)

            logger.info("✅ Запись #%d успешно отменена", appointment_id)

            # Отправляем уведомление через Celery
            from telegram_bot_app.celery_app.tasks import send_cancellation_notification
            send_cancellation_notification.delay(appointment_id, appointment.client.telegram_id)

            return True

        except Exception as e:
            logger.error(
                "Ошибка отмены записи #%d: %s",
                appointment_id, e, exc_info=True
            )
            return False