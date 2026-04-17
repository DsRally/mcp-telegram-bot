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
        
        # Используем стабильную версию модели
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001", 
            temperature=0, 
            openai_api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Инструменты определяем здесь, чтобы исключить 'self' из схемы
        @tool
        async def get_weather(city: str) -> str:
            """Узнать текущую погоду в конкретном городе."""
            return await self.mcp_client.get_weather(city)

        @tool
        async def get_currency(currency_code: str) -> str:
            """Узнать курс валюты (например, USD, EUR, RUB, BTC)."""
            return await self.mcp_client.get_currency(currency_code)

        @tool
        async def web_search(query: str) -> str:
            """Поиск любой актуальной информации в интернете."""
            return await self.mcp_client.search(query)

        @tool
        async def manage_memory(action: str, fact: str = None) -> str:
            """Сохранить ('save') или получить ('list') факты о пользователе."""
            # Мы добавим логику сохранения в методе process_message для надежности
            return "Инструмент памяти вызван"

        self.tools = [get_weather, get_currency, web_search, manage_memory]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Ты — умный Telegram-ассистент. 
Если ты не знаешь точного ответа на текущий момент (погода, валюта, новости) — ОБЯЗАТЕЛЬНО вызывай инструменты.
Никогда не пиши код вызова функции текстом, всегда используй встроенный механизм инструментов (tool calling).
Если пользователь говорит что-то о себе — используй manage_memory."""),
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

            # Запускаем выполнение
            result = await self.executor.ainvoke(
                {
                    "input": message,
                    "chat_history": history,
                }
            )

            # Простая логика сохранения фактов, если агент решил, что это нужно
            output = result.get("output", "")
            
            # Если в ответе агент говорит, что запомнил что-то, дублируем в БД
            lower_out = output.lower()
            if any(word in lower_out for word in ["запомнил", "сохранил", "записал"]):
                 self.memory.add_fact(user_id, message)

            return output

        except Exception as e:
            print(f"Agent Error: {e}")
            return f"⚠️ Ошибка агента: {str(e)}"
