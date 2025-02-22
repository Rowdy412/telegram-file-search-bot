import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from urllib.parse import quote_plus
from flask import Flask, request

# Load environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_USER = quote_plus(os.getenv("MONGO_USER"))
MONGO_PASS = quote_plus(os.getenv("MONGO_PASS"))
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cinejunkies.azgr3.mongodb.net/?retryWrites=true&w=majority&appName=cinejunkies"

# MongoDB Connection
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.file_db
files_collection = db.files

# Flask App for Webhook
app = Flask(__name__)

# Pyrogram Bot Instance
bot = Client(
    "file_search_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Webhook route for Telegram updates
@app.route("/", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = request.get_json()
        bot.process_update(update)
        return "", 200

# Handler for search queries
@bot.on_message(filters.text & filters.private)
async def search_file(client, message):
    query = message.text.strip()
    result = files_collection.find_one({"caption": {"$regex": query, "$options": "i"}})

    if result:
        file_name = result.get("caption", "File")
        file_link = f"https://t.me/CinemaMovieTimes/{result.get('message_id')}"
        await message.reply(
            f"**{file_name}**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Watch Now 🍿", url=file_link)]]
            )
        )
    else:
        await message.reply("⚠️ No file found with that name.")

if __name__ == "__main__":
    # Set webhook URL from environment or default
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-render-url.onrender.com/")
    bot.run()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
