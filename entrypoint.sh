##!/bin/sh
#set -e
#
#echo "Waiting for database..."
#while ! pg_isready -h postgres -p 5432 -U postgres; do
#  echo "PostgreSQL is unavailable - sleeping"
#  sleep 1
#done
#
#echo "Starting Telegram bot..."
#exec python -m telegram_bot_app.main

#!/bin/sh
set -e

# Если переменная DB_HOST не задана, попробуем использовать "postgres" как запасной вариант
HOST="${DB_HOST:-postgres}"
USER="${DB_USER:-postgres}"

echo "Waiting for database at $HOST..."

# Проверяем доступность базы по актуальному адресу
until pg_isready -h "$HOST" -p 5432 -U "$USER"; do
  echo "PostgreSQL at $HOST is unavailable - sleeping"
  sleep 1
done

echo "✅ Database is up! Starting Telegram bot..."
exec python -m telegram_bot_app.main