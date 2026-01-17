#!/usr/bin/env python3
"""
Script to seed PostgreSQL database with sample data for Telegram Bot
Creates 20+ records for each model with PostgreSQL optimizations
"""
import asyncio
import random
from datetime import datetime, date, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from telegram_bot_app.db.base import engine, Base, async_session
from telegram_bot_app.models import (
    User, UserRoleEnum, Salon, Service, Master, 
    MasterService, MasterSchedule, Appointment, AppointmentStatusEnum
)

# Sample data
SALON_NAMES = [
    "Элегантность", "Грация", "Стиль Плюс", "Бьюти-Лэнд", "Арт-Салон",
    "Премьера", "Люкс Стиль", "Визаж Студия", "Перфект Бьюти", "Шарм",
    "Эстетика", "Гламур", "Фэшн Хаус", "Бьюти Эмпайр", "Салон Элит",
    "Золотое Руно", "Алмаз", "Платинум", "Роял Бьюти", "Империя Стиля"
]

SALON_ADDRESSES = [
    "ул. Тверская, 1", "ул. Арбат, 15", "пр. Ленина, 42", "ул. Садовая, 8",
    "пр. Невский, 25", "ул. Пушкинская, 12", "ул. Горького, 33", "пр. Мира, 77",
    "ул. Свердлова, 19", "ул. Куйбышева, 44", "пр. Победы, 88", "ул. Карла Маркса, 66",
    "ул. Маяковского, 23", "пр. Комсомольский, 55", "ул. Дзержинского, 31",
    "ул. Володарского, 17", "пр. Октябрьский, 99", "ул. Интернациональная, 41",
    "пр. Строителей, 73", "ул. Молодежная, 29"
]

FIRST_NAMES = [
    "Анна", "Мария", "Елена", "Ольга", "Татьяна", "Наталья", "Ирина", "Светлана",
    "Екатерина", "Александра", "Юлия", "Виктория", "Дарья", "Ксения", "Полина",
    "Анастасия", "Вероника", "Маргарита", "Злата", "Алина"
]

LAST_NAMES = [
    "Иванова", "Петрова", "Смирнова", "Кузнецова", "Попова", "Васильева", "Новикова",
    "Морозова", "Волкова", "Алексеева", "Лебедева", "Соколова", "Козлова", "Зайцева",
    "Соловьева", "Ковалева", "Белова", "Егорова", "Павлова", "Степанова"
]

SERVICE_NAMES = [
    "Стрижка женская", "Стрижка мужская", "Окрашивание волос", "Мелирование",
    "Колорирование", "Кератиновое выпрямление", "Ламинирование волос",
    "Укладка", "Прическа", "Чистка кожи лица", "Пилинг", "Массаж лица",
    "Маникюр классический", "Маникюр аппаратный", "Педикюр", "Наращивание ногтей",
    "Покрытие гель-лак", "Массаж спины", "Массаж общий", "Обертывание",
    "Солярий", "Эпиляция", "Брови", "Ресницы", "Макияж"
]

async def reset_sequences(session: AsyncSession):
    """Reset PostgreSQL sequences after bulk insert"""
    await session.execute(text("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE(MAX(id), 1), true) FROM users"))
    await session.execute(text("SELECT setval(pg_get_serial_sequence('salons', 'id'), COALESCE(MAX(id), 1), true) FROM salons"))
    await session.execute(text("SELECT setval(pg_get_serial_sequence('services', 'id'), COALESCE(MAX(id), 1), true) FROM services"))
    await session.execute(text("SELECT setval(pg_get_serial_sequence('masters', 'id'), COALESCE(MAX(id), 1), true) FROM masters"))
    await session.execute(text("SELECT setval(pg_get_serial_sequence('appointments', 'id'), COALESCE(MAX(id), 1), true) FROM appointments"))
    await session.commit()

