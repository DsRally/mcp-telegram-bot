import json
from app.db.database import SessionLocal
from app.db.models import User, Conversation, ChatHistory


class DatabaseMemory:
    def __init__(self):
        self.db = SessionLocal()
    
    def get_or_create_user(self, telegram_id: int, username: str = None, first_name: str = None):
        user = self.db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def add_fact(self, telegram_id: int, fact: str):
        user = self.db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if user:
            if user.facts is None or user.facts == "":
                facts_list = []
            else:
                facts_list = json.loads(user.facts)
            
            if fact not in facts_list:
                facts_list.append(fact)
                user.facts = json.dumps(facts_list)
                self.db.commit()
                self.db.refresh(user)
                return True
        
        return False
    
    def get_facts(self, telegram_id: int):
        user = self.db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if user and user.facts:
            return json.loads(user.facts)
        
        return []
    
    def save_conversation(self, telegram_id: int, message: str, response: str):
        conv = Conversation(
            user_id=telegram_id,
            message=message,
            response=response
        )
        self.db.add(conv)
        self.db.commit()

    def add_message(self, user_id: int, role: str, content: str):
        """Сохраняет сообщение в историю чата"""
        msg = ChatHistory(
            user_id=user_id,
            role=role,
            content=content
        )
        self.db.add(msg)
        self.db.commit()
    
    def get_recent_history(self, user_id: int, limit: int = 5):
        """Получает последние N сообщений"""
        from sqlalchemy import desc
        
        messages = self.db.query(ChatHistory)\
            .filter(ChatHistory.user_id == user_id)\
            .order_by(desc(ChatHistory.timestamp))\
            .limit(limit)\
            .all()
        
        # Возвращаем в хронологическом порядке (старые → новые)
        return list(reversed(messages))
    
    def get_context_string(self, user_id: int) -> str:
        """Формирует строку контекста для агента"""
        messages = self.get_recent_history(user_id, limit=5)
        if not messages:
            return ""
        
        context = "Недавний разговор:\n"
        for msg in messages:
            prefix = "Пользователь:" if msg.role == "user" else "Бот:"
            context += f"{prefix} {msg.content}\n"
        
        return context