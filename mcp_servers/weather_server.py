from fastapi import FastAPI
from pydantic import BaseModel

# Создаём приложение
app = FastAPI(title="Weather MCP Server")

# Модель запроса (что приходит от бота)
class WeatherRequest(BaseModel):
    city: str

# Фейковая база погоды (потом заменим на реальное API)
FAKE_WEATHER = {
    "москва": {"temp": 15, "condition": "облачно"},
    "питер": {"temp": 12, "condition": "дождь"},
    "лондон": {"temp": 10, "condition": "туман"},
    "дубай": {"temp": 35, "condition": "солнечно"},
}

@app.post("/get_weather")
def get_weather(request: WeatherRequest):
    """Возвращает погоду в городе"""
    city = request.city.lower()
    
    # Ищем в фейковой базе
    if city in FAKE_WEATHER:
        data = FAKE_WEATHER[city]
        return {
            "city": request.city,
            "temperature": data["temp"],
            "condition": data["condition"],
            "message": f"В городе {request.city}: {data['temp']}°C, {data['condition']}"
        }
    
    # Если города нет в базе — рандомная температура
    import random
    temp = random.randint(-5, 30)
    return {
        "city": request.city,
        "temperature": temp,
        "condition": "неизвестно",
        "message": f"В городе {request.city}: {temp}°C (данные уточняются)"
    }

@app.get("/health")
def health():
    """Проверка, жив ли сервер"""
    return {"status": "alive", "service": "weather"}

# Для теста: запуск напрямую
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)