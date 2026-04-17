#!/usr/bin/env python3
"""
Запускает все сервисы: MCP-сервер + главный бот.
"""
import subprocess
import time
import sys
import os

# Переходим в папку app для правильных импортов
os.chdir(os.path.dirname(os.path.abspath(__file__)))

commands = [
    # MCP-сервер (запускаем из папки app)
    ["uvicorn", "mcp_servers.combined_server:app", "--host", "0.0.0.0", "--port", "8001"],
    # Главный сервер (с задержкой)
    ["sleep", "5"],
    ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
]

processes = []

for cmd in commands:
    if cmd[0] == "sleep":
        time.sleep(5)
        continue
    
    print(f"Запускаю: {' '.join(cmd)}")
    p = subprocess.Popen(cmd)
    processes.append(p)
    time.sleep(1)

print("Все серверы запущены!")
print("MCP: http://localhost:8001")
print("Главный: http://localhost:8000")

# Ждём главный сервер
processes[-1].wait()

# Убиваем MCP при остановке
for p in processes[:-1]:
    p.terminate()
    p.wait()
