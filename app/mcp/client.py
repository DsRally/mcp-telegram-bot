import httpx
from app.config import settings

class MCPClient:
    """Клиент для общения с MCP-серверами"""
    
    def __init__(self):
        # Все сервисы на одном порту, разные пути
        base_url = "http://localhost:8001"  # Один сервер для всех
        self.servers = {
            "weather": f"{base_url}/weather",
            "currency": f"{base_url}/currency",
            "search": f"{base_url}/search",
        }
    
    async def get_weather(self, city: str) -> str:
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
