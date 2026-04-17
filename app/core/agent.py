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
        
        # Стабильная модель Gemini 2.0
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001", 
            temperature=0, 
            openai_api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        @tool
        async def get_weather(city: str) -> str:
            """Get current weather in a specific city. Argument: city (string)"""
            return await self.mcp_client.get_weather(city)

        @tool
        async def get_currency(currency_code: str) -> str:
            """Get exchange rate for a currency (e.g. USD, EUR). Argument: currency_code (string)"""
            return await self.mcp_client.get_currency(currency_code)

        @tool
        async def web_search(query: str) -> str:
            """Search the web for any current information."""
            return await self.mcp_client.search(query)

        @tool
        async def save_memory(fact: str) -> str:
            """Save a personal fact about the user for future use."""
            return f"SYSTEM_SAVE_FACT: {fact}"

        self.tools = [get_weather, get_currency, web_search, save_memory]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Ты — официальный Telegram-ассистент. 
Твоя задача: помогать пользователю, используя инструменты.
1. Если вопрос про погоду или валюту — ты ОБЯЗАН вызвать инструмент.
2. ЗАПРЕЩЕНО писать технический код или JSON пользователю.
3. Если ты вызываешь инструмент, дождись ответа системы и перескажи его красиво.
4. Если пользователь говорит факт о себе — используй save_memory."""),
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
            result = await self.executor.ainvoke({
                "input": message,
                "chat_history": chat_history or []
            })

            output = result.get("output", "")

            # Обработка сохранения фактов
            if "SYSTEM_SAVE_FACT:" in output:
                fact = output.replace("SYSTEM_SAVE_FACT:", "").strip()
                self.memory.add_fact(user_id, fact)
                return f"✅ Я запомнил: {fact}"

            return output

        except Exception as e:
            return f"⚠️ Ошибка агента: {str(e)}"
