from __future__ import annotations
from typing import Any, TYPE_CHECKING
from app.config import settings
from langchain_core.messages import HumanMessage, AIMessage
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import logging

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def _get_services(context: Any):
    """Lazy initialization сервисов"""
    from app.core.memory import DatabaseMemory
    from app.mcp.client import MCPClient
    from app.core.agent import TelegramAgent
    
    bot_data = context.application.bot_data
    
    if "memory" not in bot_data:
        bot_data["memory"] = DatabaseMemory()
        logger.info("🧠 Memory инициализирована")
    
    if "mcp_client" not in bot_data:
        bot_data["mcp_client"] = MCPClient()
        logger.info("🔧 MCP Client инициализирован")
    
    if "agent" not in bot_data:
        bot_data["agent"] = TelegramAgent(
            mcp_client=bot_data["mcp_client"],
            memory=bot_data["memory"]
        )
        logger.info("🤖 Agent инициализирован")
    
    return bot_data["memory"], bot_data["mcp_client"], bot_data["agent"]


async def start(update: Any, context: Any):
    """Ответ на команду /start"""
    user = update.effective_user
    memory, _, _ = _get_services(context)
    
    # Создаём/получаем пользователя в БД
    memory.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name or 'друг'}! Я твой AI-ассистент.\n\n"
        f"Я умею:\n"
        f"🌤 Проверять погоду — спроси 'Какая погода в Москве?'\n"
        f"💱 Узнавать курсы валют — спроси 'Курс доллара'\n"
        f"🔍 Искать информацию — спроси что угодно!\n\n"
        f"Просто напиши мне, и я помогу 😊"
    )


async def help_command(update: Any, context: Any):
    """Ответ на команду /help"""
    await update.message.reply_text(
        "ℹ️ Как со мной общаться:\n\n"
        "• Погода: 'Какая погода в Лондоне?'\n"
        "• Валюта: 'Курс евро', 'Сколько стоит доллар?'\n"
        "• Поиск: 'Найди рецепт пасты', 'Кто такой Илон Маск?'\n"
        "• Личные данные: 'Меня зовут Анна' — я запомню!\n\n"
        "Команды:\n"
        "/start — Начать\n"
        "/help — Помощь"
    )


async def handle_message(update: Any, context: Any):
    """Основной обработчик текстовых сообщений"""
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    memory, _, agent = _get_services(context)
    user_id = user.id
    text = update.message.text
    
    logger.info(f"💬 Сообщение от {user_id} (@{user.username}): {text[:50]}...")
    
    # Показываем статус "печатает"
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action="typing"
    )
    
    try:
        # Создаём пользователя если новый
        memory.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
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
        
        logger.info(f"✅ Ответ отправлен: {response[:50]}...")
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}")
        response = f"⚠️ Произошла ошибка. Попробуй ещё раз позже."
    
    await update.message.reply_text(response)


def create_bot_app():
    """Создаёт и настраивает приложение бота"""
    if not settings.telegram_bot_token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в настройках!")
    
    if not settings.openai_api_key:
        raise ValueError("❌ OPENAI_API_KEY не найден в настройках!")
    
    logger.info("🤖 Создаю Telegram бота...")
    
    # Создаём приложение бота
    application = ApplicationBuilder().token(settings.telegram_bot_token).build()
    
    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Регистрируем обработку текста (важно: фильтруем команды)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    logger.info("✅ Бот настроен")
    return application
