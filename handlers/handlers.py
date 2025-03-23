import re
from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters

# ✅ Define a pattern to detect valid URLs (Instagram, YouTube, etc.)
URL_PATTERN = re.compile(r"https?://[^\s]+")

async def handle_message(update: Update, context: CallbackContext):
    """Handles user messages & ignores random text (only processes links & commands)."""
    message_text = update.effective_message.text.strip()

    # ✅ Allow commands (messages starting with "/")
    if message_text.startswith("/"):
        return  # Commands will be handled elsewhere

    # ✅ Allow valid links (Instagram, YouTube, etc.)
    if URL_PATTERN.search(message_text):
        await update.message.reply_text(f"Processing link: {message_text}")  # Example response
        return  # Continue processing

    # ❌ Ignore all other random messages (no response)
    return  

# ✅ Add the handler in your bot setup
def setup_handlers(application):
    """Registers handlers for processing messages."""
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    application.add_handler(message_handler)



