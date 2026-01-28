from datetime import date, datetime, timedelta, time
from typing import List, Dict, Tuple
import logging
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_bot_app.crud.master_schedule import MasterScheduleCRUD
from telegram_bot_app.crud.appointment import AppointmentCRUD
from telegram_bot_app.models.appointment import AppointmentStatusEnum

# Создаем логгер
logger = logging.getLogger(__name__)


class MasterAvailabilityService:
    def __init__(self, db: AsyncSession, timezone: str = "Asia/Almaty"):
        self.db = db
        self.schedule_crud = MasterScheduleCRUD(db)
        self.appointment_crud = AppointmentCRUD(db)
        self.timezone = ZoneInfo(timezone)

    async def get_available_dates(
            self,
            master_id: int,
            service_duration_minutes: int,
            days_ahead: int = 14
    ) -> List[date]:
        """Получить список доступных дат для записи к мастеру."""

        logger.info(
            "Поиск доступных дат: master_id=%d, duration=%d мин, days_ahead=%d",
            master_id, service_duration_minutes, days_ahead
        )

        try:
            available_dates = []
            today = date.today()

            for day_offset in range(days_ahead):
                check_date = today + timedelta(days=day_offset)
                weekday = check_date.weekday()

                # Получаем расписание мастера на этот день недели
                schedules = await self.schedule_crud.get_by_master_and_weekday(
                    master_id, weekday
                )

                if not schedules:
                    continue

                # Проверяем, есть ли свободные слоты в этот день
                has_available_slots = await self._check_day_availability(
                    master_id, check_date, schedules, service_duration_minutes
                )

                if has_available_slots:
                    available_dates.append(check_date)

            logger.info(
                "Найдено доступных дат: %d для master_id=%d",
                len(available_dates), master_id
            )

            return available_dates

        except Exception as e:
            logger.error(
                "Ошибка получения доступных дат для master_id=%d: %s",
                master_id, e, exc_info=True
            )
            return []

    async def get_available_time_slots(
            self,
            master_id: int,
            selected_date: date,
            service_duration_minutes: int
    ) -> List[time]:
        """Получить список доступных временных слотов на конкретную дату."""

        logger.info(
            "Поиск временных слотов: master_id=%d, date=%s, duration=%d мин",
            master_id, selected_date, service_duration_minutes
        )

        try:
            weekday = selected_date.weekday()

            # Получаем расписание мастера на этот день недели
            schedules = await self.schedule_crud.get_by_master_and_weekday(
                master_id, weekday
            )

            if not schedules:
                logger.warning(
                    "Расписание не найдено для master_id=%d, weekday=%d",
                    master_id, weekday
                )
                return []

            # Получаем существующие записи на эту дату
            existing_appointments = await self.appointment_crud.get_by_master_and_date(
                master_id, selected_date
            )

            # Фильтруем только активные записи (BOOKED)
            booked_appointments = [
                apt for apt in existing_appointments
                if apt.status == AppointmentStatusEnum.BOOKED
            ]

            logger.debug(
                "Занятых записей на %s: %d",
                selected_date, len(booked_appointments)
            )

            # Получаем текущее время в нужном часовом поясе
            now = datetime.now(self.timezone)
            current_date = now.date()
            # Добавляем 5 минут буфера для завершения записи
            current_time_minutes = now.hour * 60 + now.minute + 5

            # Собираем все доступные слоты
            all_available_slots = []

            for schedule in schedules:
                slots = self._get_time_slots_for_schedule(
                    schedule.time_from,
                    schedule.time_to,
                    booked_appointments,
                    service_duration_minutes
                )

                # Если выбранная дата - сегодня, фильтруем прошедшее время
                if selected_date == current_date:
                    filtered_slots = []
                    for slot in slots:
                        slot_time_minutes = slot.hour * 60 + slot.minute
                        # Оставляем только слоты, которые начинаются после текущего времени (с учетом буфера)
                        if slot_time_minutes >= current_time_minutes:
                            filtered_slots.append(slot)
                    all_available_slots.extend(filtered_slots)
                else:
                    all_available_slots.extend(slots)

            # Удаляем дубликаты и сортируем
            unique_slots = list(set(all_available_slots))
            unique_slots.sort()

            logger.info(
                "Найдено свободных слотов: %d для master_id=%d на %s",
                len(unique_slots), master_id, selected_date
            )

            return unique_slots

        except Exception as e:
            logger.error(
                "Ошибка получения временных слотов для master_id=%d, date=%s: %s",
                master_id, selected_date, e, exc_info=True
            )
            return []

    def _get_time_slots_for_schedule(
            self,
            time_from: time,
            time_to: time,
            booked_appointments: List,
            service_duration_minutes: int
    ) -> List[time]:
        """Получить доступные слоты для конкретного расписания."""

        # Конвертируем время в минуты от начала дня
        start_minutes = time_from.hour * 60 + time_from.minute
        end_minutes = time_to.hour * 60 + time_to.minute

        # Создаем список занятых интервалов в минутах
        busy_intervals = []
        for apt in booked_appointments:
            apt_start = apt.time_start.hour * 60 + apt.time_start.minute
            apt_end = apt.time_end.hour * 60 + apt.time_end.minute
            busy_intervals.append((apt_start, apt_end))

        # Сортируем занятые интервалы
        busy_intervals.sort()

        # Генерируем возможные слоты с шагом 30 минут
        available_slots = []
        current_time = start_minutes

        while current_time + service_duration_minutes <= end_minutes:
            slot_end = current_time + service_duration_minutes

            # Проверяем, не пересекается ли текущий слот с занятыми
            is_slot_free = True

            for busy_start, busy_end in busy_intervals:
                if self._time_intervals_overlap(
                        current_time, slot_end, busy_start, busy_end
                ):
                    is_slot_free = False
                    break

            if is_slot_free:
                # Конвертируем обратно в time объект
                hour = current_time // 60
                minute = current_time % 60
                available_slots.append(time(hour=hour, minute=minute))

            # Переходим к следующему слоту (шаг 30 минут)
            current_time += 30

        return available_slots

    async def _check_day_availability(
            self,
            master_id: int,
            check_date: date,
            schedules: List,
            service_duration_minutes: int
    ) -> bool:
        """Проверить, есть ли свободные слоты в конкретный день."""

        # Получаем существующие записи на эту дату
        existing_appointments = await self.appointment_crud.get_by_master_and_date(
            master_id, check_date
        )

        # Фильтруем только активные записи (BOOKED)
        booked_appointments = [
            apt for apt in existing_appointments
            if apt.status == AppointmentStatusEnum.BOOKED
        ]

        # Получаем текущее время в нужном часовом поясе
        now = datetime.now(self.timezone)
        current_date = now.date()
        # Добавляем 5 минут буфера для завершения записи
        current_time_minutes = now.hour * 60 + now.minute + 5

        # Для каждого расписания проверяем доступность
        for schedule in schedules:
            # Получаем все возможные слоты
            slots = self._get_time_slots_for_schedule(
                schedule.time_from,
                schedule.time_to,
                booked_appointments,
                service_duration_minutes
            )

            # Если проверяем сегодняшний день, учитываем текущее время
            if check_date == current_date:
                for slot in slots:
                    slot_time_minutes = slot.hour * 60 + slot.minute
                    if slot_time_minutes >= current_time_minutes:
                        return True
            else:
                # Для будущих дней достаточно наличия хотя бы одного слота
                if slots:
                    return True

        return False

    def _has_available_time_slots(
            self,
            time_from: time,
            time_to: time,
            booked_appointments: List,
            service_duration_minutes: int
    ) -> bool:
        """Проверить наличие свободных временных слотов."""

        # Конвертируем время в минуты от начала дня для удобства расчетов
        start_minutes = time_from.hour * 60 + time_from.minute
        end_minutes = time_to.hour * 60 + time_to.minute

        # Создаем список занятых интервалов в минутах
        busy_intervals = []
        for apt in booked_appointments:
            apt_start = apt.time_start.hour * 60 + apt.time_start.minute
            apt_end = apt.time_end.hour * 60 + apt.time_end.minute
            busy_intervals.append((apt_start, apt_end))

        # Сортируем занятые интервалы по началу времени
        busy_intervals.sort()

        # Проверяем наличие свободных слотов
        current_time = start_minutes

        while current_time + service_duration_minutes <= end_minutes:
            # Проверяем, не пересекается ли текущий слот с занятыми
            slot_end = current_time + service_duration_minutes
            is_slot_free = True

            for busy_start, busy_end in busy_intervals:
                if self._time_intervals_overlap(
                        current_time, slot_end, busy_start, busy_end
                ):
                    is_slot_free = False
                    break

            if is_slot_free:
                return True

            # Переходим к следующему возможному слоту (с шагом 30 минут)
            current_time += 30

        return False

    def _time_intervals_overlap(
            self,
            start1: int,
            end1: int,
            start2: int,
            end2: int
    ) -> bool:
        """Проверить пересечение двух временных интервалов."""
        return not (end1 <= start2 or start1 >= end2)