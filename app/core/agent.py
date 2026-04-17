"""
Telegram AI Agent — использует langchain_core напрямую.
Нет зависимости от AgentExecutor (удалён в langchain 1.0).
Работает на langchain 0.3.x через ручной tool-calling цикл.
"""
import json
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from app.config import settings
class TelegramAgent:
    def __init__(self, mcp_client, memory):
        self.mcp_client = mcp_client
        self.memory = memory
        # LLM через OpenRouter (совместим с OpenAI API)
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001",
            temperature=0,
            openai_api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        # ---- Определяем инструменты ----
        @tool
        async def get_weather(city: str) -> str:
            """Получить текущую погоду в конкретном городе. Используй этот инструмент когда пользователь спрашивает о погоде."""
            return await self.mcp_client.get_weather(city)
        @tool
        async def get_currency(currency_code: str) -> str:
            """Получить курс валюты к рублю. Аргумент — код валюты, например USD, EUR, BTC. Используй когда спрашивают о курсе валют."""
            return await self.mcp_client.get_currency(currency_code)
        @tool
        async def web_search(query: str) -> str:
            """Поиск актуальной информации, новостей или ответов на вопросы в интернете. Используй для любых актуальных данных."""
            return await self.mcp_client.search(query)
        @tool
        async def save_user_fact(fact: str) -> str:
            """Сохранить важный факт о пользователе: его имя, предпочтения, интересы. Используй когда пользователь сообщает что-то личное о себе."""
            return f"__SAVE_FACT__:{fact}"
        self.tools = [get_weather, get_currency, web_search, save_user_fact]
        # Привязываем инструменты к LLM (работает в langchain 0.3.x)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        # Словарь для быстрого вызова инструментов по имени
        self.tools_map = {t.name: t for t in self.tools}
        # Системный промпт
        self.system_prompt = (
            "Ты полезный ассистент. Отвечай на русском языке. "
            "Если пользователь спрашивает о погоде — ОБЯЗАТЕЛЬНО вызови get_weather. "
            "Если о курсе валют — вызови get_currency. "
            "Если нужна актуальная информация — вызови web_search. "
            "Если пользователь называет личные данные о себе (имя, предпочтения) — вызови save_user_fact. "
            "Никогда не выдумывай данные — всегда используй инструменты."
        )
    async def _run_tool(self, tool_name: str, tool_args: dict) -> str:
        """Вызывает инструмент по имени и возвращает результат."""
        tool_fn = self.tools_map.get(tool_name)
        if not tool_fn:
            return f"Инструмент '{tool_name}' не найден."
        try:
            result = tool_fn.invoke(tool_args)
            # Если результат — корутина (async tool), ждём её
            if asyncio.iscoroutine(result):
                result = await result
            return str(result)
        except Exception as e:
            return f"Ошибка при вызове {tool_name}: {str(e)}"
    async def process_message(
        self, user_id: int, message: str, chat_history: list = None
    ) -> str:
        """
        Основной метод обработки сообщения пользователя.
        Реализует ручной tool-calling цикл без AgentExecutor.
        """
        try:
            # Получаем сохранённые факты о пользователе
            facts = self.memory.get_facts(user_id)
            system_content = self.system_prompt
            if facts:
                facts_str = "\n".join([f"- {f}" for f in facts])
                system_content += f"\n\nИзвестные факты о пользователе:\n{facts_str}"
            # Формируем список сообщений для LLM
            messages = [SystemMessage(content=system_content)]
            # Добавляем историю чата
            if chat_history:
                messages.extend(chat_history)
            # Добавляем текущее сообщение пользователя
            messages.append(HumanMessage(content=message))
            # Цикл tool-calling (максимум 5 итераций чтобы не зациклиться)
            for _ in range(5):
                response = await self.llm_with_tools.ainvoke(messages)
                messages.append(response)
                # Если LLM не вызывает инструменты — возвращаем ответ
                if not response.tool_calls:
                    output = response.content
                    # Проверяем на сохранение факта (на случай если пришло через текст)
                    if "__SAVE_FACT__:" in output:
                        fact = output.split("__SAVE_FACT__:")[1].strip()
                        self.memory.add_fact(user_id, fact)
                        return f"✅ Я запомнил: {fact}"
                    return output
                # Выполняем все запрошенные инструменты
                tool_results = []
                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]
                    tool_call_id = tc["id"]
                    result = await self._run_tool(tool_name, tool_args)
                    # Проверяем — вдруг инструмент save_user_fact
                    if "__SAVE_FACT__:" in result:
                        fact = result.split("__SAVE_FACT__:")[1].strip()
                        self.memory.add_fact(user_id, fact)
                        result = f"Факт сохранён: {fact}"
                    tool_results.append(
                        ToolMessage(
                            content=result,
                            tool_call_id=tool_call_id,
                        )
                    )
                messages.extend(tool_results)
            # Если вышли из цикла — возвращаем последний ответ
            return messages[-1].content if hasattr(messages[-1], "content") else "⚠️ Не удалось получить ответ."
        except Exception as e:
            return f"⚠️ Ошибка агента: {str(e)}"
