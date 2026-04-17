from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Search MCP Server")

class SearchRequest(BaseModel):
    query: str

SEARCH_API_KEY = os.getenv("SERPAPI_KEY", "ckhGCs5k1ycTgQWGNFFy6c4X")

@app.post("/search")
async def search(request: SearchRequest):
    query = request.query.strip()
    if not query:
        return {"message": "Пустой запрос."}
    
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SEARCH_API_KEY,
        "num": 3
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=15.0)
            data = response.json()
            
            answer = data.get("answer_box", {}).get("answer")
            if answer:
                return {"message": f"💡 Ответ: {answer}"}
            
            results = data.get("organic_results", [])
            if results:
                top = results[0]
                return {"message": f"🔍 Нашел: {top.get('title')}\n{top.get('snippet')}\nИсточник: {top.get('link')}"}
            
            return {"message": "Ничего не найдено."}
    except Exception as e:
        return {"message": f"Ошибка поиска: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
