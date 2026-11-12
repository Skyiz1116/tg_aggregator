from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy import select, func
from config import ADMIN_IDS
from database.db_requests import get_messages_by_period, SessionLocal
from database.models import Message, Chat, User
import csv
import io

admin_router = Router()


@admin_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Я бот-агрегатор корпоративных переписок.\n\n"
        f"Команды:\n"
        f"/getchatid — ID текущего чата\n"
        f"/stats — статистика БД\n"
        f"/export <chat_id> <дни> — выгрузка CSV"
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
    args = message.text.split()
    if len(args) != 3:
        return await message.answer(
            "❌ Формат: /export [chat_id] [дни]\nПример: /export -100123456789 7"
        )
    try:
        chat_id = int(args[1])
        days = int(args[2])
    except ValueError:
        return await message.answer("❌ ID и дни должны быть числами!")

    await message.answer(f"⏳ Выгружаю чат {chat_id} за {days} дн...")

    messages = get_messages_by_period(chat_id, days)
    if not messages:
        return await message.answer("📭 Сообщений не найдено.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Дата", "ID", "Имя", "Тип", "Текст"])
    for msg, user in messages:
        writer.writerow([
            msg.date.strftime("%Y-%m-%d %H:%M:%S"),
            msg.user_id,
            user.first_name or "",
            msg.media_type,
            msg.text or ""
        ])
    output.seek(0)

    await message.answer_document(
        document=types.BufferedInputFile(
            output.getvalue().encode('utf-8'),
            filename=f"export_{chat_id}_{days}d.csv"
        ),
        caption=f"✅ Выгружено {len(messages)} сообщений."
    )