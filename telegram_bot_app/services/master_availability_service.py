from datetime import date, datetime, timedelta, time
from typing import List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_bot_app.crud.master_schedule import MasterScheduleCRUD
from telegram_bot_app.crud.appointment import AppointmentCRUD
from telegram_bot_app.models.appointment import AppointmentStatusEnum


class MasterAvailabilityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.schedule_crud = MasterScheduleCRUD(db)
        self.appointment_crud = AppointmentCRUD(db)

    async def get_available_dates(
        self,
        master_id: int,
        service_duration_minutes: int,
        days_ahead: int = 14
    ) -> List[date]:
        """
        Получить список доступных дат для записи к мастеру.
        
        Args:
            master_id: ID мастера
            service_duration_minutes: Длительность услуги в минутах
            days_ahead: Количество дней для проверки (по умолчанию 14)
            
        Returns:
            List[date]: Список доступных дат
        """
        available_dates = []
        today = date.today()
        
        for day_offset in range(days_ahead):
            check_date = today + timedelta(days=day_offset)
            weekday = check_date.weekday()  # 0=Monday, 6=Sunday
            
            # Получаем расписание мастера на этот день недели
            schedules = await self.schedule_crud.get_by_master_and_weekday(
                master_id, weekday
            )
            
            if not schedules:
                continue  # У мастера нет работы в этот день
                
            # Проверяем, есть ли свободные слоты в этот день
            has_available_slots = await self._check_day_availability(
                master_id, check_date, schedules, service_duration_minutes
            )
            
            if has_available_slots:
                available_dates.append(check_date)
        
        return available_dates

    async def get_available_time_slots(
        self,
        master_id: int,
        selected_date: date,
        service_duration_minutes: int
    ) -> List[time]:
        """
        Получить список доступных временных слотов на конкретную дату.
        
        Args:
            master_id: ID мастера
            selected_date: Выбранная дата
            service_duration_minutes: Длительность услуги в минутах
            
        Returns:
            List[time]: Список доступных временных слотов
        """
        weekday = selected_date.weekday()
        
        # Получаем расписание мастера на этот день недели
        schedules = await self.schedule_crud.get_by_master_and_weekday(
            master_id, weekday
        )
        
        if not schedules:
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
        
        # Собираем все доступные слоты
        all_available_slots = []
        
        for schedule in schedules:
            slots = self._get_time_slots_for_schedule(
                schedule.time_from,
                schedule.time_to,
                booked_appointments,
                service_duration_minutes
            )
            all_available_slots.extend(slots)
        
        # Удаляем дубликаты и сортируем
        unique_slots = list(set(all_available_slots))
        unique_slots.sort()
        
        return unique_slots

    def _get_time_slots_for_schedule(
        self,
        time_from: time,
        time_to: time,
        booked_appointments: List,
        service_duration_minutes: int
    ) -> List[time]:
        """
        Получить доступные слоты для конкретного расписания.
        
        Args:
            time_from: Начало рабочего времени
            time_to: Конец рабочего времени
            booked_appointments: Список забронированных записей
            service_duration_minutes: Длительность услуги
            
        Returns:
            List[time]: Список доступных временных слотов
        """
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
        """
        Проверить, есть ли свободные слоты в конкретный день.
        
        Args:
            master_id: ID мастера
            check_date: Дата для проверки
            schedules: Расписания мастера на этот день недели
            service_duration_minutes: Длительность услуги в минутах
            
        Returns:
            bool: True если есть свободные слоты
        """
        # Получаем существующие записи на эту дату
        existing_appointments = await self.appointment_crud.get_by_master_and_date(
            master_id, check_date
        )
        
        # Фильтруем только активные записи (BOOKED)
        booked_appointments = [
            apt for apt in existing_appointments 
            if apt.status == AppointmentStatusEnum.BOOKED
        ]
        
        # Для каждого расписания проверяем доступность
        for schedule in schedules:
            if self._has_available_time_slots(
                schedule.time_from, 
                schedule.time_to, 
                booked_appointments, 
                service_duration_minutes
            ):
                return True
        
        return False

    def _has_available_time_slots(
        self,
        time_from: time,
        time_to: time,
        booked_appointments: List,
        service_duration_minutes: int
    ) -> bool:
        """
        Проверить наличие свободных временных слотов.
        
        Args:
            time_from: Начало рабочего времени
            time_to: Конец рабочего времени
            booked_appointments: Список забронированных записей
            service_duration_minutes: Длительность услуги
            
        Returns:
            bool: True если есть свободные слоты
        """
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
        """
        Проверить пересечение двух временных интервалов.
        
        Args:
            start1, end1: Первый интервал в минутах
            start2, end2: Второй интервал в минутах
            
        Returns:
            bool: True если интервалы пересекаются
        """
        return not (end1 <= start2 or start1 >= end2)
