import inspect
import os

from langchain.tools import tool
from langchain_classic.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from app.config import settings

class TelegramAgent:
    def __init__(self, mcp_client, memory):
        self.mcp_client = mcp_client
        self.memory = memory
        
        # Инициализация LLM с правками под OpenRouter
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001", 
            temperature=0, 
            openai_api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"  # Критически важная правка для ключей sk-or-v1
        )

        # Инструменты
        self.tools = [
            self.get_weather_tool,
            self.get_currency_tool,
            self.web_search_tool,
            self.manage_user_memory_tool
        ]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Ты — полезный Telegram-агент. Если пользователь говорит факт о себе — сохрани его."),
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

    @tool
    async def get_weather_tool(self, city: str) -> str:
        """Узнать погоду в городе."""
        return await self.mcp_client.get_weather(city)

    @tool
    async def get_currency_tool(self, currency_code: str) -> str:
        """Узнать курс валюты (USD, EUR...)."""
        return await self.mcp_client.get_currency(currency_code)

    @tool
    async def web_search_tool(self, query: str) -> str:
        """Поиск информации в интернете."""
        return await self.mcp_client.search(query)

    @tool
    async def manage_user_memory_tool(self, telegram_id: int, action: str, fact: str = None) -> str:
        """Сохранить ('save') или получить ('list') факты о пользователе."""
        if action == "save" and fact:
            self.memory.add_fact(telegram_id, fact)
            return f"Запомнил: {fact}"
        facts = self.memory.get_facts(telegram_id)
        return "О тебе я знаю: " + ", ".join(facts) if facts else "Ничего не знаю."

    async def process_message(self, user_id: int, message: str, chat_history: list = None) -> str:
        try:
            history = chat_history if chat_history is not None else []

            inv = self.executor.ainvoke(
                {
                    "input": message,
                    "chat_history": history,
                    "telegram_id": user_id,
                }
            )
            result = await inv if inspect.isawaitable(inv) else inv

            if not isinstance(result, dict):
                return str(result) if result is not None else ""

            raw = result.get("output", "Извините, не удалось сформировать ответ.")
            return raw if isinstance(raw, str) else str(raw)

        except Exception as e:
            print(f"Agent Error: {e}")
            return f"⚠️ Ошибка агента: {str(e)}"
