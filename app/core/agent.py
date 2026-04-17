from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from app.config import settings

class TelegramAgent:
    def __init__(self, mcp_client, memory):
        self.mcp_client = mcp_client
        self.memory = memory
        
        # Используем современную модель. Gemini на OpenRouter лучше работает с tool_calling
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001", 
            temperature=0, 
            openai_api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        @tool
        async def get_weather(city: str) -> str:
            """Получить текущую погоду в конкретном городе."""
            return await self.mcp_client.get_weather(city)

        @tool
        async def get_currency(currency_code: str) -> str:
            """Получить курс валюты (например, USD, EUR, BTC) к рублю."""
            return await self.mcp_client.get_currency(currency_code)

        @tool
        async def web_search(query: str) -> str:
            """Поиск в интернете актуальной информации, новостей или ответов на вопросы."""
            return await self.mcp_client.search(query)

        @tool
        async def manage_memory(fact: str) -> str:
            """Сохранить важный факт о пользователе (его предпочтения, имя, интересы)."""
            return f"SYSTEM_SAVE: {fact}"

        self.tools = [get_weather, get_currency, web_search, manage_memory]

        # Обновленный промпт для лучшего понимания инструментов
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Ты — полезный ассистент. Если пользователь спрашивает о погоде, валюте или фактах, "
                       "ТЫ ОБЯЗАН вызвать соответствующий инструмент. Не пиши код. "
                       "Если ты сохраняешь факт, обязательно используй manage_memory."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # ИСПОЛЬЗУЕМ create_tool_calling_agent вместо openai_functions
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    async def process_message(self, user_id: int, message: str, chat_history: list = None) -> str:
        try:
            # Получаем все факты о пользователе из БД перед запросом
            facts = self.memory.get_facts(user_id)
            if facts:
                facts_str = "\n".join([f"- {f.content}" for f in facts])
                message = f"Информация о пользователе:\n{facts_str}\n\nКонтекст: {message}"

            result = await self.executor.ainvoke({"input": message, "chat_history": chat_history or []})
            output = result.get("output", "")

            # Обработка сохранения фактов
            if "SYSTEM_SAVE:" in output:
                fact = output.split("SYSTEM_SAVE:")[1].strip()
                self.memory.add_fact(user_id, fact)
                return f"✅ Я запомнил: {fact}"

            return output
        except Exception as e:
            return f"⚠️ Ошибка агента: {str(e)}"
