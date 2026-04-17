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
        # Railway предоставляет DATABASE_URL автоматически для PostgreSQL
        # Если нет — fallback на SQLite для локальной разработки
        database_url: str = "sqlite:///./bot.db"
        
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
    
    settings = Settings()
else:
    _maybe_load_dotenv()
    
    @dataclass(frozen=True)
    class Settings:
        telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        database_url: str = os.getenv("DATABASE_URL", "sqlite:///./bot.db")
    
    settings = Settings()
