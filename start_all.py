#!/usr/bin/env python3
"""
Запускает все сервисы: MCP-сервер (combined) + главный бот.
"""
import subprocess
import time
import sys
import os

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

commands = [
    # MCP-сервер (объединённый) — запускаем первым
    [sys.executable, "-c", 
     "import uvicorn; uvicorn.run('app.mcp_servers.combined_server:app', host='0.0.0.0', port=8001)"],
    # Главный сервер (с задержкой)
    ["sleep", "5"],
    ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
]

processes = []

for cmd in commands:
    if cmd[0] in ["sleep", "timeout"]:
        time.sleep(5)
        continue
    
    print(f"Запускаю: {' '.join(cmd[:2])}...")  # Короткий вывод
    p = subprocess.Popen(cmd)
    processes.append(p)
    time.sleep(1)

print("Все серверы запущены!")
print("MCP сервер: http://localhost:8001")
print("Главный: http://localhost:8000")

# Ждём завершения главного сервера (последний в списке)
processes[-1].wait()

# При завершении убиваем MCP сервер
for p in processes[:-1]:
    p.terminate()
    p.wait()
