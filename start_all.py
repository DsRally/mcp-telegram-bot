import subprocess
import time
import sys

commands = [
    # MCP-серверы
    ["uvicorn", "mcp_servers.weather_server:app", "--port", "8001"],
    ["uvicorn", "mcp_servers.currency_server:app", "--port", "8002"],
    ["uvicorn", "mcp_servers.search_server:app", "--port", "8003"],
    # Главный сервер (с задержкой)
    ["sleep", "3"] if sys.platform != "win32" else ["timeout", "/t", "3"],
    ["uvicorn", "app.main:app", "--reload"],
]

processes = []

for cmd in commands:
    if cmd[0] in ["sleep", "timeout"]:
        time.sleep(3)
        continue
    print(f"Запускаю: {' '.join(cmd)}")
    p = subprocess.Popen(cmd)
    processes.append(p)
    time.sleep(1)

print("Все серверы запущены!")
print("Погода: http://localhost:8001")
print("Валюты: http://localhost:8002")
print("Поиск: http://localhost:8003")
print("Главный: http://localhost:8000")

# Ждём завершения
for p in processes:
    p.wait()