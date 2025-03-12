from telegram import Update
from telegram.ext import ContextTypes
from handlers.rate_limiter import enforce_rate_limit  # ✅ Import the rate limiter

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await enforce_rate_limit(update, context):  # ✅ Apply Rate Limiter
        return

    user_message = update.message.text
    if "instagram.com" in user_message:
        await update.message.reply_text("📥 Downloading your media...")
        # Call the download function here
    else:
        await update.message.reply_text("⚠️ Please send a valid Instagram link.")



