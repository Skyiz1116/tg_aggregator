import logging
from aiogram import Router, types
from database.db_requests import save_user, save_chat, save_message

collector_router = Router()
logger = logging.getLogger(__name__)


@collector_router.message()
async def process_message(message: types.Message):
    """Обработчик всех сообщений — сохраняет их в БД"""
    # Логируем каждое сообщение
    logger.info(f"📨 Получено сообщение: chat_id={message.chat.id}, text={message.text}, type={message.content_type}")
    
    try:
        save_user(message.from_user)
        logger.info(f"✅ Пользователь {message.from_user.id} сохранён")
        
        save_chat(message.chat)
        logger.info(f"✅ Чат {message.chat.id} сохранён")

        media_type = "text"
        text = message.text
        file_id = None

        if message.photo:
            media_type = "photo"
            text = message.caption or "[Фото]"
            file_id = message.photo[-1].file_id
        elif message.document:
            media_type = "document"
            text = message.caption or "[Документ]"
            file_id = message.document.file_id
        elif message.sticker:
            media_type = "sticker"
            text = "[Стикер]"
            file_id = message.sticker.file_id
        elif message.video:
            media_type = "video"
            text = message.caption or "[Видео]"
            file_id = message.video.file_id
        elif message.voice:
            media_type = "voice"
            text = "[Голосовое]"
            file_id = message.voice.file_id

        save_message(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            tg_message_id=message.message_id,
            text=text,
            date=message.date.replace(tzinfo=None),
            media_type=media_type,
            file_id=file_id
        )
        logger.info(f"✅ Сообщение сохранено в БД: {text}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении: {e}", exc_info=True)