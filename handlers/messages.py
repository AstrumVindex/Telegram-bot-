import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from handlers.downloads import download_instagram
from handlers.rate_limiter import enforce_rate_limit

# ✅ Pattern to detect Instagram/YouTube links
URL_PATTERN = re.compile(r"(https?://(?:www\.)?(instagram\.com|youtu\.be|youtube\.com)/[^\s]+)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user messages: processes Instagram/YouTube links and ignores random text."""
    message_text = update.effective_message.text.strip()

    # ✅ Allow commands to be handled elsewhere
    if message_text.startswith("/"):
        return

    # ✅ Enforce rate limit
    if not await enforce_rate_limit(update, context):
        return

    # ✅ Match Instagram or YouTube links
    match = URL_PATTERN.search(message_text)
    if match:
        if "instagram.com" in message_text:
            await download_instagram(update, context)
        else:
            await update.message.reply_text("⚠️ Only Instagram links are supported right now.")
        return

    # ❌ Ignore all other text (no reply)
    return
