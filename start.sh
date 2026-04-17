#!/bin/bash

# Запускаем MCP сервер в фоне на порту 8001
python -c "import uvicorn; uvicorn.run('app.mcp_servers.combined_server:app', host='0.0.0.0', port=8001)" &

# Ждём 5 секунд пока он стартует
sleep 5

# Запускаем главный сервер на порту 8000 (foreground)
uvicorn app.main:app --host 0.0.0.0 --port 8000
