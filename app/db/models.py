from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger
from app.db.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    facts = Column(Text, default="[]")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    message = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
  
class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    role = Column(String(20))  # "user" или "assistant"
    content = Column(Text)     # Текст сообщения
    timestamp = Column(DateTime, default=datetime.utcnow)