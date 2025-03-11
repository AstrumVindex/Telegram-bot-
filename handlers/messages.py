from telegram import Update
from telegram.ext import ContextTypes

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if "instagram.com" in user_message:
        await update.message.reply_text("📥 Downloading your media...")
        # Call the download function here
    else:
        await update.message.reply_text("⚠️ Please send a valid Instagram link.")
