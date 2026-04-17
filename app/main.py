"""
Главный файл FastAPI приложения.
Запускает Telegram бота в фоне через lifespan.
Включает MCP endpoints прямо здесь (не нужен отдельный сервер).
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from pydantic import BaseModel
from app.config import settings
from app.telegram.bot import create_bot_app
from app.db.database import init_db
from app.mcp.tools import MCPTools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Глобальный экземпляр бота (нужен для shutdown)
_bot_app = None

# === MCP Tools (встроенные инструменты) ===
_mcp_tools = MCPTools(weather_api_key="")


class ToolRequest(BaseModel):
    arguments: dict = {}


# === Lifespan (управление жизненным циклом) ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения.
    Запускает бота при старте, останавливает при завершении.
    """
    global _bot_app
    
    logger.info("🚀 Инициализация приложения...")
    
    # Создаём таблицы БД (синхронно, т.к. SQLAlchemy синхронный)
    try:
        init_db()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка инициализации БД: {e}")
        # Продолжаем работу без БД — бот ответит, но не сохранит историю
    
    logger.info("🤖 Запускаю Telegram бота...")
    _bot_app = create_bot_app()
    
    await _bot_app.initialize()
    await _bot_app.start()
    
    # drop_pending_updates=True — КРИТИЧНО для Railway
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


# === Создаём FastAPI приложение (ДО всех декораторов!) ===
app = FastAPI(
    title="Telegram AI Agent",
    description="AI Telegram бот с инструментами: погода, валюты, поиск. Работает на Railway.",
    version="2.0.0",
    lifespan=lifespan,
)


# === MCP API Endpoints (после создания app!) ===
@app.get("/health")
async def health():
    return {"status": "ok", "service": "telegram-ai-agent"}


@app.get("/tools")
async def list_tools():
    """Список доступных инструментов MCP"""
    return {
        "tools": [
            {
                "name": "get_weather",
                "description": "Получить текущую погоду в городе",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "Название города"}
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "get_exchange_rate",
                "description": "Получить курс валюты к USD",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "currency": {"type": "string", "description": "Код валюты, например USD, EUR, RUB"}
                    },
                    "required": ["currency"]
                }
            },
            {
                "name": "search_info",
                "description": "Найти информацию по запросу",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Поисковый запрос"}
                    },
                    "required": ["query"]
                }
            }
        ]
    }


@app.post("/tools/get_weather")
async def api_get_weather(request: ToolRequest):
    """API endpoint для погоды"""
    city = request.arguments.get("city", "")
    result = await _mcp_tools.get_weather(city)
    return {"result": result}


@app.post("/tools/get_exchange_rate")
async def api_get_exchange_rate(request: ToolRequest):
    """API endpoint для курса валют"""
    currency = request.arguments.get("currency", "")
    result = await _mcp_tools.get_currency(currency)
    return {"result": result}


@app.post("/tools/search_info")
async def api_search_info(request: ToolRequest):
    """API endpoint для поиска"""
    query = request.arguments.get("query", "")
    result = await _mcp_tools.search(query)
    return {"result": result}


# === Основные endpoint'ы ===
@app.get("/")
def root():
    return {
        "message": "🤖 Telegram AI Agent работает!",
        "docs": "/docs",
        "health": "/health",
        "tools": "/tools",
        "status": "ok",
    }


@app.get("/api/health")
def health_check():
    """Детальная проверка здоровья"""
    bot_running = _bot_app is not None and _bot_app.running
    return {
        "status": "alive",
        "service": "telegram-ai-agent",
        "bot_token_loaded": bool(settings.telegram_bot_token),
        "bot_running": bot_running,
        "database_url_configured": bool(settings.database_url),
    }
