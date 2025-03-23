import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackContext, filters
)
from telegram.ext import CallbackQueryHandler
from handlers.config import BOT_TOKEN  # Secure Import
from telegram import Update
from telegram.ext import ContextTypes
from handlers.downloads import download_instagram, download_youtube
from handlers.rate_limiter import enforce_rate_limit  # Import rate limiter
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
        instagram_url = query.data.split(":", 1)[1]  # Extract Instagram URL

        # ✅ Instead of editing, send a new message to prevent "no text to edit" error
        status_message = await query.message.reply_text("🎵 Converting video to MP3... Please wait... ⏳")

        # ✅ Call the Zamzar MP3 conversion function
        mp3_link = await convert_instagram_to_mp3(instagram_url)

        # ✅ Send the MP3 file or error message
        if mp3_link.startswith("http"):
            await status_message.delete()  # ✅ Delete status message if conversion is successful
            await query.message.reply_audio(audio=mp3_link, caption="🎶 Here is your MP3 file!")
        else:
            await status_message.edit_text(mp3_link)  # ✅ Update message with error info

#rate limiter

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages from users and processes Instagram & YouTube downloads."""
    # Enforce rate limit
    if not await enforce_rate_limit(update, context):
        return  # Stop processing if the user is rate-limited

    user_message = update.message.text.strip()

    if "instagram.com" in user_message:
        await download_instagram(update, context)  # Call Instagram download function

    elif "youtube.com" in user_message or "youtu.be" in user_message:
        video_info = await download_youtube(user_message)  # Call YouTube download function

        if video_info and "download_link" in video_info:
            video_link = video_info["download_link"]
            await update.message.reply_text(f"✅ *Download Link:* [Click Here]({video_link})")
        else:
            await update.message.reply_text("❌ *Error:* Failed to fetch YouTube video.\nPlease check the link and try again.")

    else:
        await update.message.reply_text("⚠️ *Please send a valid Instagram or YouTube link.*")



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
