from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="FastAPI Telegram Bot Test", version="1.0")

# Health-check эндпоинт
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Проверка работоспособности API.
    """
    return JSONResponse(content={"status": "ok"})
