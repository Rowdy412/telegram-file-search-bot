import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from urllib.parse import quote_plus
from fastapi import FastAPI, Request
import uvicorn

# Load environment variables safely
def get_env_var(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Environment variable {name} is missing.")
    return value

API_ID = int(get_env_var("API_ID"))
API_HASH = get_env_var("API_HASH")
BOT_TOKEN = get_env_var("BOT_TOKEN")
MONGO_USER = quote_plus(get_env_var("MONGO_USER"))
MONGO_PASS = quote_plus(get_env_var("MONGO_PASS"))
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cinejunkies.azgr3.mongodb.net/?retryWrites=true&w=majority&appName=cinejunkies"
CHANNEL_LINK = "https://t.me/CinemaMovieTimes"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://telegram-file-search-bot.onrender.com/")

# MongoDB Connection
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.file_db
files_collection = db.files

# FastAPI app (instead of Flask for async compatibility)
app = FastAPI()

# Pyrogram Bot Client
bot = Client(
    "file_search_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Endpoint for Telegram webhook
@app.post("/")
async def telegram_webhook(request: Request):
    update = await request.json()
    await bot.process_update(update)
    return {"status": "ok"}

# File saving handler
@bot.on_message(filters.channel & filters.document)
async def save_file(client, message):
    file_caption = message.caption or message.document.file_name
    file_id = message.document.file_id
    files_collection.insert_one({"caption": file_caption, "file_id": file_id})
    print(f"✅ Saved file with caption: {file_caption}")

# File searching handler
@bot.on_message(filters.private & filters.text)
async def search_file(client, message):
    query = message.text.strip()
    result = files_collection.find_one({"caption": {"$regex": query, "$options": "i"}})

    if result:
        await message.reply_document(
            result["file_id"],
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📺 Visit Channel", url=CHANNEL_LINK)]]
            )
        )
    else:
        await message.reply("❌ No file found with that name.")

# Async startup function
async def main():
    await bot.start()
    print(f"🚀 Bot running at {WEBHOOK_URL}")
    port = int(os.environ.get("PORT", 5000))
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
