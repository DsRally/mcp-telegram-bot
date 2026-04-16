from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LangSearch Server")

class SearchRequest(BaseModel):
    query: str

# Используем SearchApi.io (часто используется в связке с LangChain)
# Зарегистрируйся на searchapi.io и вставь ключ сюда
SEARCH_API_KEY = "cKhGCs5k1ycTgQWGNFFy6c4X"

@app.post("/search")
async def search(request: SearchRequest):
    query = request.query.strip()
    
    if not query:
        return {"message": "❌ Пустой запрос"}
    
    # Мы будем использовать движок Google Search через SearchApi
    url = "https://www.searchapi.io/api/v1/search"
    
    params = {
        "engine": "google",
        "q": query,
        "api_key": SEARCH_API_KEY,
        "num": 3  # Количество результатов
    }
    
    try:
        # trust_env=True позволяет httpx подхватывать системные настройки прокси (VPN)
        async with httpx.AsyncClient(trust_env=True) as client:
            response = await client.get(url, params=params, timeout=20.0)
            
            logger.info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # SearchApi возвращает результаты в ключе 'organic_results'
                results = data.get("organic_results", [])
                # Некоторые движки дают быстрый ответ в 'answer_box'
                answer_box = data.get("answer_box", {}).get("answer") or data.get("answer_box", {}).get("snippet")
                
                message_parts = []
                
                if answer_box:
                    message_parts.append(f"💡 Прямой ответ: {answer_box}")
                
                if results:
                    links = "\n\n🔗 Найденные источники:\n"
                    for i, res in enumerate(results[:3], 1):
                        title = res.get("title", "Без названия")
                        link = res.get("link", "")
                        snippet = res.get("snippet", "")[:150]
                        links += f"{i}. {title}\n{snippet}...\n{link}\n\n"
                    message_parts.append(links)
                
                if not message_parts:
                    return {"query": query, "message": "Ничего не нашлось 🤷‍♂️"}
                
                return {
                    "query": query,
                    "message": "\n".join(message_parts)
                }
            
            else:
                return {
                    "query": query, 
                    "message": f"⚠️ Ошибка поиска (Код {response.status_code}): {response.text[:100]}"
                }
                
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return {
            "query": query,
            "message": f"⚠️ Ошибка подключения к поисковому движку. Проверьте VPN."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)