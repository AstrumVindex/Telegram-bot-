from telegram import Update
from telegram.ext import CallbackContext
from handlers.rate_limiter import enforce_rate_limit
from database import user_db  # ✅ Import your database

async def start(update: Update, context: CallbackContext):
    if not await enforce_rate_limit(update, context):
        return

    user = update.effective_user

    # ✅ Track the user in the database
    try:
        user_db.track_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
    except Exception as e:
        print("❌ Error tracking user:", e)

    await update.message.reply_text("🎉 Welcome, Ready to get started?  Send me a link now!")
