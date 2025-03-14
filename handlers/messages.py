from telegram import Update
from telegram.ext import CallbackContext
from handlers.downloads import download_instagram, download_youtube
from handlers.rate_limiter import enforce_rate_limit  # ✅ Import rate limiter

async def process_message(update: Update, context: CallbackContext):
    if not await enforce_rate_limit(update, context):  # ✅ Apply rate limit
        return

    user_message = update.message.text

    if "instagram.com" in user_message.lower():
        await update.message.reply_text("📥 Downloading Instagram media...")
        await download_instagram(update, context)
    elif "youtube.com" in user_message.lower() or "youtu.be" in user_message.lower():
        await update.message.reply_text("📥 Downloading YouTube video...")
        await download_youtube(update, context)
    else:
        await update.message.reply_text("⚠️ Please send a valid Instagram or YouTube link.")
