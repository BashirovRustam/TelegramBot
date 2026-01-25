#!/bin/sh
set -e

echo "Waiting for database..."
while ! pg_isready -h postgres -p 5432 -U postgres; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "Starting Telegram bot..."
exec python -m telegram_bot_app.main
