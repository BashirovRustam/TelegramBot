# Telegram Bot Task Manager

FastAPI + Aiogram проект для управления задачами через Telegram.

## Структура проекта

```
project_root/
├── app/                      # FastAPI приложение
│   ├── main.py              # Точка входа
│   ├── core/
│   │   └── config.py        # Настройки
│   ├── db/
│   │   ├── base.py          # Base для SQLAlchemy
│   │   ├── models.py        # Модели БД
│   │   ├── session.py       # Async сессия
│   │   └── alembic/         # Миграции
│   ├── schemas/             # Pydantic схемы
│   ├── services/            # Бизнес-логика
│   └── api/                 # API эндпоинты
├── bot/                     # Telegram бот
│   ├── bot.py              # Запуск бота
│   ├── handlers/           # Обработчики команд
│   └── keyboards/          # Клавиатуры
├── scripts/                # Вспомогательные скрипты
└── requirements.txt        # Зависимости
```

## Установка и запуск

1. Установить зависимости:
```bash
pip install -r requirements.txt
```

2. Создать `.env` файл:
```bash
cp .env.example .env
```
Заполнить `BOT_TOKEN` и `DATABASE_URL`.

3. Настроить базу данных PostgreSQL и выполнить миграции.

4. Создать тестовые данные:
```bash
python scripts/create_db.py
```

5. Запустить API:
```bash
python -m app.main
```

6. Запустить бота:
```bash
python bot/bot.py
```

## API эндпоинты

- `GET /health` - Проверка работоспособности
- `GET /api/v1/users/` - Список пользователей
- `GET /api/v1/tasks/` - Список задач
- И другие...

## Команды бота

- `/start` - Главное меню
- `/tasks` - Список задач
- `/create` - Создать задачу
- `/admin` - Панель администратора
