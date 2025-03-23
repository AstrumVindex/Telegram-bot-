import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackContext,
    CallbackQueryHandler, filters
)
from handlers.config import BOT_TOKEN  # Secure Import
from handlers.start import start
from handlers.messages import process_message
from handlers.errors import error_handler
from handlers.downloads import download_youtube, download_instagram, L
from handlers.mp3button import convert_instagram_to_mp3  # MP3 Conversion

# ✅ Logger Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ Initialize the Bot
TOKEN = BOT_TOKEN

# ✅ Admin User ID (Replace with your actual Telegram ID)
ADMIN_ID = 1262827267  

# ✅ File to Track Users
USER_TRACKING_FILE = "users.txt"

# ✅ Function to Track Users
def track_user(user_id: int):
    """Tracks users who interact with the bot."""
    try:
        with open(USER_TRACKING_FILE, "r") as file:
            users = file.read().splitlines()
    except FileNotFoundError:
        users = []

    if str(user_id) not in users:
        with open(USER_TRACKING_FILE, "a") as file:
            file.write(str(user_id) + "\n")

# ✅ Admin Command to Send User List
async def send_users(update: Update, context: CallbackContext):
    """Sends the list of tracked users to the admin."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    try:
        with open(USER_TRACKING_FILE, "r") as file:
            users = file.read()
        message = f"📜 User List:\n{users}" if users.strip() else "📂 No users have used the bot yet."
        await update.message.reply_text(message)
    except FileNotFoundError:
        await update.message.reply_text("📂 No users have used the bot yet.")

# ✅ MP3 Conversion Button Handler
async def handle_button_click(update: Update, context: CallbackContext):
    """Handles button clicks for MP3 conversion."""
    query = update.callback_query
    await query.answer()  # Acknowledge button click

    if query.data.startswith("convert_mp3:"):
        shortcode = query.data.split(":", 1)[1]  # Extract post shortcode
        media_path = f"downloads/{shortcode}.mp4"  # Correct path

        # ✅ Check if the video file exists
        if not os.path.exists(media_path):
            await query.message.reply_text("❌ Error: Video file not found!")
            return

        await query.edit_message_text("🎵 Converting video to MP3... Please wait... ⏳")
        mp3_link = await convert_instagram_to_mp3(media_path)  # Call Zamzar API

        if mp3_link.startswith("http"):
            await query.message.reply_audio(audio=mp3_link, caption="🎶 Here is your MP3 file!")
        else:
            await query.message.reply_text(mp3_link)  # Show error message

# ✅ Main Bot Function
def main():
    """Starts the Telegram bot."""
    application = Application.builder().token(TOKEN).build()

    # ✅ Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send_users", send_users))  # Admin-only command
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))
    application.add_handler(CommandHandler("download_youtube", download_youtube))
    application.add_handler(CommandHandler("youtube", lambda u, c: download_youtube(u, c, L)))
    application.add_handler(CommandHandler("instagram", lambda u, c: download_instagram(u, c, L)))
    application.add_handler(CallbackQueryHandler(handle_button_click))  # MP3 Button Handler

    # ✅ Start the bot
    application.run_polling(drop_pending_updates=True)

# ✅ Start the bot
if __name__ == "__main__":
    main()
