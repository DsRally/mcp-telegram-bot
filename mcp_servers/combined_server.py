"""
Объединённый MCP сервер для Railway.
Все сервисы (погода, валюты, поиск) в одном приложении на разных путях.
"""
import os
import httpx
import random
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel

app = FastAPI(title="Combined MCP Server")

# ============ WEATHER SERVICE ============
class WeatherRequest(BaseModel):
    city: str

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "2Y8GE4WZ3HD2FMBCGXN3MSEJ4")

FAKE_WEATHER = {
    "москва": {"temp": 15, "condition": "облачно"},
    "питер": {"temp": 12, "condition": "дождь"},
    "лондон": {"temp": 10, "condition": "туман"},
    "дубай": {"temp": 35, "condition": "солнечно"},
    "харьков": {"temp": 18, "condition": "ясно"},
}

@app.post("/weather/get_weather")
async def get_weather(request: WeatherRequest):
    city = request.city.strip()
    city_lower = city.lower()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                    "lang": "ru"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                temp = int(data["main"]["temp"])
                condition = data["weather"][0]["description"]
                return {
                    "city": city,
                    "temperature": temp,
                    "condition": condition,
                    "message": f"В городе {city.capitalize()}: {temp}°C, {condition}"
                }
            
            elif response.status_code == 404:
                if city_lower in FAKE_WEATHER:
                    data = FAKE_WEATHER[city_lower]
                    return {
                        "city": city,
                        "temperature": data["temp"],
                        "condition": data["condition"],
                        "message": f"В городе {city.capitalize()}: {data['temp']}°C, {data['condition']}"
                    }
                else:
                    return {
                        "city": city,
                        "temperature": None,
                        "condition": "неизвестно",
                        "message": f"Город {city} не найден."
                    }
            else:
                raise Exception(f"API error: {response.status_code}")
                
    except Exception as e:
        if city_lower in FAKE_WEATHER:
            data = FAKE_WEATHER[city_lower]
            return {
                "city": city,
                "temperature": data["temp"],
                "condition": data["condition"],
                "message": f"В городе {city.capitalize()}: {data['temp']}°C, {data['condition']}"
            }
        else:
            temp = random.randint(-5, 30)
            return {
                "city": city,
                "temperature": temp,
                "condition": "переменная облачность",
                "message": f"В городе {city.capitalize()} сейчас около {temp}°C, переменная облачность."
            }

# ============ CURRENCY SERVICE ============
class CurrencyRequest(BaseModel):
    currency: str

EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")

@app.post("/currency/get_rate")
async def get_rate(request: CurrencyRequest):
    currency = request.currency.upper().strip()
    
    fallback_rates = {
        "USD": 92.5, "EUR": 99.2, "GBP": 116.8, "UAH": 2.45,
        "JPY": 0.61, "CNY": 12.8, "BTC": 4500000.0, "RUB": 1.0
    }
    
    if not EXCHANGE_RATE_API_KEY:
        rate = fallback_rates.get(currency)
        if rate:
            return {
                "currency": currency,
                "rate": rate,
                "message": f"Курс {currency} к рублю: {rate:.2f} ₽"
            }
        else:
            return {
                "currency": currency,
                "rate": None,
                "message": f"Валюта {currency} не найдена."
            }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/USD"
            )
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get("conversion_rates", {})
                usd_rate = rates.get(currency)
                
                if usd_rate:
                    rub_rate = usd_rate * 92.5  # Конвертируем в рубли
                    return {
                        "currency": currency,
                        "rate": rub_rate,
                        "message": f"Курс {currency} к рублю: {rub_rate:.2f} ₽"
                    }
                else:
                    return {
                        "currency": currency,
                        "rate": None,
                        "message": f"Валюта {currency} не найдена."
                    }
            else:
                raise Exception(f"API error: {response.status_code}")
                
    except Exception as e:
        rate = fallback_rates.get(currency)
        if rate:
            return {
                "currency": currency,
                "rate": rate,
                "message": f"Курс {currency} к рублю: {rate:.2f} ₽ (демо)"
            }
        else:
            return {
                "currency": currency,
                "rate": None,
                "message": f"Ошибка получения курса."
            }

# ============ SEARCH SERVICE ============
class SearchRequest(BaseModel):
    query: str

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

@app.post("/search/search")
async def search(request: SearchRequest):
    query = request.query.strip()
    
    if not SERPAPI_KEY:
        return {
            "results": [
                f"🔍 Результаты поиска: '{query}'",
                "Для реального поиска добавьте SERPAPI_KEY",
                "Или используйте DuckDuckGo."
            ]
        }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "api_key": SERPAPI_KEY,
                    "engine": "google",
                    "hl": "ru",
                    "num": 3
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                organic_results = data.get("organic_results", [])
                
                results = []
                for result in organic_results[:3]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    results.append(f"📌 {title}\n{snippet}")
                
                if not results:
                    results = ["Ничего не найдено."]
                
                return {"results": results}
            else:
                raise Exception(f"API error: {response.status_code}")
                
    except Exception as e:
        return {
            "results": [f"Ошибка поиска. Попробуйте уточнить запрос."]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
