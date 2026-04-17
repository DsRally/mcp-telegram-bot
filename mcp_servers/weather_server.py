from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI(title="Weather MCP Server")

class WeatherRequest(BaseModel):
    city: str

FAKE_WEATHER = {
    "москва": {"temp": 15, "condition": "облачно"},
    "питер": {"temp": 12, "condition": "дождь"},
    "лондон": {"temp": 10, "condition": "туман"},
    "дубай": {"temp": 35, "condition": "солнечно"},
    "харьков": {"temp": 18, "condition": "ясно"},
}

@app.post("/get_weather")
def get_weather(request: WeatherRequest):
    """Возвращает погоду в городе"""
    city = request.city.lower().strip()
    
    if city in FAKE_WEATHER:
        data = FAKE_WEATHER[city]
        return {
            "city": request.city,
            "temperature": data["temp"],
            "condition": data["condition"],
            "message": f"В городе {request.city.capitalize()}: {data['temp']}°C, {data['condition']}"
        }
    
    temp = random.randint(-5, 30)
    return {
        "city": request.city,
        "temperature": temp,
        "condition": "переменная облачность",
        "message": f"В городе {request.city.capitalize()} сейчас около {temp}°C, переменная облачность."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