async def create_salons(session: AsyncSession) -> list[Salon]:
    """Create 20 salons"""
    salons = []
    for i in range(20):
        salon = Salon(
            name=SALON_NAMES[i],
            address=SALON_ADDRESSES[i],
            description=f"Современный салон красоты с высококлассными мастерами и уютной атмосферой. Салон {SALON_NAMES[i]} предлагает полный спектр услуг для вашей красоты.",
            is_active=True
        )
        salons.append(salon)
        session.add(salon)
    
    await session.commit()
    # Refresh to get IDs from PostgreSQL
    for salon in salons:
        await session.refresh(salon)
    
    print(f"✅ Created {len(salons)} salons")
    return salons

async def create_users(session: AsyncSession) -> list[User]:
    """Create 30 users (20 clients, 8 masters, 2 admins)"""
    users = []
    
    # Create clients
    for i in range(20):
        user = User(
            telegram_id=1000000 + i,
            full_name=f"{FIRST_NAMES[i]} {LAST_NAMES[i]}",
            role=UserRoleEnum.CLIENT,
            is_active=True
        )
        users.append(user)
        session.add(user)
    
    # Create masters
    for i in range(8):
        user = User(
            telegram_id=2000000 + i,
            full_name=f"{FIRST_NAMES[i]} {LAST_NAMES[i % len(LAST_NAMES)]}",
            role=UserRoleEnum.MASTER,
            is_active=True
        )
        users.append(user)
        session.add(user)
    
    # Create admins
    for i in range(2):
        user = User(
            telegram_id=3000000 + i,
            full_name=f"Admin {i+1}",
            role=UserRoleEnum.ADMIN,
            is_active=True
        )
        users.append(user)
        session.add(user)
    
    await session.commit()
    # Refresh to get IDs from PostgreSQL
    for user in users:
        await session.refresh(user)
    
    print(f"✅ Created {len(users)} users (20 clients, 8 masters, 2 admins)")
    return users

async def create_services(session: AsyncSession, salons: list[Salon]) -> list[Service]:
    """Create 100+ services across all salons"""
    services = []
    
    for salon in salons:
        # Each salon gets 5-8 services
        num_services = random.randint(5, 8)
        selected_services = random.sample(SERVICE_NAMES, num_services)
        
        for service_name in selected_services:
            service = Service(
                salon_id=salon.id,
                name=service_name,
                duration_minutes=random.choice([30, 45, 60, 90, 120, 150, 180]),
                price=random.uniform(500.0, 5000.0),
                is_active=True
            )
            services.append(service)
            session.add(service)
    
    await session.commit()
    # Refresh to get IDs from PostgreSQL
    for service in services:
        await session.refresh(service)
    
    print(f"✅ Created {len(services)} services")
    return services

async def create_masters(session: AsyncSession, users: list[User], salons: list[Salon]) -> list[Master]:
    """Create 8 masters"""
    masters = []
    master_users = [u for u in users if u.role == UserRoleEnum.MASTER]
    
    for i, user in enumerate(master_users):
        # Assign master to random salon
        salon = random.choice(salons)
        master = Master(
            user_id=user.id,
            salon_id=salon.id,
            is_active=True
        )
        masters.append(master)
        session.add(master)
    
    await session.commit()
    # Refresh to get IDs from PostgreSQL
    for master in masters:
        await session.refresh(master)
    
    print(f"✅ Created {len(masters)} masters")
    return masters

async def create_master_services(session: AsyncSession, masters: list[Master], services: list[Service]) -> list[MasterService]:
    """Create master-service relationships"""
    master_services = []
    
    for master in masters:
        # Each master provides 3-6 services from their salon
        salon_services = [s for s in services if s.salon_id == master.salon_id]
        num_services = min(random.randint(3, 6), len(salon_services))
        selected_services = random.sample(salon_services, num_services)
        
        for service in selected_services:
            master_service = MasterService(
                master_id=master.id,
                service_id=service.id
            )
            master_services.append(master_service)
            session.add(master_service)
    
    await session.commit()
    print(f"✅ Created {len(master_services)} master-service relationships")
    return master_services

