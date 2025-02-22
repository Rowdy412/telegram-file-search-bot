from pyrogram import Client, filters
from pymongo import MongoClient
import os

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
CHANNEL_LINK = "https://t.me/CinemaMovieTimes"

bot = Client("file_search_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

client = MongoClient(MONGO_URI)
db = client["telegram_files"]
collection = db["files"]

@bot.on_message(filters.channel & filters.document)
async def save_file(client, message):
    file_caption = message.caption or message.document.file_name
    file_id = message.document.file_id
    collection.insert_one({"caption": file_caption, "file_id": file_id})
    print(f"Saved: {file_caption}")

@bot.on_message(filters.private & filters.text)
async def search_file(client, message):
    query = message.text
    result = collection.find_one({"caption": {"$regex": query, "$options": "i"}})
    if result:
        await message.reply_document(result["file_id"],
                                     reply_markup=InlineKeyboardMarkup(
                                         [[InlineKeyboardButton("📁 Visit Channel", url=CHANNEL_LINK)]]
                                     ))
    else:
        await message.reply("❌ File not found.")

bot.run()