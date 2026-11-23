from aiogram import Router, types, F
from datetime import datetime, timedelta
from aiogram.filters import Command
from sqlalchemy import select, func
from config import ADMIN_IDS
from database.db_requests import get_messages_by_period, get_attachments_by_period, SessionLocal
from database.models import Message, Chat, User
import csv
import io
import os

admin_router = Router()


@admin_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Я бот-агрегатор корпоративных переписок.\n\n"
        f"Команды:\n"
        f"/getchatid — ID текущего чата\n"
        f"/stats — статистика БД\n"
        f"/export <chat_id> <дата_начала> <дата_конца> — выгрузка CSV\n"
        f"/export_media <chat_id> <дата_начала> <дата_конца> — выгрузка вложений"
    )


@admin_router.message(Command("getchatid"), F.from_user.id.in_(ADMIN_IDS))
async def get_chat_id(message: types.Message):
    await message.answer(
        f"🆔 ID этого чата: `{message.chat.id}`\n"
        f"👤 Твой ID: `{message.from_user.id}`",
        parse_mode="Markdown"
    )


@admin_router.message(Command("stats"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_stats(message: types.Message):
    with SessionLocal() as session:
        chats = session.execute(select(func.count(Chat.id))).scalar()
        users = session.execute(select(func.count(User.id))).scalar()
        msgs = session.execute(select(func.count(Message.id))).scalar()
    await message.answer(
        f"📊 Статистика:\n"
        f"• Чатов: {chats}\n"
        f"• Пользователей: {users}\n"
        f"• Сообщений: {msgs}"
    )


@admin_router.message(Command("export"), F.from_user.id.in_(ADMIN_IDS))
async def export_data(message: types.Message):
    # ПУНКТ 1: Только в личном чате
    if message.chat.type != "private":
        return await message.answer(
            "⚠️ Команда /export работает только в личных сообщениях с ботом."
        )
    
    args = message.text.split()
    # ПУНКТ 4: Период по датам
    if len(args) != 4:
        return await message.answer(
            "❌ Формат: /export <chat_id> <дата_начала> <дата_конца>\n"
            "Пример: /export -4955706149 2026-11-01 2026-11-30"
        )
    
    try:
        chat_id = int(args[1])
        date_from = datetime.strptime(args[2], "%Y-%m-%d")
        date_to = datetime.strptime(args[3], "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        return await message.answer("❌ Неверный формат. Даты должны быть в формате YYYY-MM-DD")

    await message.answer(f"⏳ Выгружаю чат {chat_id} с {args[2]} по {args[3]}...")

    messages = get_messages_by_period(chat_id, date_from, date_to)
    if not messages:
        return await message.answer("📭 Сообщений за этот период не найдено.")

    output = io.StringIO()
    writer = csv.writer(output)
    # ПУНКТ 3: добавили File ID и File Path в выгрузку
    writer.writerow(["Дата", "ID пользователя", "Имя", "Тип", "Текст", "File ID", "File Path"])
    
    for msg, user in messages:
        writer.writerow([
            msg.date.strftime("%Y-%m-%d %H:%M:%S"),
            msg.user_id,
            user.first_name or "",
            msg.media_type,
            msg.text or "",
            msg.file_id or "",
            msg.file_path or ""  # ← ДОБАВЛЕНО
        ])
    output.seek(0)

    await message.answer_document(
        document=types.BufferedInputFile(
            output.getvalue().encode('utf-8'),
            filename=f"export_{chat_id}_{args[2]}_{args[3]}.csv"
        ),
        caption=f"✅ Выгружено {len(messages)} сообщений."
    )


# ПУНКТ 3: Новая команда для экспорта вложений
@admin_router.message(Command("export_media"), F.from_user.id.in_(ADMIN_IDS))
async def export_media(message: types.Message):
    """Экспорт вложений за период"""
    if message.chat.type != "private":
        return await message.answer("⚠️ Только в личных сообщениях.")
    
    args = message.text.split()
    if len(args) != 4:
        return await message.answer(
            "❌ Формат: /export_media <chat_id> <дата_начала> <дата_конца>\n"
            "Пример: /export_media -4955706149 2026-11-01 2026-11-30"
        )
    
    try:
        chat_id = int(args[1])
        date_from = datetime.strptime(args[2], "%Y-%m-%d")
        date_to = datetime.strptime(args[3], "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        return await message.answer("❌ Неверный формат дат")

    await message.answer(f"⏳ Ищу вложения в чате {chat_id} с {args[2]} по {args[3]}...")

    attachments = get_attachments_by_period(chat_id, date_from, date_to)
    if not attachments:
        return await message.answer("📭 Вложений не найдено.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Дата", "Тип", "Имя пользователя", "Текст", "File ID", "Путь к файлу"])
    for msg, user in attachments:
        writer.writerow([
            msg.date.strftime("%Y-%m-%d %H:%M:%S"),
            msg.media_type,
            user.first_name or "",
            msg.text or "",
            msg.file_id or "",
            msg.file_path or ""
        ])
    output.seek(0)

    await message.answer_document(
        document=types.BufferedInputFile(
            output.getvalue().encode('utf-8'),
            filename=f"media_{chat_id}_{args[2]}_{args[3]}.csv"
        ),
        caption=f"✅ Найдено {len(attachments)} вложений. Файлы лежат в папке downloads/"
    )