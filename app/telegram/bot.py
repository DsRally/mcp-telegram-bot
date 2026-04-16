from __future__ import annotations
from typing import Any, TYPE_CHECKING
from app.config import settings

# Импортируем типы для аннотаций
if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes
    from app.core.memory import DatabaseMemory
    from app.mcp.client import MCPClient
    from app.core.agent import TelegramAgent

def _get_services(context: Any):
    """Ленивая инициализация сервисов в bot_data"""
    from app.core.memory import DatabaseMemory
    from app.mcp.client import MCPClient
    from app.core.agent import TelegramAgent

    bot_data = context.application.bot_data

    # 1. Инициализируем Память (БД)
    if "memory" not in bot_data:
        bot_data["memory"] = DatabaseMemory()

    # 2. Инициализируем MCP клиент (Погода, Валюты, Поиск)
    if "mcp_client" not in bot_data:
        bot_data["mcp_client"] = MCPClient()

    # 3. Инициализируем LangChain Агента
    if "agent" not in bot_data:
        # Передаем оба требуемых аргумента
        bot_data["agent"] = TelegramAgent(
            mcp_client=bot_data["mcp_client"], 
            memory=bot_data["memory"]
        )

    return bot_data["memory"], bot_data["mcp_client"], bot_data["agent"]


async def start_command(update: Any, context: Any):
    """Команда /start"""
    memory, _, _ = _get_services(context)
    user = update.effective_user
    
    # Создаем пользователя в БД, если его нет
    memory.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n"
        f"Я умный агент на базе LangChain. Я могу искать информацию, узнавать погоду и запоминать важные факты о тебе. Просто напиши мне!"
    )


async def help_command(update: Any, context: Any):
    """Команда /help"""
    await update.message.reply_text(
        "🤖 **Доступные команды:**\n"
        "/start — Перезапустить бота\n"
        "/facts — Показать всё, что я о тебе запомнил\n"
        "/help — Справка\n\n"
        "Просто общайся со мной обычным текстом, и я постараюсь помочь!"
    )


async def facts_command(update: Any, context: Any):
    """Показать сохраненные факты"""
    memory, _, _ = _get_services(context)
    user_id = update.effective_user.id
    facts = memory.get_facts(user_id)
    
    if facts:
        text = "🧠 **Вот что я о тебе знаю:**\n" + "\n".join([f"• {f}" for f in facts])
    else:
        text = "🤔 Я пока ничего не запомнил. Расскажи мне что-нибудь о себе!"
    
    await update.message.reply_text(text)


async def handle_message(update: Any, context: Any):
    """Главный обработчик сообщений через LangChain"""
    memory, _, agent = _get_services(context)
    user_id = update.effective_user.id
    text = update.message.text
    
    if not text:
        return

    # Отображаем статус "печатает", пока ИИ думает (особенно полезно для поиска)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # 1. Получаем историю (LangChain ожидает список кортежей или объектов сообщений)
        # В твоем случае DatabaseMemory должен возвращать историю
        history_objs = memory.get_facts(user_id) # Или метод получения истории диалога
        
        # 2. Обрабатываем сообщение через агента
        # Мы передаем историю как список, агент сам преобразует её в промпт
        response = await agent.process_message(
            user_id=user_id, 
            message=text, 
            chat_history=[] # Здесь можно передать историю в формате LangChain
        )
        
        # 3. Сохраняем диалог в БД (если есть такие методы в memory)
        if hasattr(memory, 'save_conversation'):
            memory.save_conversation(user_id, text, response)

    except Exception as e:
        response = f"⚠️ Ошибка: {str(e)}"
    
    await update.message.reply_text(response)


def create_bot_app():
    """Создаёт и настраивает приложение бота"""
    try:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Установите библиотеку: pip install python-telegram-bot")

    # Собираем приложение
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Регистрация команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("facts", facts_command))
    
    # Обработка обычного текста
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application