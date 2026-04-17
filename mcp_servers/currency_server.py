from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Currency MCP Server")

class CurrencyRequest(BaseModel):
    currency: str

# API ключ из переменной окружения
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")

@app.post("/get_rate")
async def get_rate(request: CurrencyRequest):
    """Возвращает курс валюты к USD"""
    currency = request.currency.upper().strip()
    
    # Если нет API ключа — используем фиксированные курсы
    if not EXCHANGE_RATE_API_KEY:
        fallback_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "UAH": 36.5,
            "RUB": 92.5,
            "JPY": 150.2,
            "CNY": 7.2,
        }
        rate = fallback_rates.get(currency)
        if rate:
            return {
                "currency": currency,
                "rate": rate,
                "message": f"Курс {currency} к USD: {rate} (демо-данные, добавьте EXCHANGE_RATE_API_KEY для реальных курсов)"
            }
        else:
            return {
                "currency": currency,
                "rate": None,
                "message": f"Валюта {currency} не найдена в демо-данных."
            }
    
    # Реальный API запрос
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Используем ExchangeRate-API
            response = await client.get(
                f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/USD"
            )
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get("conversion_rates", {})
                rate = rates.get(currency)
                
                if rate:
                    return {
                        "currency": currency,
                        "rate": rate,
                        "message": f"Курс {currency} к USD: {rate:.2f}"
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
        return {
            "currency": currency,
            "rate": None,
            "message": f"Ошибка получения курса: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
