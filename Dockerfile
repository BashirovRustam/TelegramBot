#FROM python:3.12-slim
#
#WORKDIR /app
#
## Установка зависимостей системы
#RUN apt-get update && apt-get install -y \
#    gcc \
#    postgresql-client \
#    && rm -rf /var/lib/apt/lists/*
#
## Копирование requirements
#COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
#
## Копирование приложения
#COPY . .
#
## Копирование и настройка entrypoint скрипта
#COPY entrypoint.sh /app/entrypoint.sh
#RUN chmod +x /app/entrypoint.sh
#
## Запуск через entrypoint
#ENTRYPOINT ["/app/entrypoint.sh"]


FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей системы
# Мы оставляем postgresql-client на случай, если вам нужно будет
# делать дампы или проверять БД вручную, но это не обязательно
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# На Render лучше использовать CMD, так как его проще переопределить в панели управления
# Убедитесь, что путь к модулю (telegram_bot_app.main) верный
CMD ["python", "-m", "telegram_bot_app.main"]