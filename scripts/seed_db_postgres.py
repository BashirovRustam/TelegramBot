#!/usr/bin/env python3
"""
Python script to seed PostgreSQL database with initial data
"""

import asyncio
import asyncpg
import os
from datetime import time
from typing import List, Dict, Any

# Get DATABASE_URL from environment or use default
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/telegram_bot")

async def seed_database():
    """Seed the database with initial data"""
    
    # Connect to database using the correct URL for container environment
    if "postgresql+asyncpg://" in DATABASE_URL:
        conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    else:
        conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Starting database seeding...")
        
        # Insert users (masters)
        users_data = [
            (1, None, 'Никита', 'MASTER', True),
            (2, None, 'Айжан', 'MASTER', True),
            (3, None, 'Евгения', 'MASTER', True),
            (4, None, 'Карина', 'MASTER', True),
            (5, None, 'Симона', 'MASTER', True),
            (6, None, 'Эльдар', 'MASTER', True),
            (7, None, 'Инна', 'MASTER', True),
            (8, None, 'Кристина', 'MASTER', True),
            (9, None, 'Инесса', 'MASTER', True),
            (10, None, 'Айгерим', 'MASTER', True),
            (11, None, 'Акбота', 'MASTER', True)
        ]
        
        await conn.executemany(
            "INSERT INTO users (id, telegram_id, full_name, role, is_active) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING",
            users_data
        )
        print("✓ Users inserted")
        
        # Insert salons
        salons_data = [
            (1, 'Салон красоты на Навои', '​Улица Навои, 310​ Бостандыкский район, Алматы', 'Сеть салонов красоты', True, 'https://2gis.kz/almaty/geo/9430047374970929'),
            (2, 'Салон красоты на Сатпаева', 'Улица Каныша Сатпаева, 63а, Алматы', 'Сеть салонов красоты', True, 'https://2gis.kz/almaty/geo/9430047375164163'),
            (3, 'Салон красоты на Сейфулина', 'Проспект Сейфуллина, 452, Алматы', 'Сеть салонов красоты', True, 'https://2gis.kz/almaty/geo/9430047374967231')
        ]
        
        await conn.executemany(
            "INSERT INTO salons (id, name, address, description, is_active, gis_link) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (id) DO NOTHING",
            salons_data
        )
        print("✓ Salons inserted")
        
        # Insert services
        services_data = [
            (1, 1, 'Запись к стилисту', 60, 5000, True),
            (2, 1, 'Запись на ноготочки', 60, 7000, True),
            (3, 2, 'Массаж лица', 60, 5000, True),
            (4, 3, 'Массаж лица', 60, 7000, True),
            (5, 1, 'Мужская стрижка + бритье', 90, 10000, True),
            (6, 2, 'Свадебный макияж', 60, 15000, True),
            (7, 3, 'Детская стрижка', 30, 3000, True),
            (8, 2, 'Запись к стилисту', 60, 5000, True)
        ]
        
        await conn.executemany(
            "INSERT INTO services (id, salon_id, name, duration_minutes, price, is_active) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (id) DO NOTHING",
            services_data
        )
        print("✓ Services inserted")
        
        # Insert masters
        masters_data = [
            (1, 1, 1, True),
            (2, 2, 1, True),
            (3, 3, 1, True),
            (4, 4, 1, True),
            (5, 5, 2, True),
            (6, 6, 2, True),
            (7, 7, 2, True),
            (8, 8, 3, True),
            (9, 9, 3, True),
            (10, 10, 3, True),
            (11, 11, 3, True)
        ]
        
        await conn.executemany(
            "INSERT INTO masters (id, user_id, salon_id, is_active) VALUES ($1, $2, $3, $4) ON CONFLICT (id) DO NOTHING",
            masters_data
        )
        print("✓ Masters inserted")
        
        # Insert master_services relationships
        master_services_data = [
            (1, 1), (2, 2), (3, 2), (4, 1), (5, 3), (6, 8), (7, 2), (8, 1), (9, 4), (10, 2), (11, 2)
        ]
        
        await conn.executemany(
            "INSERT INTO master_services (master_id, service_id) VALUES ($1, $2) ON CONFLICT (master_id, service_id) DO NOTHING",
            master_services_data
        )
        print("✓ Master services inserted")
        
        # Insert master_schedules
        schedules_data = [
            (3, 1, 0, time(10, 0), time(20, 0)), (4, 1, 1, time(10, 0), time(20, 0)), (5, 1, 3, time(10, 0), time(20, 0)),
            (6, 1, 4, time(10, 0), time(20, 0)), (7, 1, 5, time(10, 0), time(20, 0)), (8, 1, 6, time(10, 0), time(20, 0)),
            (9, 2, 0, time(10, 0), time(20, 0)), (10, 2, 1, time(10, 0), time(20, 0)), (11, 2, 3, time(10, 0), time(20, 0)),
            (12, 2, 4, time(10, 0), time(20, 0)), (13, 2, 5, time(10, 0), time(20, 0)), (14, 2, 6, time(10, 0), time(20, 0)),
            (15, 3, 0, time(10, 0), time(20, 0)), (16, 3, 1, time(10, 0), time(20, 0)), (17, 3, 3, time(10, 0), time(20, 0)),
            (18, 3, 4, time(10, 0), time(20, 0)), (19, 3, 5, time(10, 0), time(20, 0)), (20, 3, 6, time(10, 0), time(20, 0)),
            (21, 4, 0, time(10, 0), time(20, 0)), (22, 4, 1, time(10, 0), time(20, 0)), (23, 4, 3, time(10, 0), time(20, 0)),
            (24, 4, 4, time(10, 0), time(20, 0)), (25, 4, 5, time(10, 0), time(20, 0)), (26, 4, 6, time(10, 0), time(20, 0)),
            (27, 5, 0, time(9, 0), time(19, 0)), (28, 5, 1, time(9, 0), time(19, 0)), (29, 5, 2, time(9, 0), time(19, 0)),
            (30, 5, 3, time(9, 0), time(19, 0)), (31, 5, 4, time(9, 0), time(19, 0)), (32, 5, 5, time(9, 0), time(19, 0)),
            (33, 5, 6, time(9, 0), time(19, 0)), (34, 6, 0, time(9, 0), time(19, 0)), (35, 6, 1, time(9, 0), time(19, 0)),
            (36, 6, 2, time(9, 0), time(19, 0)), (37, 6, 3, time(9, 0), time(19, 0)), (38, 6, 4, time(9, 0), time(19, 0)),
            (39, 6, 5, time(9, 0), time(19, 0)), (40, 6, 6, time(9, 0), time(19, 0)), (41, 7, 0, time(9, 0), time(19, 0)),
            (42, 7, 1, time(9, 0), time(19, 0)), (43, 7, 2, time(9, 0), time(19, 0)), (44, 7, 3, time(9, 0), time(19, 0)),
            (45, 7, 4, time(9, 0), time(19, 0)), (46, 7, 5, time(9, 0), time(19, 0)), (47, 7, 6, time(9, 0), time(19, 0)),
            (48, 8, 1, time(10, 0), time(19, 0)), (49, 8, 3, time(10, 0), time(19, 0)), (50, 8, 4, time(10, 0), time(19, 0)),
            (51, 8, 5, time(10, 0), time(19, 0)), (52, 8, 6, time(10, 0), time(19, 0)), (53, 9, 1, time(10, 0), time(19, 0)),
            (54, 9, 3, time(10, 0), time(19, 0)), (55, 9, 4, time(10, 0), time(19, 0)), (56, 9, 5, time(10, 0), time(19, 0)),
            (57, 9, 6, time(10, 0), time(19, 0)), (58, 10, 1, time(10, 0), time(19, 0)), (59, 10, 3, time(10, 0), time(19, 0)),
            (60, 10, 4, time(10, 0), time(19, 0)), (61, 10, 5, time(10, 0), time(19, 0)), (62, 10, 6, time(10, 0), time(19, 0)),
            (63, 11, 1, time(10, 0), time(19, 0)), (64, 11, 3, time(10, 0), time(19, 0)), (65, 11, 4, time(10, 0), time(19, 0)),
            (66, 11, 5, time(10, 0), time(19, 0)), (67, 11, 6, time(10, 0), time(19, 0))
        ]
        
        await conn.executemany(
            "INSERT INTO master_schedules (id, master_id, weekday, time_from, time_to) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING",
            schedules_data
        )
        print("✓ Master schedules inserted")
        
        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
