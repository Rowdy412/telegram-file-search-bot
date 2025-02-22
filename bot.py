from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import os

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = os.environ.get("MONGO_URI", "")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "")

bot = Client(
    "file_search_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

client = MongoClient(MONGO_URI)
db = client["file_search_bot"]
movies_collection = db["movies"]

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    await message.reply_text(
        "👋 Welcome to the File Search Bot!\n\n"
        "🔍 *How to Use:*\n"
        "Send me any keyword, and I'll search files by caption from my database.\n\n"
        "📁 *Example:*\n"
        "_Send:_ Avengers\n"
        "_I'll reply with:_ 🎬 *Avengers: Endgame (2019)*\n\n"
        "👉 Join our channel for more files: @{}".format(CHANNEL_USERNAME),
        parse_mode="markdown"
    )

@bot.on_message(filters.command("import_movies") & filters.private)
async def import_movies(client, message: Message):
    await message.reply("⏳ Importing movies from the channel...")
    try:
        async for msg in client.get_chat_history(CHANNEL_USERNAME, limit=0):
            if msg.document:
                movie_data = {
                    "file_id": msg.document.file_id,
                    "file_name": msg.document.file_name,
                    "file_size": msg.document.file_size,
                    "caption": msg.caption or ""
                }
                if not movies_collection.find_one({"file_id": msg.document.file_id}):
                    movies_collection.insert_one(movie_data)
        await message.reply("✅ Movies imported successfully!")
    except Exception as e:
        await message.reply(f"❌ Error while importing: {e}")

@bot.on_message(filters.text & filters.private)
async def search_file(client, message: Message):
    query = message.text.strip()
    result = movies_collection.find_one({"caption": {"$regex": query, "$options": "i"}})
    if result:
        await message.reply_document(
            document=result["file_id"],
            caption=f"🎬 *{result['file_name']}*\n💾 Size: {round(result['file_size']/1024/1024, 2)} MB",
            parse_mode="markdown"
        )
    else:
        await message.reply("😔 No file found with that name. Try another keyword.")

if __name__ == "__main__":
    print("🚀 Bot is running with polling on Railway...")
    bot.run()
