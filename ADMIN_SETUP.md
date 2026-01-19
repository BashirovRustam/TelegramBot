# SQLAdmin Setup для Beauty Bot

## Структура файлов

```
telegram_bot_app/admin/
├── __init__.py
├── admin.py                    # Основной файл настройки админки
└── models_admin/
    ├── __init__.py
    ├── user_admin.py           # UserAdmin
    ├── salon_admin.py          # SalonAdmin  
    ├── service_admin.py        # ServiceAdmin
    ├── master_admin.py         # MasterAdmin
    ├── master_service_admin.py # MasterServiceAdmin
    ├── master_schedule_admin.py# MasterScheduleAdmin
    └── appointment_admin.py   # AppointmentAdmin
```

## Подключение

Админка уже подключена в `main.py`:

```python
from telegram_bot_app.admin.admin import setup_admin
from telegram_bot_app.db.base import engine

app = FastAPI()
setup_admin(app, engine)
```

## Доступ к админке

После запуска FastAPI приложения админка будет доступна по адресу:
- **URL**: `http://localhost:8000/admin`
- **Title**: "Beauty Admin"

## Особенности реализации

### 1. Человекочитаемые поля
- Все `id` поля скрыты из списков
- ForeignKey поля показываются через `__str__` метод моделей
- Many-to-many связи выводятся через свойства (например, `services_list` у Master)

### 2. Русские названия колонок
- Все колонки переименованы через `column_labels`
- Статусы и дни недели локализованы

### 3. Форматирование дат и времени
- Даты: `дд.мм.гггг`
- Время: `чч:мм`
- Статусы записей на русском языке

### 4. Оптимизация запросов
- Используется `lazy="joined"` для всех связей
- Предотвращает `DetachedInstanceError`

### 5. Поиск и сортировка
- Настроены `column_searchable_list` для важных полей
- Настроены `column_sortable_list` для удобной навигации

## Модели и их Admin классы

| Модель | Admin класс | Основные поля |
|--------|-------------|---------------|
| User | UserAdmin | telegram_id, full_name, role, is_active |
| Salon | SalonAdmin | name, address, description, is_active |
| Service | ServiceAdmin | name, salon, duration_minutes, price |
| Master | MasterAdmin | user, salon, services_list, is_active |
| MasterService | MasterServiceAdmin | master, service |
| MasterSchedule | MasterScheduleAdmin | master, weekday, time_from, time_to |
| Appointment | AppointmentAdmin | client, salon, master, service, date, time_start, status |

## Использование

1. Запустите приложение:
```bash
uvicorn telegram_bot_app.main:app --reload
```

2. Откройте в браузере:
```
http://localhost:8000/admin
```

3. Управляйте данными через веб-интерфейс SQLAdmin
