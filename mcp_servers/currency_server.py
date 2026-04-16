from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI(title="Currency MCP Server")

class CurrencyRequest(BaseModel):
    currency: str

# ВСТАВЬ СЮДА СВОЙ API КЛЮЧ от exchangerate-api.com
API_KEY = "6bac6e0bb871fd569a25c642"

@app.post("/get_rate")
async def get_rate(request: CurrencyRequest):
    """Реальный курс валюты к рублю через Exchange Rate API"""
    currency = request.currency.upper().strip()
    
    # Очистка от лишних слов
    currency = currency.replace("ДОЛЛАР", "USD").replace("$", "USD")
    currency = currency.replace("ЕВРО", "EUR").replace("€", "EUR")
    currency = currency.replace("ФУНТ", "GBP").replace("£", "GBP")
    currency = currency.replace("ЮАНЬ", "CNY").replace("¥", "CNY")
    currency = currency.replace("ГРИВНА", "UAH").replace("ГРН", "UAH")
    currency = currency.replace("ЙЕНА", "JPY").replace("ИЕНА", "JPY")
    currency = currency.replace("РУБ", "RUB").replace("РУБЛЬ", "RUB")
    
    # Если рубль — возвращаем 1
    if currency == "RUB":
        return {
            "currency": request.currency,
            "rate": 1.0,
            "name": "российский рубль",
            "message": "💱 Курс RUB: 1 ₽"
        }
    
    try:
        # Запрос к Exchange Rate API
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{currency}/RUB"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            data = response.json()
            
            if data.get("result") == "success":
                rate = data["conversion_rate"]
                return {
                    "currency": currency,
                    "rate": round(rate, 2),
                    "name": currency,
                    "message": f"💱 Курс {currency}: {round(rate, 2)} ₽"
                }
            else:
                error_type = data.get("error-type", "unknown")
                return {
                    "currency": request.currency,
                    "rate": 0,
                    "name": "ошибка",
                    "message": f"❌ Ошибка API: {error_type}. Проверьте код валюты."
                }
                
    except Exception as e:
        return {
            "currency": request.currency,
            "rate": 0,
            "name": "ошибка",
            "message": f"⚠️ Ошибка: {str(e)}"
        }

@app.get("/health")
def health():
    return {"status": "alive", "service": "currency"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)