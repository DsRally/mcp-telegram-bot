from fastapi import FastAPI
from config import settings
from app.core.memory import DatabaseMemory
from app.telegram.bot import create_bot_app
import asyncio
from contextlib import asynccontextmanager

# Создаём приложение FastAPI (для health-check)
app = FastAPI(title="Telegram MCP Agent")
memory = DatabaseMemory()

@app.get("/health")
def health_check():
    return {
        "status": "alive",
        "service": "telegram-mcp-agent",
        "bot_token_loaded": settings.telegram_bot_token != ""
    }

@app.get("/")
def root():
    return {"message": "Telegram MCP Agent", "docs": "/docs"}

# === Telegram Bot ===
bot_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте
    global bot_app
    bot_app = create_bot_app()
    
    # Запускаем бота в фоне
    await bot_app.initialize()
    await bot_app.start()
    
    # polling — бот сам спрашивает Telegram о новых сообщениях
    asyncio.create_task(bot_app.updater.start_polling())
    
    print("🤖 Бот запущен! Напиши ему в Telegram.")
    yield
    
    # При остановке
    await bot_app.stop()

# Перезапускаем с правильным lifespan
app.router.lifespan_context = lifespan
