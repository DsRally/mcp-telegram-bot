#!/bin/bash

# Запускаем MCP сервер в фоне
python -c "import uvicorn; uvicorn.run('app.mcp_servers.combined_server:app', host='0.0.0.0', port=8001)" &

# Ждём 5 секунд
sleep 5

# Запускаем главный сервер (занимает foreground)
uvicorn app.main:app --host 0.0.0.0 --port 8000