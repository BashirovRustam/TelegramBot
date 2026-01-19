from fastapi import FastAPI
from telegram_bot_app.admin.admin import setup_admin
from telegram_bot_app.db.base import engine

app = FastAPI()

setup_admin(app, engine)

@app.get("/health")
async def health_check():
    return {"status": "ok"}