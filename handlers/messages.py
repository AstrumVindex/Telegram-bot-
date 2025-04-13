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

    # ✅ Skip command messages (handled separately)
    if message_text.startswith("/"):
        return

    # ✅ Apply rate limiting
    if not await enforce_rate_limit(update, context):
        return

    # ✅ Match supported URLs
    match = URL_PATTERN.search(message_text)
    if match:
        url = match.group(0)

        if "instagram.com" in url:
            await download_instagram(update, context)
        elif "youtube.com" in url or "youtu.be" in url:
            await update.message.reply_text("📌 YouTube support is coming soon! Stay tuned.")
        else:
            await update.message.reply_text("⚠️ Unsupported link format.")

        return

    # ❌ Ignore unrelated messages (no reply)
    return
