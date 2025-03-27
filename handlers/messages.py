from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from handlers.downloads import download_instagram, download_youtube
from handlers.rate_limiter import enforce_rate_limit  # ✅ Import rate limiter

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages from users and processes Instagram & YouTube downloads."""
    user_message = update.message.text.strip()

    if "instagram.com" in user_message:
        await download_instagram(update, context)  # ✅ Call Instagram download function

    elif "youtube.com" in user_message or "youtu.be" in user_message:
        # ✅ Pass update and context correctly
        await download_youtube(update, context)  

    else:
        await update.message.reply_text("⚠️ *Please send a valid Instagram or YouTube link.*", parse_mode=ParseMode.MARKDOWN)
