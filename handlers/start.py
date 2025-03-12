from telegram import Update
from telegram.ext import CallbackContext
from handlers.rate_limiter import enforce_rate_limit  # ✅ Ensure Correct Import

async def start(update: Update, context: CallbackContext):
    if not await enforce_rate_limit(update, context):  # ✅ Apply Rate Limiter
        return
    await update.message.reply_text("Welcome! Send me an Instagram link to download media.")





