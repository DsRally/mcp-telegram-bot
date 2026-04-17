import httpx
from app.config import settings

class MCPClient:
    """Клиент для общения с MCP-серверами"""
    
    def __init__(self):
        self.servers = {
            "weather": settings.weather_service_url,
            "currency": settings.currency_service_url,
            "search": settings.search_service_url,
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
                return response.json().get("message", "Не удалось получить данные о погоде")
        except Exception as e:
            return f"Ошибка сервиса погоды: {str(e)}"
    
    async def get_currency(self, currency_code: str) -> str:
        """Спрашивает курс валюты"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.servers['currency']}/get_rate",
                    json={"currency": currency_code},
                    timeout=10.0
                )
                return response.json().get("message", "Не удалось получить курс")
        except Exception as e:
            return f"Ошибка сервиса валют: {str(e)}"
    
    async def search(self, query: str) -> str:
        """Поиск в интернете"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.servers['search']}/search",
                    json={"query": query},
                    timeout=10.0
                )
                data = response.json()
                results = data.get("results", [])
                return results[0] if results else "Ничего не найдено"
        except Exception as e:
            return f"Ошибка поиска: {str(e)}"
