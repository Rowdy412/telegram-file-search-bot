import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from urllib.parse import quote_plus
from flask import Flask, request, jsonify
import threading

# Load environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_USER = quote_plus(os.getenv("MONGO_USER"))
MONGO_PASS = quote_plus(os.getenv("MONGO_PASS"))
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cinejunkies.azgr3.mongodb.net/?retryWrites=true&w=majority&appName=cinejunkies"
CHANNEL_LINK = "https://t.me/CinemaMovieTimes"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-render-url.onrender.com/")

# MongoDB Connection
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.file_db
files_collection = db.files

# Initialize Flask App for Webhook
app = Flask(__name__)

# Initialize Pyrogram Bot
bot = Client(
    "file_search_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Webhook endpoint for Telegram
@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    if update:
        bot.process_update(update)
    return jsonify({"status": "ok"}), 200

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

# Run bot and Flask server simultaneously
def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
