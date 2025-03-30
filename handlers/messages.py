from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from handlers.downloads import download_instagram
from handlers.rate_limiter import enforce_rate_limit  # ✅ Import rate limiter

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages from users and processes Instagram downloads."""
    user_message = update.message.text.strip()

    # ✅ Enforce rate limiting (if enabled)
    if not await enforce_rate_limit(update, context):
        return  # Stop if rate limit is exceeded

    if "instagram.com" in user_message:
        await download_instagram(update, context)  # ✅ Call Instagram download function

    else:
        await update.message.reply_text(
            "⚠️ *Please send a valid Instagram link.*", parse_mode=ParseMode.MARKDOWN
        )
