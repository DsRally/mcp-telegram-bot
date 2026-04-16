import httpx
from typing import Dict, Any, List


class MCPClient:
    """Клиент для общения с MCP-серверами"""
    
    def __init__(self):
        self.servers = {
            "weather": "http://localhost:8001",
            "currency": "http://localhost:8002",
            "search": "http://localhost:8003",
        }
    
    async def check_health(self, server_name: str) -> bool:
        """Проверяет, жив ли сервер"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.servers[server_name]}/health", timeout=5.0)
                return response.status_code == 200
        except:
            return False
    
    async def get_weather(self, city: str) -> str:
        """Спрашивает погоду у сервера"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.servers['weather']}/get_weather",
                    json={"city": city},
                    timeout=10.0
                )
                data = response.json()
                return data.get("message", "Не удалось узнать погоду")
        except Exception as e:
            return f"Ошибка погоды: {str(e)}"
    
    async def get_currency(self, currency: str) -> str:
        """Спрашивает курс валюты"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.servers['currency']}/get_rate",
                    json={"currency": currency},
                    timeout=10.0
                )
                data = response.json()
                return data.get("message", "Не удалось узнать курс")
        except Exception as e:
            return f"Ошибка курса: {str(e)}"
    
    async def search(self, query: str) -> str:
        """Ищет в интернете"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.servers['search']}/search",
                    json={"query": query},
                    timeout=10.0
                )
                data = response.json()
                results = data.get("results", [])
                if results:
                    return f"Нашёл: {results[0]}"
                return "Ничего не найдено"
        except Exception as e:
            return f"Ошибка поиска: {str(e)}"
    
    def get_tools_description(self) -> str:
        """Описание инструментов для агента"""
        return """
        У тебя есть доступ к инструментам:
        1. get_weather(city) - узнать погоду в городе
        2. get_currency(currency) - узнать курс валюты (USD, EUR, и т.д.)
        3. search(query) - поискать информацию в интернете
        """