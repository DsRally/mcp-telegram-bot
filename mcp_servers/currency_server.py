from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI(title="Currency MCP Server")

class CurrencyRequest(BaseModel):
    currency: str

# Твой API ключ
API_KEY = "6bac6e0bb871fd569a25c642"

@app.post("/get_rate")
async def get_rate(request: CurrencyRequest):
    """Реальный курс валюты к рублю"""
    raw_currency = request.currency.upper().strip()
    
    # Словарь синонимов для надежности
    synonyms = {
        "ДОЛЛАР": "USD", "ДОЛЛАРЫ": "USD", "$": "USD",
        "ЕВРО": "EUR", "€": "EUR",
        "ФУНТ": "GBP", "ФУНТЫ": "GBP",
        "ГРИВНА": "UAH", "ГРН": "UAH",
        "РУБЛЬ": "RUB", "РУБ": "RUB"
    }
    
    currency = synonyms.get(raw_currency, raw_currency)
    
    if currency == "RUB":
        return {"message": "Курс RUB к RUB всегда 1 к 1."}
    
    try:
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{currency}/RUB"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            data = response.json()
            
            if data.get("result") == "success":
                rate = round(data["conversion_rate"], 2)
                return {
                    "currency": currency,
                    "message": f"💱 Текущий курс {currency}: {rate} ₽"
                }
            else:
                return {"message": f"Не удалось найти валюту {currency}. Попробуйте код (USD, EUR)."}
                
    except Exception as e:
        return {"message": f"Ошибка сервиса валют: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
