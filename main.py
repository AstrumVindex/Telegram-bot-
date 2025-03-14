import logging
import re
import asyncio
from instaloader import Instaloader, Post
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from handlers.config import BOT_TOKEN # ✅ Secure Import
from handlers.start import start
from handlers.messages import process_message
from handlers.errors import error_handler
from handlers.downloads import download_youtube
from handlers.downloads import download_youtube, download_instagram, L
 # Import Instaloader instance
import sys
sys.path.append("handlers")
from handlers.rate_limiter import enforce_rate_limit

# Logger Setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Instaloader

TOKEN = BOT_TOKEN  # Use the secure token

# Admin User ID (Replace with your actual Telegram numeric ID)
ADMIN_ID = 1262827267  # Change this to your Telegram user ID

# File to store user IDs
USER_TRACKING_FILE = "users.txt"

# Function to track users
def track_user(user_id: int):
    """Track users who use the bot."""
    try:
        # Load existing users
        with open(USER_TRACKING_FILE, "r") as file:
            users = file.read().splitlines()
    except FileNotFoundError:
        users = []

    # Add user if not already tracked
    if str(user_id) not in users:
        with open(USER_TRACKING_FILE, "a") as file:
            file.write(str(user_id) + "\n")

# Function to send user list (Admin only)
async def send_users(update: Update, context: CallbackContext):
    """Send the list of tracked users to the admin."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    try:
        with open(USER_TRACKING_FILE, "r") as file:
            users = file.read()
        if users.strip():
            await update.message.reply_text(f"📜 User List:\n{users}")
        else:
            await update.message.reply_text("📂 No users have used the bot yet.")
    except FileNotFoundError:
        await update.message.reply_text("📂 No users have used the bot yet.")

# Async Start Command

# Main Function
def main():

    """Starts the Telegram bot."""
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send_users", send_users))  # Admin-only command
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))
    application.add_handler(CommandHandler("download_youtube", download_youtube))
    application.add_handler(CommandHandler("youtube", lambda u, c: download_youtube(u, c, L)))
    application.add_handler(CommandHandler("instagram", lambda u, c: download_instagram(u, c, L)))


    # Start the bot
    application.run_polling(drop_pending_updates=True)

# Start the bot
if __name__ == "__main__":
    main()