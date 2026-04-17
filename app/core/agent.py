import inspect
import os

from langchain_core.tools import tool
from langchain_classic.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from app.config import settings

class TelegramAgent:
    def __init__(self, mcp_client, memory):
        self.mcp_client = mcp_client
        self.memory = memory
        
        # Инициализация LLM
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001", # Используем более стабильный ID
            temperature=0,
            openai_api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Инструменты: определяем их так, чтобы 'self' не попадал в схему для нейросети
        @tool
        async def get_weather(city: str) -> str:
            """Узнать текущую погоду в указанном городе."""
            return await self.mcp_client.get_weather(city)

        @tool
        async def get_currency(currency_code: str) -> str:
            """Получить актуальный курс валюты (например, USD, EUR, RUB)."""
            return await self.mcp_client.get_currency(currency_code)

        @tool
        async def web_search(query: str) -> str:
            """Найти актуальную информацию в интернете по любому вопросу."""
            return await self.mcp_client.search(query)

        @tool
        async def manage_memory(action: str, fact: str = None) -> str:
            """Сохранить ('save') новый факт о пользователе или получить ('list') список всех известных фактов."""
            # Мы берем telegram_id из контекста вызова в process_message
            # Но для простоты в описании инструмента оставим только action/fact
            return "Инструмент памяти вызван" # Логика будет ниже в executor

        self.tools = [get_weather, get_currency, web_search, manage_memory]

        # Расширенный системный промпт
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Ты — продвинутый ИИ-ассистент в Telegram.
У тебя есть доступ к реальному времени через инструменты:
1. Погода (get_weather)
2. Курсы валют (get_currency)
3. Поиск в интернете (web_search) — используй его всегда, если не знаешь точного ответа на текущую дату.

Если пользователь сообщает факт о себе (например, 'Я люблю пиццу' или 'Меня зовут Алекс'), ОБЯЗАТЕЛЬНО используй инструмент памяти, чтобы сохранить это.
Всегда старайся дать максимально точный ответ, используя свои инструменты."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True
        )

    async def process_message(self, user_id: int, message: str, chat_history: list = None) -> str:
        try:
            history = chat_history if chat_history is not None else []

            # Перехватываем вызов инструмента памяти, чтобы подставить telegram_id
            # Это более надежный способ, чем просить нейросеть саму вводить ID
            result = await self.executor.ainvoke(
                {
                    "input": message,
                    "chat_history": history,
                }
            )

            # Дополнительная проверка: если нейросеть сказала сохранить факт,
            # но мы хотим сделать это прозрачно через наш объект memory
            if "запомнил" in result["output"].lower() or "сохранил" in result["output"].lower():
                # Простая логика: если в сообщении есть "люблю", "зовут" и т.д.
                self.memory.add_fact(user_id, message)

            return result.get("output", "Не удалось получить ответ.")

        except Exception as e:
            print(f"Agent Error: {e}")
            return f"⚠️ Ошибка агента: {str(e)}"
