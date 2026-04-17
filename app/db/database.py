from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Определяем тип БД по URL
is_sqlite = settings.database_url.startswith("sqlite")

# Создаём движок БД
if is_sqlite:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL или другая БД (Railway)
    engine = create_engine(settings.database_url, echo=False)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

def init_db():
    """Создаёт таблицы при первом запуске"""
    try:
        # Импортируем модели здесь, чтобы избежать circular imports
        from app.db.models import User, Conversation, ChatHistory
        
        # Создаём все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Таблицы БД созданы/проверены")
        
        # Проверка — выведем список таблиц для PostgreSQL
        if not is_sqlite:
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            logger.info(f"📋 Таблицы в БД: {tables}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {e}")
        raise

def get_db():
    """Генератор для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
