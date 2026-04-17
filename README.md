# 🤖 Telegram AI Agent

AI-ассистент в Telegram с интеллектуальными инструментами. Бот использует LangChain + OpenRouter (Gemini) для обработки запросов и сохраняет контекст разговора в PostgreSQL.

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 🌤 **Погода** | Актуальная погода в любом городе (OpenWeatherMap API) |
| 💱 **Курсы валют** | Конвертация USD, EUR, RUB и других валют |
| 🔍 **Поиск** | Поиск информации через Wikipedia |
| 🧠 **Память** | Запоминает факты о пользователе (имя, предпочтения) |
| 💬 **История** | Сохраняет контекст последних 10 сообщений |

## 🚀 Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone https://github.com/your-username/telegram-ai-agent.git
cd telegram-ai-agent
2. Настрой переменные окружения
Создай .env файл:
env
Copy
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openrouter_api_key
WEATHER_API_KEY=your_openweathermap_api_key
DATABASE_URL=sqlite:///./bot.db
Где получить ключи:
Telegram BotFather — TELEGRAM_BOT_TOKEN
OpenRouter — OPENAI_API_KEY (используем Gemini)
OpenWeatherMap — WEATHER_API_KEY (бесплатно)
3. Запусти локально
bash
Copy
pip install -r requirements.txt
uvicorn app.main:app --reload
🚂 Деплой на Railway
Автоматический деплой
Форкни этот репозиторий
Подключи Railway к GitHub
Добавь переменные окружения в Railway Dashboard
Добавь PostgreSQL сервис (Railway создаст DATABASE_URL автоматически)
Вручную
bash
Copy
railway login
railway link
railway up
📁 Структура проекта
plain
Copy
telegram-ai-agent/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Агент и память
│   │   ├── agent.py      # LangChain агент
│   │   └── memory.py     # Работа с БД
│   ├── db/               # Модели и подключение
│   │   ├── database.py
│   │   └── models.py
│   ├── mcp/              # Инструменты (погода, валюты, поиск)
│   │   ├── tools.py
│   │   └── client.py
│   ├── telegram/         # Telegram бот
│   │   └── bot.py
│   ├── config.py         # Настройки
│   └── main.py           # Точка входа (FastAPI)
├── requirements.txt
├── Procfile
└── start.sh
🛠 Технологии
Python 3.12
FastAPI — веб-фреймворк
python-telegram-bot — интеграция с Telegram
LangChain 0.3.x — LLM и tool-calling
OpenRouter — доступ к Gemini/Claude/GPT
SQLAlchemy + PostgreSQL — персистентность
Railway — хостинг
💡 Примеры использования
Table
Запрос	Действие бота
"Какая погода в Париже?"	Вызывает get_weather → показывает температуру, влажность, ветер
"Курс доллара к евро"	Вызывает get_currency → конвертирует валюты
"Что такое квантовая физика?"	Вызывает web_search → ищет в Wikipedia
"Меня зовут Алекс"	Вызывает save_user_fact → запоминает имя
"Как меня зовут?"	Использует сохранённые факты из БД
🔧 Переменные окружения
Table
Переменная	Обязательная	Описание
TELEGRAM_BOT_TOKEN	✅	Токен бота от @BotFather
OPENAI_API_KEY	✅	Ключ OpenRouter (или OpenAI)
DATABASE_URL	✅	PostgreSQL/SQLite строка подключения
WEATHER_API_KEY	❌	OpenWeatherMap API (без него погода примерная)
PORT	❌	Устанавливается Railway автоматически
📝 Логирование
Бот логирует все действия:
Инициализация сервисов
Вызовы инструментов (погода, валюты)
Сохранение фактов в БД
Ошибки API
🤝 Лицензия
MIT License — свободное использование и модификация.
