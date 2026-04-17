from __future__ import annotations
import os
from dataclasses import dataclass

try:
    from pydantic_settings import BaseSettings
except ModuleNotFoundError:
    BaseSettings = None

def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    load_dotenv()

if BaseSettings is not None:
    class Settings(BaseSettings):
        telegram_bot_token: str = ""
        openai_api_key: str = ""
        database_url: str = "sqlite:///./bot.db"
        # URL для микросервисов MCP
        weather_service_url: str = "http://localhost:8001"
        currency_service_url: str = "http://localhost:8002"
        search_service_url: str = "http://localhost:8003"

        class Config:
            env_file = ".env"
    settings = Settings()
else:
    _maybe_load_dotenv()
    @dataclass(frozen=True)
    class Settings:
        telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        database_url: str = os.getenv("DATABASE_URL", "sqlite:///./bot.db")
        weather_service_url: str = os.getenv("WEATHER_SERVICE_URL", "http://localhost:8001")
        currency_service_url: str = os.getenv("CURRENCY_SERVICE_URL", "http://localhost:8002")
        search_service_url: str = os.getenv("SEARCH_SERVICE_URL", "http://localhost:8003")
    settings = Settings()
