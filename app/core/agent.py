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
        
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001", 
            temperature=0, 
            openai_api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        @tool
        async def get_weather(city: str) -> str:
            """Get current weather in a city."""
            return await self.mcp_client.get_weather(city)

        @tool
        async def get_currency(currency_code: str) -> str:
            """Get exchange rate (USD, EUR, etc)."""
            return await self.mcp_client.get_currency(currency_code)

        @tool
        async def web_search(query: str) -> str:
            """Search the web for current information."""
            return await self.mcp_client.search(query)

        @tool
        async def manage_memory(fact: str) -> str:
            """Save a fact about the user."""
            return f"SYSTEM_SAVE: {fact}"

        self.tools = [get_weather, get_currency, web_search, manage_memory]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Ты — ассистент. Для погоды, валют и поиска ВСЕГДА используй инструменты. Никогда не пиши код в ответ."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    async def process_message(self, user_id: int, message: str, chat_history: list = None) -> str:
        try:
            result = await self.executor.ainvoke({"input": message, "chat_history": chat_history or []})
            output = result.get("output", "")

            if "SYSTEM_SAVE:" in output:
                fact = output.split("SYSTEM_SAVE:")[1].strip()
                self.memory.add_fact(user_id, fact)
                return f"✅ Запомнил: {fact}"

            return output
        except Exception as e:
            return f"⚠️ Ошибка: {str(e)}"
