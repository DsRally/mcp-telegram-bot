import inspect
from langchain_core.tools import tool
from langchain_classic.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from app.config import settings

class TelegramAgent:
    def __init__(self, mcp_client, memory):
        self.mcp_client = mcp_client
        self.memory = memory
        
        # Обновляем модель до стабильной версии
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001", 
            temperature=0, 
            openai_api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # ОПРЕДЕЛЯЕМ ИНСТРУМЕНТЫ БЕЗ SELF
        @tool
        async def get_weather(city: str) -> str:
            """Узнать текущую погоду в городе. Аргумент: city (название города)."""
            return await self.mcp_client.get_weather(city)

        @tool
        async def get_currency(currency_code: str) -> str:
            """Узнать курс валюты. Аргумент: currency_code (например, USD, EUR)."""
            return await self.mcp_client.get_currency(currency_code)

        @tool
        async def web_search(query: str) -> str:
            """Поиск информации в интернете."""
            return await self.mcp_client.search(query)

        @tool
        async def manage_memory(fact: str) -> str:
            """Сохранить важный факт о пользователе, который он сообщил."""
            return f"ФАКТ_ДЛЯ_СОХРАНЕНИЯ: {fact}"

        self.tools = [get_weather, get_currency, web_search, manage_memory]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Ты — полезный ассистент. 
Если тебе задают вопрос о погоде или валюте — ОБЯЗАТЕЛЬНО вызывай соответствующий инструмент.
Если пользователь говорит что-то о себе — используй инструмент manage_memory.
Отвечай всегда на языке пользователя."""),
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
            result = await self.executor.ainvoke({
                "input": message,
                "chat_history": history
            })

            output = result.get("output", "")

            # Исправляем сохранение фактов
            if "ФАКТ_ДЛЯ_СОХРАНЕНИЯ:" in output:
                fact = output.replace("ФАКТ_ДЛЯ_СОХРАНЕНИЯ:", "").strip()
                self.memory.add_fact(user_id, fact)
                return f"Я запомнил: {fact}"

            return output

        except Exception as e:
            print(f"Agent Error: {e}")
            return f"⚠️ Ошибка: {str(e)}"
