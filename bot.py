import os
from pyrogram import Client, filters
from pymongo import MongoClient
from time import sleep

# Load environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client["file_search_db"]
collection = db["files"]

# Telegram Bot Client
bot = Client("file_search_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@bot.on_message(filters.document | filters.video | filters.audio)
async def save_file(client, message):
    """Save file details (caption + file_id) in the database."""
    file_caption = message.caption if message.caption else "No Caption"
    file_id = message.document.file_id if message.document else None

    if file_id:
        collection.insert_one({"file_id": file_id, "caption": file_caption})
        await message.reply_text(f"✅ File saved with caption: {file_caption}")


@bot.on_message(filters.text & filters.private)
async def search_file(client, message):
    """Search files by caption in the database and return matching files with button."""
    query = message.text
    result = collection.find_one({"caption": {"$regex": query, "$options": "i"}})

    if result:
        file_id = result["file_id"]
        await message.reply_document(
            file_id,
            caption=f"🎬 Found: {result['caption']}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 Visit Channel", url="https://t.me/CinemaMovieTimes")]]
            ),
        )
    else:
        await message.reply_text("❌ No files found for your query.")


if __name__ == "__main__":
    print("🚀 Bot is running...")
    bot.run()

    # Keep the process alive for Render
    while True:
        sleep(3600)
