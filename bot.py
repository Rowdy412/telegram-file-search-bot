import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from urllib.parse import quote_plus

# Load environment variables
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
CHANNEL_USERNAME = "https://t.me/+mp-uMTEidL1mNDll"  # Replace with your channel username

# MongoDB connection
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.file_db
files_collection = db.files

# Pyrogram Bot
bot = Client(
    "file_search_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# /start command handler
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    welcome_text = (
        "👋 **Welcome to the File Search Bot!**\n\n"
        "🔍 **How to Use:**\n"
        "Send me any keyword, and I'll search files by caption from my database.\n\n"
        "📁 **Example:**\n"
        "_Send:_ `Avengers`\n"
        "_I'll reply with:_ 🎬 *Avengers: Endgame (2019)*\n\n"
        "👉 **Join our channel for more files:**"
    )
    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📺 Visit Channel", url=CHANNEL_LINK)]]
        )
    )

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

# Import all existing movies from the channel
@bot.on_message(filters.command("import_movies") & filters.private)
async def import_movies(client, message):
    await message.reply("⏳ Importing all movies from the channel... This may take a while.")
    total_imported = 0

    async for msg in bot.get_chat_history(CHANNEL_USERNAME, limit=0):
        if msg.document:
            file_caption = msg.caption or msg.document.file_name
            file_id = msg.document.file_id
            if not files_collection.find_one({"file_id": file_id}):
                files_collection.insert_one({"caption": file_caption, "file_id": file_id})
                total_imported += 1
                print(f"✅ Imported: {file_caption}")

    await message.reply(f"✅ Import completed! Total movies imported: {total_imported}")

# Run bot with polling
if __name__ == "__main__":
    print("🚀 Bot is running with polling on Railway...")
    bot.run()
