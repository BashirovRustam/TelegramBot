FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание entrypoint скрипта
RUN echo '#!/bin/sh\n\
set -e\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Starting Telegram bot..."\n\
exec python -m telegram_bot_app.main' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Запуск через entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]