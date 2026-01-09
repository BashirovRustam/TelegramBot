from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.router import api_router

app = FastAPI(title="FastAPI Telegram Bot", version="1.0")

# Health-check эндпоинт
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Проверка работоспособности API.
    """
    return JSONResponse(content={"status": "ok"})

# Подключаем API роутеры
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
