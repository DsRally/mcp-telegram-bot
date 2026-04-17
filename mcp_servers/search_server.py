from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Search MCP Server")

class SearchRequest(BaseModel):
    query: str

# API ключ из переменной окружения
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

@app.post("/search")
async def search(request: SearchRequest):
    """Поиск информации в интернете"""
    query = request.query.strip()
    
    # Если нет API ключа — возвращаем заглушку
    if not SERPAPI_KEY:
        return {
            "results": [
                f"🔍 Поиск по запросу '{query}' (демо-режим)",
                "Для реального поиска добавьте SERPAPI_KEY в переменные окружения.",
                "Или используйте DuckDuckGo/Brave Search API."
            ]
        }
    
    # Реальный API запрос через SerpApi
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
                    link = result.get("link", "")
                    results.append(f"📌 {title}\n{snippet}\n🔗 {link}")
                
                if not results:
                    results = ["Ничего не найдено по вашему запросу."]
                
                return {"results": results}
            else:
                raise Exception(f"API error: {response.status_code}")
                
    except Exception as e:
        return {
            "results": [f"Ошибка поиска: {str(e)}"]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
