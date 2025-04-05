import re
from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from models import Session, User, Activity
from datetime import datetime

# ✅ URL pattern
URL_PATTERN = re.compile(r"https?://[^\s]+")

# ✅ Add platform-specific matchers
INSTAGRAM_PATTERN = re.compile(r"(instagram\.com|instagr\.am)")
YOUTUBE_PATTERN = re.compile(r"(youtube\.com|youtu\.be)")

async def handle_message(update: Update, context: CallbackContext):
    """Handle messages with link detection, tracking, and intelligent routing."""
    message_text = update.effective_message.text.strip()
    user_id = update.effective_user.id
    username = update.effective_user.username or "NoUsername"

    # ✅ Track user
    session = Session()
    user = session.query(User).filter_by(telegram_id=user_id).first()
    if not user:
        user = User(telegram_id=user_id, username=username)
        session.add(user)
    else:
        user.last_seen = datetime.utcnow()
    session.commit()

    # ✅ Track activity
    def log_action(action_type, url=None):
        activity = Activity(telegram_id=user_id, action_type=action_type, target_url=url)
        session.add(activity)
        session.commit()

    # ✅ Skip commands
    if message_text.startswith("/"):
        session.close()
        return

    # ✅ Check for URLs
    if URL_PATTERN.search(message_text):
        # 🔍 Instagram
        if INSTAGRAM_PATTERN.search(message_text):
            await update.message.reply_text("📸 Instagram link detected! Processing...")
            log_action("InstagramLink", message_text)
            session.close()
            # Hand over to your Instagram download logic here
            return

        # 🔍 YouTube (not handled here)
        elif YOUTUBE_PATTERN.search(message_text):
            await update.message.reply_text(
                "📺 This is a YouTube link. Please use our YouTube bot instead:\n👉 @YourYouTubeBot"
            )
            log_action("WrongPlatform_YT", message_text)
            session.close()
            return

        # ❓ Other links
        else:
            await update.message.reply_text("🔗 Link detected, but not supported yet.")
            log_action("UnsupportedLink", message_text)
            session.close()
            return

    # ❌ Ignore all other messages
    session.close()
    return

# ✅ Register the handler
def setup_handlers(application):
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    application.add_handler(message_handler)
