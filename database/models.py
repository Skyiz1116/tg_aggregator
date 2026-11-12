from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Таблица пользователей Telegram"""
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    messages = relationship("Message", back_populates="user")


class Chat(Base):
    """Таблица чатов"""
    __tablename__ = 'chats'
    
    id = Column(BigInteger, primary_key=True)
    title = Column(String, nullable=True)
    chat_type = Column(String, nullable=True)
    
    messages = relationship("Message", back_populates="chat")


class Message(Base):
    """Таблица сообщений"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_message_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, ForeignKey('chats.id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    text = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    media_type = Column(String, nullable=True)  # text, photo, document, sticker
    file_id = Column(String, nullable=True)
    
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="messages")