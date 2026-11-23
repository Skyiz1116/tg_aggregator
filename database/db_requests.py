from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from config import DATABASE_URL
from .models import Base, User, Chat, Message
from aiogram import types

# Синхронный движок — стабильно работает на Windows
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Создание таблиц при первом запуске"""
    Base.metadata.create_all(bind=engine)


def save_user(user: types.User):
    with SessionLocal() as session:
        existing = session.get(User, user.id)
        if not existing:
            session.add(User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            ))
            session.commit()


def save_chat(chat: types.Chat):
    with SessionLocal() as session:
        existing = session.get(Chat, chat.id)
        if not existing:
            session.add(Chat(
                id=chat.id,
                title=chat.title,
                chat_type=chat.type
            ))
            session.commit()


def save_message(chat_id, user_id, tg_message_id, text, date, media_type, file_id=None, file_path=None):
    """Сохранить или обновить сообщение в БД"""
    from .models import Message
    
    with SessionLocal() as session:
        # Ищем сообщение по уникальной паре chat_id + tg_message_id
        existing = session.query(Message).filter_by(
            chat_id=chat_id,
            tg_message_id=tg_message_id
        ).first()
        
        if existing:
            # Если есть — обновляем (закрывает пункт 7 про редактирование)
            existing.text = text
            existing.media_type = media_type
            existing.file_id = file_id
            existing.file_path = file_path
            existing.date = date
        else:
            # Если нет — создаём новое
            session.add(Message(
                tg_message_id=tg_message_id,
                chat_id=chat_id,
                user_id=user_id,
                text=text,
                date=date,
                media_type=media_type,
                file_id=file_id,
                file_path=file_path
            ))
        session.commit()


def get_messages_by_period(chat_id: int, date_from: datetime, date_to: datetime):
    """Получить сообщения из чата за период [date_from, date_to)"""
    with SessionLocal() as session:
        query = (
            session.query(Message, User)
            .join(User, Message.user_id == User.id)
            .filter(
                Message.chat_id == chat_id,
                Message.date >= date_from,
                Message.date < date_to
            )
            .order_by(Message.date)
        )
        return query.all()


def save_reaction(chat_id, tg_message_id, user_id, reaction_emoji, date):
    """Сохранить или обновить реакцию на сообщение"""
    from .models import Reaction
    
    with SessionLocal() as session:
        existing = session.query(Reaction).filter_by(
            chat_id=chat_id,
            tg_message_id=tg_message_id,
            user_id=user_id
        ).first()
        
        if existing:
            existing.reaction_emoji = reaction_emoji
            existing.date = date
        else:
            session.add(Reaction(
                chat_id=chat_id,
                tg_message_id=tg_message_id,
                user_id=user_id,
                reaction_emoji=reaction_emoji,
                date=date
            ))
        session.commit()
    
def get_attachments_by_period(chat_id: int, date_from: datetime, date_to: datetime):
    """Получить вложения из чата за период"""
    with SessionLocal() as session:
        query = (
            session.query(Message, User)
            .join(User, Message.user_id == User.id)
            .filter(
                Message.chat_id == chat_id,
                Message.date >= date_from,
                Message.date < date_to,
                Message.media_type != "text",
                Message.file_path.isnot(None)
            )
            .order_by(Message.date)
        )
        return query.all()