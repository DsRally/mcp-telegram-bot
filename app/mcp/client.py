"""
MCP Client — обёртка над MCPTools.
"""
from app.mcp.tools import MCPTools
import os
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Клиент для инструментов MCP.
    Работает напрямую (без HTTP) — идеально для Railway с одним процессом.
    """
    
    def __init__(self):
        # Получаем API ключ для погоды из переменных окружения
        weather_key = os.getenv("WEATHER_API_KEY", "")
        self.tools = MCPTools(weather_api_key=weather_key)
        logger.info("🔧 MCP Client инициализирован")
    
    async def get_weather(self, city: str) -> str:
        """Получить погоду в городе"""
        return await self.tools.get_weather(city)
    
    async def get_currency(self, currency_code: str) -> str:
        """Получить курс валюты"""
        return await self.tools.get_currency(currency_code)
    
    async def search(self, query: str) -> str:
        """Поиск информации"""
        return await self.tools.search(query)
