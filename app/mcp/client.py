import httpx
from typing import Dict, Any, List
from app.config import settings

class MCPClient:
    """Клиент для общения с MCP-серверами"""
    
    def __init__(self):
        # ВАЖНО: В Railway localhost не работает. 
        # Используй переменные из settings или замени на внутренние адреса Railway (напр. http://weather:8001)
        self.servers = {
            "weather": getattr(settings, "weather_url", "http://localhost:8001"),
            "currency": getattr(settings, "currency_url", "http://localhost:8002"),
            "search": getattr(settings, "search_url", "http://localhost:8003"),
        }
    
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
            return f"Ошибка погоды (проверьте URL): {str(e)}"
    
    async def get_currency(self, currency_code: str) -> str:
        """Спрашивает курс валюты. Аргумент совпадает с agent.py"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.servers['currency']}/get_rate",
                    # В API передаем ключ "currency", как ожидает твой сервер
                    json={"currency": currency_code}, 
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
                    return f"Результат поиска: {results[0]}"
                return "Ничего не найдено"
        except Exception as e:
            return f"Ошибка поиска: {str(e)}"
