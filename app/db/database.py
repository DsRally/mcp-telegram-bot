from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Создаём движок БД (подключение к файлу bot.db)
engine = create_engine(
    settings.database_url, 
    connect_args={"check_same_thread": False}  # Только для SQLite
)

# Фабрика сессий (создаёт "разговоры" с базой)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для таблиц
Base = declarative_base()

# Функция для получения сессии (будем использовать позже)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()