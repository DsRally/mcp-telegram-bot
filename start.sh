#!/bin/bash

# Простой запуск одного процесса на Railway
# Railway сама установит PORT переменную

echo "🚀 Запуск Telegram AI Agent..."

# Запускаем uvicorn на порту из переменной окружения (Railway) или 8000 (локально)
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
