"""
MCP Client — теперь просто обёртка над MCPTools.
Нет необходимости в HTTP-запросах к localhost!
"""
from app.mcp.tools import MCPTools
from app.config import settings
import os


class MCPClient:
    """
    Клиент для инструментов MCP.
    Работает напрямую (без HTTP) — идеально для Railway с одним процессом.
    """
    
    def __init__(self):
        # Получаем API ключ для погоды из переменных окружения
        weather_key = os.getenv("WEATHER_API_KEY", "")
        self.tools = MCPTools(weather_api_key=weather_key)
    
    async def get_weather(self, city: str) -> str:
        """Получить погоду в городе"""
        return await self.tools.get_weather(city)
    
    async def get_currency(self, currency_code: str) -> str:
        """Получить курс валюты"""
        return await self.tools.get_currency(currency_code)
    
    async def search(self, query: str) -> str:
        """Поиск информации"""
        return await self.tools.search(query)
