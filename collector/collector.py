import os
import logging
from aiogram import Router, types
from database.db_requests import save_user, save_chat, save_message, save_reaction

collector_router = Router()
logger = logging.getLogger(__name__)


@collector_router.message()
async def process_message(message: types.Message):
    """Обработчик всех сообщений — сохраняет их в БД"""
    logger.debug(f"Обработка msg_id={message.message_id} в chat_id={message.chat.id}")
    
    try:
        save_user(message.from_user)
        save_chat(message.chat)

        media_type = "text"
        text = message.text
        file_id = None
        file_path = None

        if message.photo:
            media_type = "photo"
            text = message.caption or "[Фото]"
            file_id = message.photo[-1].file_id
            file = await message.bot.get_file(file_id)
            file_path = f"downloads/photo_{message.message_id}.jpg"
            os.makedirs("downloads", exist_ok=True)
            await message.bot.download_file(file.file_path, file_path)
            
        elif message.document:
            media_type = "document"
            text = message.caption or "[Документ]"
            file_id = message.document.file_id
            file = await message.bot.get_file(file_id)
            file_path = f"downloads/doc_{message.message_id}_{message.document.file_name}"
            os.makedirs("downloads", exist_ok=True)
            await message.bot.download_file(file.file_path, file_path)
            
        elif message.sticker:
            media_type = "sticker"
            text = "[Стикер]"
            file_id = message.sticker.file_id
            
        elif message.video:
            media_type = "video"
            text = message.caption or "[Видео]"
            file_id = message.video.file_id
            file = await message.bot.get_file(file_id)
            file_path = f"downloads/video_{message.message_id}.mp4"
            os.makedirs("downloads", exist_ok=True)
            await message.bot.download_file(file.file_path, file_path)
            
        elif message.voice:
            media_type = "voice"
            text = "[Голосовое]"
            file_id = message.voice.file_id
            file = await message.bot.get_file(file_id)
            file_path = f"downloads/voice_{message.message_id}.ogg"
            os.makedirs("downloads", exist_ok=True)
            await message.bot.download_file(file.file_path, file_path)

        save_message(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            tg_message_id=message.message_id,
            text=text,
            date=message.date.replace(tzinfo=None),
            media_type=media_type,
            file_id=file_id,
            file_path=file_path
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении: {e}", exc_info=True)


@collector_router.edited_message()
async def process_edited_message(message: types.Message):
    """Обработка отредактированных сообщений — обновляет текст в БД"""
    try:
        from datetime import datetime as dt
        
        # Конвертируем edit_date: если int — превращаем в datetime
        if isinstance(message.edit_date, int):
            edit_date = dt.fromtimestamp(message.edit_date)
        else:
            edit_date = message.edit_date.replace(tzinfo=None) if message.edit_date else message.date.replace(tzinfo=None)
        
        save_message(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            tg_message_id=message.message_id,
            text=message.text or "[Сообщение изменено]",
            date=edit_date,
            media_type="text",
            file_id=None
        )
        logger.info(f"✏️ Обновлено msg_id={message.message_id}: '{message.text}'")
    except Exception as e:
        logger.error(f"Ошибка при редактировании: {e}", exc_info=True)

@collector_router.message_reaction()
async def process_reaction(update: types.MessageReactionUpdated):
    """Обработка реакций на сообщения"""
    try:
        logger.info(f"👍 ПРИШЛО Событие реакции: chat={update.chat.id}, msg={update.message_id}, new={update.new_reaction}")
        for reaction in update.new_reaction:
            if hasattr(reaction, 'emoji'):
                emoji = reaction.emoji
            elif hasattr(reaction, 'custom_emoji_id'):
                emoji = f"custom:{reaction.custom_emoji_id}"
            else:
                emoji = "unknown"
            
            save_reaction(
                chat_id=update.chat.id,
                tg_message_id=update.message_id,
                user_id=update.user.id if update.user else 0,
                reaction_emoji=emoji,
                date=update.date.replace(tzinfo=None)
            )
            logger.debug(f"Реакция: msg={update.message_id} emoji={emoji}")
    except Exception as e:
        logger.error(f"Ошибка обработки реакции: {e}")