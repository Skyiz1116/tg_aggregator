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


def save_message(chat_id, user_id, tg_message_id, text, date, media_type, file_id=None):
    with SessionLocal() as session:
        session.add(Message(
            tg_message_id=tg_message_id,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            date=date,
            media_type=media_type,
            file_id=file_id
        ))
        session.commit()


def get_messages_by_period(chat_id: int, days: int):
    """Получить сообщения из чата за последние N дней"""
    with SessionLocal() as session:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = (
            select(Message, User)
            .join(User, Message.user_id == User.id)
            .where(and_(Message.chat_id == chat_id, Message.date >= cutoff_date))
            .order_by(Message.date)
        )
        return session.execute(query).all()