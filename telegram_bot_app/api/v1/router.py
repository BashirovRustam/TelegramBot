from fastapi import APIRouter

from telegram_bot_app.api.v1.endpoints import users, tasks

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
