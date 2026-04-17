from __future__ import annotations
from typing import Any, TYPE_CHECKING
from app.config import settings
from langchain_core.messages import HumanMessage, AIMessage
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

def _get_services(context: Any):
    from app.core.memory import DatabaseMemory
    from app.mcp.client import MCPClient
    from app.core.agent import TelegramAgent
    
    bot_data = context.application.bot_data
    if "memory" not in bot_data: 
        bot_data["memory"] = DatabaseMemory()
    if "mcp_client" not in bot_data: 
        bot_data["mcp_client"] = MCPClient()
    if "agent" not in bot_data:
        bot_data["agent"] = TelegramAgent(
            mcp_client=bot_data["mcp_client"], 
            memory=bot_data["memory"]
        )
    return bot_data["memory"], bot_data["mcp_client"], bot_data["agent"]

async def start(update: Any, context: Any):
    """Ответ на команду /start"""
    await update.message.reply_text(
        "Привет! Я твой AI-ассистент. Я умею проверять погоду, курс валют и искать информацию. Чем помочь?"
    )

async def help_command(update: Any, context: Any):
    """Ответ на команду /help"""
    await update.message.reply_text(
        "Просто напиши мне вопрос, например:\n"
        "- Какая погода в Харькове?\n"
        "- Какой курс доллара?\n"
        "- Найди последние новости о космосе."
    )

async def handle_message(update: Any, context: Any):
    """Основной обработчик текстовых сообщений"""
    if not update.message or not update.message.text:
        return

    memory, _, agent = _get_services(context)
    user_id = update.effective_user.id
    text = update.message.text

    # Показываем статус "печатает"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Получаем историю и конвертируем для агента
        chat_history = []
        raw_history = memory.get_recent_history(user_id, limit=10)
        for msg in raw_history:
            if msg.role == "user": 
                chat_history.append(HumanMessage(content=msg.content))
            else: 
                chat_history.append(AIMessage(content=msg.content))

        # Запрос к агенту (мозгу)
        response = await agent.process_message(
            user_id=user_id, 
            message=text, 
            chat_history=chat_history
        )
        
        # Сохраняем в историю
        memory.add_message(user_id, "user", text)
        memory.add_message(user_id, "assistant", response)

    except Exception as e:
        response = f"⚠️ Ошибка: {str(e)}"
    
    await update.message.reply_text(response)

def create_bot_app():
    """Эта функция вызывается в main.py для запуска бота"""
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в настройках!")

    # Создаем приложение бота
    application = ApplicationBuilder().token(settings.telegram_bot_token).build()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрируем обработку текста (важно: фильтруем команды)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application
