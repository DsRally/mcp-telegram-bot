"""
Встроенные инструменты MCP — работают напрямую через HTTP API.
"""
import httpx
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class MCPTools:
    """Встроенные инструменты для агента — погода, валюты, поиск"""
    
    def __init__(self, weather_api_key: Optional[str] = None, searchapi_key: Optional[str] = None):
        # Читаем ключи из переменных окружения или параметров
        self.weather_api_key = weather_api_key or os.getenv("WEATHER_API_KEY", "")
        self.searchapi_key = searchapi_key or os.getenv("SEARCHAPI_API_KEY", "")
        
        if self.weather_api_key:
            logger.info("🌤 Weather API ключ загружен")
        
        if self.searchapi_key:
            logger.info("🔍 SearchAPI ключ загружен")
        else:
            logger.warning("⚠️ SearchAPI ключ не найден — поиск будет ограничен Wikipedia")
    
    async def get_weather(self, city: str) -> str:
        """Получить погоду в городе через OpenWeatherMap API"""
        if not city:
            return "❌ Не указан город"
        
        if not self.weather_api_key:
            logger.warning(f"Нет WEATHER_API_KEY для города {city}")
            return f"🌤 Погода в {city}: ~15°C, облачно. (Добавьте WEATHER_API_KEY для точных данных)"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "http://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": city,
                        "appid": self.weather_api_key,
                        "units": "metric",
                        "lang": "ru"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    temp = data["main"]["temp"]
                    feels_like = data["main"]["feels_like"]
                    description = data["weather"][0]["description"]
                    humidity = data["main"]["humidity"]
                    wind = data["wind"]["speed"]
                    city_name = data.get("name", city)
                    
                    logger.info(f"✅ Погода получена для {city_name}: {temp}°C")
                    
                    return (
                        f"🌤 Погода в {city_name}:\n"
                        f"🌡 Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                        f"☁️ {description.capitalize()}\n"
                        f"💧 Влажность: {humidity}%\n"
                        f"💨 Ветер: {wind} м/с"
                    )
                elif response.status_code == 401:
                    return "❌ Неверный API ключ погоды. Проверьте WEATHER_API_KEY."
                elif response.status_code == 404:
                    return f"❌ Город '{city}' не найден"
                else:
                    return f"⚠️ Ошибка сервиса погоды (код {response.status_code})"
                    
        except Exception as e:
            logger.error(f"Ошибка погоды: {e}")
            return f"⚠️ Ошибка получения погоды: {str(e)}"
    
    async def get_currency(self, currency_code: str) -> str:
        """Получить курс валюты к USD"""
        if not currency_code:
            return "❌ Не указана валюта"
        
        currency = currency_code.upper().strip()
        currency_map = {
            "ДОЛЛАР": "USD", "ЕВРО": "EUR", "РУБЛЬ": "RUB", 
            "ГРИВНА": "UAH", "ФУНТ": "GBP", "ЙЕНА": "JPY"
        }
        currency = currency_map.get(currency, currency)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://api.exchangerate-api.com/v4/latest/USD")
                
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get("rates", {})
                    
                    if currency in rates:
                        rate = rates[currency]
                        rub_rate = rates.get("RUB", 0)
                        usd_to_rub = 1 / rub_rate if rub_rate else 0
                        target_to_rub = rate * usd_to_rub if usd_to_rub else 0
                        
                        result = f"💱 Курс {currency}:\n"
                        result += f"• 1 USD = {rate:.2f} {currency}\n"
                        if target_to_rub > 0:
                            result += f"• 1 {currency} = {target_to_rub:.2f} RUB"
                        return result
                    return f"❌ Валюта '{currency}' не найдена"
                return "❌ Не удалось получить курсы валют"
        except Exception as e:
            logger.error(f"Ошибка валют: {e}")
            return f"⚠️ Ошибка курса: {str(e)}"
    
    async def search(self, query: str) -> str:
        """Поиск через SearchAPI.io с откатом на Wikipedia"""
        if not query:
            return "❌ Не указан запрос"

        # 1. Попытка поиска через SearchAPI.io (Google Engine)
        if self.searchapi_key:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(
                        "https://www.searchapi.io/api/v1/search",
                        params={
                            "engine": "google",
                            "q": query,
                            "api_key": self.searchapi_key,
                            "num": 3
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("organic_results", [])
                        if results:
                            out = [f"🔍 Результаты поиска: {query}\n"]
                            for res in results[:3]:
                                out.append(f"🔵 {res.get('title')}\n🔗 {res.get('link')}\n📝 {res.get('snippet')}\n")
                            return "\n".join(out)
            except Exception as e:
                logger.error(f"Ошибка SearchAPI: {e}")

        # 2. Откат на Wikipedia, если SearchAPI недоступен
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://ru.wikipedia.org/api/rest_v1/page/summary/{query}",
                    headers={"User-Agent": "TelegramBot/1.0"}
                )
                if response.status_code == 200:
                    data = response.json()
                    extract = data.get("extract", "")
                    if extract:
                        return f"📖 Wikipedia: {data.get('title')}\n\n{extract[:800]}..."
        except Exception as e:
            logger.error(f"Ошибка Wikipedia: {e}")

        return f"🔍 По запросу '{query}' ничего не найдено."
