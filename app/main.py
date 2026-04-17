"""
Главный файл FastAPI приложения.
"""
import asyncio
import logging
import os
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

_bot_app = None

# === MCP Tools (Здесь обновленная инициализация) ===
_mcp_tools = MCPTools(
    weather_api_key=os.getenv("WEATHER_API_KEY", ""),
    searchapi_key=os.getenv("SEARCHAPI_API_KEY", "")
)

class ToolRequest(BaseModel):
    arguments: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bot_app
    logger.info("🚀 Инициализация приложения...")
    
    try:
        init_db()
    except Exception as e:
        logger.error(f"❌ Ошибка БД: {e}")
    
    _bot_app = create_bot_app()
    await _bot_app.initialize()
    await _bot_app.start()
    
    await _bot_app.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )
    
    logger.info("✅ Бот запущен!")
    yield
    
    logger.info("🛑 Останавливаю бота...")
    try:
        if _bot_app.updater.running:
            await _bot_app.updater.stop()
        if _bot_app.running:
            await _bot_app.stop()
        await _bot_app.shutdown()
    except Exception as e:
        logger.warning(f"Ошибка остановки: {e}")

app = FastAPI(
    title="Telegram AI Agent",
    lifespan=lifespan,
)

# --- MCP API Endpoints ---
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "get_weather", "description": "Погода", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
            {"name": "get_exchange_rate", "description": "Валюта", "parameters": {"type": "object", "properties": {"currency": {"type": "string"}}, "required": ["currency"]}},
            {"name": "search_info", "description": "Поиск", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}
        ]
    }

@app.post("/tools/get_weather")
async def api_get_weather(request: ToolRequest):
    city = request.arguments.get("city", "")
    return {"result": await _mcp_tools.get_weather(city)}

@app.post("/tools/get_exchange_rate")
async def api_get_exchange_rate(request: ToolRequest):
    currency = request.arguments.get("currency", "")
    return {"result": await _mcp_tools.get_currency(currency)}

@app.post("/tools/search_info")
async def api_search_info(request: ToolRequest):
    query = request.arguments.get("query", "")
    return {"result": await _mcp_tools.search(query)}

@app.get("/")
def root():
    return {"message": "🤖 Бот работает!", "status": "ok"}
