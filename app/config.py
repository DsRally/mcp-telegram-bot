from __future__ import annotations

import os
from dataclasses import dataclass


try:
    from pydantic_settings import BaseSettings  # type: ignore
except ModuleNotFoundError:
    BaseSettings = None  # type: ignore


def _maybe_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except ModuleNotFoundError:
        return
    load_dotenv()


if BaseSettings is not None:

    class Settings(BaseSettings):
        telegram_bot_token: str = ""
        openai_api_key: str = ""
        weather_api_key: str = ""
        database_url: str = "sqlite:///./bot.db"

        class Config:
            env_file = ".env"


    settings = Settings()

else:
    _maybe_load_dotenv()

    @dataclass(frozen=True)
    class Settings:
        telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
        database_url: str = os.getenv("DATABASE_URL", "sqlite:///./bot.db")


    settings = Settings()