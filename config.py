import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# База данных (берем готовую строку из .env)
DATABASE_URL = os.getenv("DATABASE_URL")