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
    
    def __init__(self, weather_api_key: Optional[str] = None):
        # Читаем API ключ из переменной окружения или переданного параметра
        self.weather_api_key = weather_api_key or os.getenv("WEATHER_API_KEY", "")
        if self.weather_api_key:
            logger.info("🌤 Weather API ключ загружен")
        else:
            logger.warning("⚠️ Weather API ключ не найден — погода будет примерной")
    
    async def get_weather(self, city: str) -> str:
        """Получить погоду в городе через OpenWeatherMap API"""
        if not city:
            return "❌ Не указан город"
        
        # Если нет API ключа — возвращаем fallback
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
                    logger.error("❌ Неверный Weather API ключ")
                    return "❌ Неверный API ключ погоды. Проверьте WEATHER_API_KEY."
                elif response.status_code == 404:
                    return f"❌ Город '{city}' не найден"
                else:
                    logger.error(f"Ошибка погоды: {response.status_code}")
                    return f"⚠️ Ошибка сервиса погоды (код {response.status_code})"
                    
        except Exception as e:
            logger.error(f"Ошибка погоды: {e}")
            return f"⚠️ Ошибка получения погоды: {str(e)}"
    
    async def get_currency(self, currency_code: str) -> str:
        """Получить курс валюты к USD"""
        if not currency_code:
            return "❌ Не указана валюта"
        
        currency = currency_code.upper().strip()
        
        # Маппинг популярных валют
        currency_map = {
            "ДОЛЛАР": "USD",
            "ЕВРО": "EUR",
            "РУБЛЬ": "RUB",
            "ГРИВНА": "UAH",
            "ФУНТ": "GBP",
            "ЙЕНА": "JPY",
            "ФРАНК": "CHF",
            "ЮАНЬ": "CNY",
        }
        currency = currency_map.get(currency, currency)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Бесплатный API курсов валют
                response = await client.get(
                    "https://api.exchangerate-api.com/v4/latest/USD"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get("rates", {})
                    
                    if currency == "USD":
                        return "💵 1 USD = 1 USD"
                    
                    if currency in rates:
                        rate = rates[currency]
                        rub_rate = rates.get("RUB", 0)
                        usd_to_rub = 1 / rub_rate if rub_rate else 0
                        target_to_rub = rate * usd_to_rub if usd_to_rub else 0
                        
                        result = f"💱 Курс {currency}:\n"
                        result += f"• 1 USD = {rate:.2f} {currency}\n"
                        if target_to_rub > 0:
                            result += f"• 1 {currency} = {target_to_rub:.2f} RUB (рублей)"
                        return result
                    
                    # Пробуем обратный курс
                    response2 = await client.get(
                        f"https://api.exchangerate-api.com/v4/latest/{currency}"
                    )
                    if response2.status_code == 200:
                        data2 = response2.json()
                        usd = data2.get("rates", {}).get("USD", 0)
                        if usd:
                            return f"💱 1 {currency} = {usd:.4f} USD"
                    
                    return f"❌ Валюта '{currency}' не найдена"
                else:
                    return "❌ Не удалось получить курсы валют"
                    
        except Exception as e:
            logger.error(f"Ошибка валют: {e}")
            return f"⚠️ Ошибка получения курса: {str(e)}"
    
    async def search(self, query: str) -> str:
        """Поиск информации через Wikipedia"""
        if not query:
            return "❌ Не указан запрос"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Сначала пробуем русскую Wikipedia
                response = await client.get(
                    f"https://ru.wikipedia.org/api/rest_v1/page/summary/{query}",
                    headers={"User-Agent": "TelegramBot/1.0"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    title = data.get("title", query)
                    extract = data.get("extract", "")
                    
                    if extract:
                        if len(extract) > 800:
                            extract = extract[:800] + "..."
                        return f"📖 {title}\n\n{extract}"
                
                # Fallback — английская Wikipedia
                response2 = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
                    headers={"User-Agent": "TelegramBot/1.0"}
                )
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    extract = data2.get("extract", "")
                    title = data2.get("title", query)
                    
                    if extract:
                        if len(extract) > 800:
                            extract = extract[:800] + "..."
                        return f"📖 {title} (EN)\n\n{extract}"
                
                return f"🔍 По запросу '{query}' ничего не найдено в Wikipedia"
                
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return f"⚠️ Ошибка поиска: {str(e)}"
