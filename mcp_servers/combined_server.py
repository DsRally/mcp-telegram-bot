from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "")


class ToolRequest(BaseModel):
    arguments: dict = {}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {
                "name": "get_weather",
                "description": "Получить текущую погоду в городе",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Название города"
                        }
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
                        "currency": {
                            "type": "string",
                            "description": "Код валюты, например USD, EUR, RUB"
                        }
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
                        "query": {
                            "type": "string",
                            "description": "Поисковый запрос"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    }


@app.post("/tools/get_weather")
async def get_weather(request: ToolRequest):
    city = request.arguments.get("city", "")
    if not city:
        return {"error": "Не указан город"}

    if not WEATHER_API_KEY:
        # Fallback без API ключа
        return {
            "result": f"Погода в {city}: ~15°C, облачно. (Для точных данных добавьте WEATHER_API_KEY)"
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "http://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": WEATHER_API_KEY,
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
                return {
                    "result": (
                        f"Погода в {city}:\n"
                        f"🌡 Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                        f"☁️ {description.capitalize()}\n"
                        f"💧 Влажность: {humidity}%\n"
                        f"💨 Ветер: {wind} м/с"
                    )
                }
            else:
                return {"error": f"Город '{city}' не найден"}
    except Exception as e:
        return {"error": f"Ошибка получения погоды: {str(e)}"}


@app.post("/tools/get_exchange_rate")
async def get_exchange_rate(request: ToolRequest):
    currency = request.arguments.get("currency", "").upper()
    if not currency:
        return {"error": "Не указана валюта"}

    # Маппинг популярных валют
    currency_map = {
        "ДОЛЛАР": "USD",
        "ЕВРО": "EUR",
        "РУБЛЬ": "RUB",
        "ГРИВНА": "UAH",
        "ФУНТ": "GBP",
    }
    currency = currency_map.get(currency, currency)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Используем бесплатный API без ключа
            response = await client.get(
                f"https://api.exchangerate-api.com/v4/latest/USD"
            )
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})

                if currency == "USD":
                    return {"result": "1 USD = 1 USD 😄"}

                if currency in rates:
                    rate = rates[currency]
                    usd_rate = 1 / rate
                    return {
                        "result": (
                            f"Курс валют:\n"
                            f"💵 1 USD = {rate:.2f} {currency}\n"
                            f"💱 1 {currency} = {usd_rate:.4f} USD"
                        )
                    }
                else:
                    # Попробуем другой эндпоинт
                    response2 = await client.get(
                        f"https://api.exchangerate-api.com/v4/latest/{currency}"
                    )
                    if response2.status_code == 200:
                        data2 = response2.json()
                        usd = data2.get("rates", {}).get("USD", 0)
                        return {
                            "result": f"💵 1 {currency} = {usd:.4f} USD"
                        }
                    return {"error": f"Валюта '{currency}' не найдена"}
            else:
                return {"error": "Не удалось получить курсы валют"}
    except Exception as e:
        return {"error": f"Ошибка получения курса: {str(e)}"}


@app.post("/tools/search_info")
async def search_info(request: ToolRequest):
    query = request.arguments.get("query", "")
    if not query:
        return {"error": "Не указан запрос"}

    # Используем Wikipedia API (бесплатно, без ключа)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://ru.wikipedia.org/api/rest_v1/page/summary/" + query,
                headers={"User-Agent": "TelegramBot/1.0"}
            )
            if response.status_code == 200:
                data = response.json()
                title = data.get("title", query)
                extract = data.get("extract", "")
                if extract:
                    # Обрезаем до 500 символов
                    if len(extract) > 500:
                        extract = extract[:500] + "..."
                    return {
                        "result": f"📖 {title}\n\n{extract}"
                    }

            # Fallback - английская Wikipedia
            response2 = await client.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/" + query,
                headers={"User-Agent": "TelegramBot/1.0"}
            )
            if response2.status_code == 200:
                data2 = response2.json()
                extract = data2.get("extract", "")
                title = data2.get("title", query)
                if extract:
                    if len(extract) > 500:
                        extract = extract[:500] + "..."
                    return {
                        "result": f"📖 {title}\n\n{extract}"
                    }

            return {"result": f"По запросу '{query}' информация не найдена в Wikipedia"}
    except Exception as e:
        return {"error": f"Ошибка поиска: {str(e)}"}