async def create_master_schedules(session: AsyncSession, masters: list[Master]) -> list[MasterSchedule]:
    """Create work schedules for masters"""
    schedules = []
    
    for master in masters:
        # Each master works 3-5 days a week
        work_days = random.sample(range(7), random.randint(3, 5))
        
        for weekday in work_days:
            schedule = MasterSchedule(
                master_id=master.id,
                weekday=weekday,
                time_from=time(9, 0),  # 9:00 AM
                time_to=time(19, 0)    # 7:00 PM
            )
            schedules.append(schedule)
            session.add(schedule)
    
    await session.commit()
    print(f"✅ Created {len(schedules)} master schedules")
    return schedules

async def create_appointments(session: AsyncSession, users: list[User], salons: list[Salon], 
                           masters: list[Master], services: list[Service]) -> list[Appointment]:
    """Create 50+ appointments"""
    appointments = []
    client_users = [u for u in users if u.role == UserRoleEnum.CLIENT]
    
    # Generate appointments for the past 30 days and next 30 days
    base_date = date.today()
    
    for i in range(50):
        # Random date within ±30 days
        days_offset = random.randint(-30, 30)
        appointment_date = base_date + timedelta(days=days_offset)
        
        # Random master and their services
        master = random.choice(masters)
        result = await session.execute(
            select(MasterService.service_id).filter(MasterService.master_id == master.id)
        )
        master_service_ids = result.all()
        
        if not master_service_ids:
            continue
            
        service_id = random.choice(master_service_ids)[0]
        service = next(s for s in services if s.id == service_id)
        
        # Random time during working hours
        start_hour = random.randint(9, 17)
        start_minute = random.choice([0, 15, 30, 45])
        start_time = time(start_hour, start_minute)
        
        # Calculate end time based on service duration
        end_datetime = datetime.combine(appointment_date, start_time) + timedelta(minutes=service.duration_minutes)
        end_time = end_datetime.time()
        
        # Random status
        if appointment_date < base_date:
            # Past appointments are either completed or cancelled
            status = random.choice([AppointmentStatusEnum.COMPLETED, AppointmentStatusEnum.CANCELLED])
        else:
            # Future appointments are booked
            status = AppointmentStatusEnum.BOOKED
        
        appointment = Appointment(
            client_id=random.choice(client_users).id,
            salon_id=master.salon_id,
            master_id=master.id,
            service_id=service_id,
            date=appointment_date,
            time_start=start_time,
            time_end=end_time,
            status=status
        )
        appointments.append(appointment)
        session.add(appointment)
    
    await session.commit()
    # Refresh to get IDs from PostgreSQL
    for appointment in appointments:
        await session.refresh(appointment)
    
    print(f"✅ Created {len(appointments)} appointments")
    return appointments

async def seed_database():
    """Main function to seed the PostgreSQL database"""
    print("🌱 Starting PostgreSQL database seeding...")
    
    async with engine.begin() as conn:
        # Drop all tables and recreate them
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        print("📋 Database schema recreated")
    
    async with async_session() as session:
        # Create data in correct order (respecting foreign keys)
        salons = await create_salons(session)
        users = await create_users(session)
        services = await create_services(session, salons)
        masters = await create_masters(session, users, salons)
        master_services = await create_master_services(session, masters, services)
        schedules = await create_master_schedules(session, masters)
        appointments = await create_appointments(session, users, salons, masters, services)
        
        # Reset PostgreSQL sequences
        await reset_sequences(session)
        
        print("\n🎉 PostgreSQL database seeding completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Salons: {len(salons)}")
        print(f"   - Users: {len(users)}")
        print(f"   - Services: {len(services)}")
        print(f"   - Masters: {len(masters)}")
        print(f"   - Master-Service relationships: {len(master_services)}")
        print(f"   - Master Schedules: {len(schedules)}")
        print(f"   - Appointments: {len(appointments)}")

if __name__ == "__main__":
    asyncio.run(seed_database())
