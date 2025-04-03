from telegram import Update
from telegram.ext import CallbackContext
from telegram.constants import ParseMode  # Add this import
from telegram.helpers import escape_markdown
from database import user_db
import logging  # Add this import for logger

# Initialize logger
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    """Handles /start command with proper user tracking"""
    try:
        user = update.effective_user
        
        # Track user
        user_db.track_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Send welcome message
        await update.message.reply_text(
            f"👋 *Welcome* {escape_markdown(user.first_name or 'there')}!\n\n"
            "I can download Instagram content for you. Just send me a link!",
            parse_mode=ParseMode.MARKDOWN_V2  # Use the imported ParseMode
        )
        
    except Exception as e:
        logger.error(f"Start command error: {e}", exc_info=True)
        await update.message.reply_text("🚧 Bot is temporarily unavailable. Please try later.")