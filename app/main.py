"""
Главный файл FastAPI приложения.
Запускает Telegram бота в фоне через lifespan.
Исправления:
- drop_pending_updates=True — устраняет Conflict ошибку при перезапуске
- Правильная регистрация lifespan через FastAPI(lifespan=...)
- Корректный shutdown бота
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.telegram.bot import create_bot_app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
# Глобальный экземпляр бота (нужен для shutdown)
_bot_app = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения.
    Запускает бота при старте, останавливает при завершении.
    """
    global _bot_app
    logger.info("🚀 Запускаю Telegram бота...")
    _bot_app = create_bot_app()
    await _bot_app.initialize()
    await _bot_app.start()
    # drop_pending_updates=True — КРИТИЧНО для Railway:
    # убирает накопившиеся обновления и устраняет Conflict ошибку
    # когда старый инстанс ещё не успел остановиться
    await _bot_app.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )
    logger.info("✅ Бот запущен и слушает сообщения!")
    yield  # Приложение работает
    # === Корректная остановка ===
    logger.info("🛑 Останавливаю бота...")
    try:
        if _bot_app.updater.running:
            await _bot_app.updater.stop()
        if _bot_app.running:
            await _bot_app.stop()
        await _bot_app.shutdown()
    except Exception as e:
        logger.warning(f"Ошибка при остановке бота: {e}")
    logger.info("👋 Бот остановлен.")
# Создаём приложение с правильным lifespan
app = FastAPI(
    title="Telegram MCP Agent",
    description="AI Telegram бот с инструментами: погода, валюты, поиск.",
    version="1.0.0",
    lifespan=lifespan,  # Правильный способ (не app.router.lifespan_context)
)
@app.get("/")
def root():
    return {
        "message": "Telegram MCP Agent работает",
        "docs": "/docs",
        "status": "ok",
    }
@app.get("/health")
def health_check():
    bot_running = _bot_app is not None and _bot_app.running
    return {
        "status": "alive",
        "service": "telegram-mcp-agent",
        "bot_token_loaded": bool(settings.telegram_bot_token),
        "bot_running": bot_running,
    }
