from __future__ import annotations
from typing import Any, TYPE_CHECKING
from app.config import settings
from langchain_core.messages import HumanMessage, AIMessage

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

def _get_services(context: Any):
    from app.core.memory import DatabaseMemory
    from app.mcp.client import MCPClient
    from app.core.agent import TelegramAgent
    bot_data = context.application.bot_data
    if "memory" not in bot_data: bot_data["memory"] = DatabaseMemory()
    if "mcp_client" not in bot_data: bot_data["mcp_client"] = MCPClient()
    if "agent" not in bot_data:
        bot_data["agent"] = TelegramAgent(mcp_client=bot_data["mcp_client"], memory=bot_data["memory"])
    return bot_data["memory"], bot_data["mcp_client"], bot_data["agent"]

async def handle_message(update: Any, context: Any):
    memory, _, agent = _get_services(context)
    user_id = update.effective_user.id
    text = update.message.text
    if not text: return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Получаем историю и конвертируем для агента
        chat_history = []
        raw_history = memory.get_recent_history(user_id, limit=10)
        for msg in raw_history:
            if msg.role == "user": chat_history.append(HumanMessage(content=msg.content))
            else: chat_history.append(AIMessage(content=msg.content))

        response = await agent.process_message(user_id=user_id, message=text, chat_history=chat_history)
        
        # Сохраняем в историю
        memory.add_message(user_id, "user", text)
        memory.add_message(user_id, "assistant", response)

    except Exception as e:
        response = f"⚠️ Ошибка: {str(e)}"
    
    await update.message.reply_text(response)

# ... (остальные функции start, help, create_bot_app оставь без изменений)
