from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import random

app = FastAPI(title="Combined MCP Server")

# --- Модели данных ---
class WeatherRequest(BaseModel):
    city: str

class CurrencyRequest(BaseModel):
    currency: str

class SearchRequest(BaseModel):
    query: str

# --- Настройки ---
CURRENCY_API_KEY = "6bac6e0bb871fd569a25c642"
SEARCH_API_KEY = "cKhGCs5k1ycTgQWGNFFy6c4X"

# --- Эндпоинт ПОГОДЫ ---
@app.post("/get_weather")
async def get_weather(request: WeatherRequest):
    city = request.city.lower().strip()
    FAKE_WEATHER = {"харьков": 18, "москва": 15, "киев": 17}
    temp = FAKE_WEATHER.get(city, random.randint(10, 25))
    return {"message": f"В городе {city.capitalize()} сейчас {temp}°C."}

# --- Эндпоинт ВАЛЮТЫ ---
@app.post("/get_rate")
async def get_rate(request: CurrencyRequest):
    currency = request.currency.upper().strip()
    try:
        url = f"https://v6.exchangerate-api.com/v6/{CURRENCY_API_KEY}/pair/{currency}/RUB"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            data = resp.json()
            if data.get("result") == "success":
                return {"message": f"Курс {currency}: {round(data['conversion_rate'], 2)} ₽"}
            return {"message": f"Валюта {currency} не найдена."}
    except:
        return {"message": "Ошибка сервиса валют."}

# --- Эндпоинт ПОИСКА ---
@app.post("/search")
async def search(request: SearchRequest):
    try:
        url = "https://www.searchapi.io/api/v1/search"
        params = {"engine": "google", "q": request.query, "api_key": SEARCH_API_KEY}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=15.0)
            data = resp.json()
            results = data.get("organic_results", [])
            if results:
                return {"message": f"Нашел: {results[0].get('title')}\n{results[0].get('link')}"}
            return {"message": "Ничего не найдено."}
    except:
        return {"message": "Ошибка поиска."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
