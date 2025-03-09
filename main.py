import logging
import re
import asyncio
import os
from dotenv import load_dotenv
from instaloader import Instaloader, Post
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from aiolimiter import AsyncLimiter
import asyncio
# Global variables
download_in_progress = False
download_queue = []


# Load environment variables
load_dotenv()

# Get the bot token
import os

# Load bot token from Render environment variables
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ Bot token is missing! Make sure it is set in Render.")
    exit(1)

rate_limiter = AsyncLimiter(1, 2)  # Allows 1 message every 2 seconds

# Initialize the bot application after loading the token
app = Application.builder().token(TOKEN).build()

# Initialize Instaloader
L = Instaloader()

# Logger Setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Token Loaded: {TOKEN}")




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
        await update.message.reply_text("🫵 You are not authorized to use this command.")
        return
    
    try:
        with open(USER_TRACKING_FILE, "r") as file:
            users = file.read()
        if users.strip():
            await update.message.reply_text(f" User List:\n{users}")
        else:
            await update.message.reply_text("😩 No users have used the bot yet.")
    except FileNotFoundError:
        await update.message.reply_text("😩 No users have used the bot yet.")

# Async Start Command
async def start(update: Update, context: CallbackContext):
    """Handles the /start command."""
    track_user(update.effective_user.id)  # Track user
    await update.message.reply_text("👋 Hey there! Just send an Instagram post or reel link, and I'll fetch the media for you!")

# Async Download Function
async def download_media(update: Update, context: CallbackContext):
    global download_in_progress, download_queue

    link = update.message.text.strip()
    user_id = update.message.from_user.id

    # Check if a download is already in progress
    if download_in_progress:
        await update.message.reply_text("⏳ A download is already in progress. Your link has been added to the queue.")
        download_queue.append((link, user_id))
        return

    download_in_progress = True
    await update.message.reply_text("📥 Preparing to download...")

    try:
        # Simulate download with progress updates
        total_size = 100  # Example total size in KB
        downloaded = 0
        message = await update.message.reply_text(generate_progress_bar(downloaded, total_size))

        while downloaded < total_size:
            await asyncio.sleep(1)  # Simulate download time
            downloaded += 10  # Simulate download chunk
            if downloaded > total_size:
                downloaded = total_size
            await message.edit_text(generate_progress_bar(downloaded, total_size))

        await update.message.reply_text("✅ Download complete!")

    except Exception as e:
        logger.error(f"Error during download: {e}")
        await update.message.reply_text("❌ An error occurred during the download.")

    finally:
        download_in_progress = False
        # Process the next item in the queue
        await process_queue(context)

#download media
async def process_queue(context: CallbackContext):
    global download_in_progress, download_queue

    if not download_in_progress and download_queue:
        next_link, user_id = download_queue.pop(0)
        chat_id = user_id  # Assuming user_id is the chat_id
        await context.bot.send_message(chat_id=chat_id, text="📥 Starting your download...")
        # Create a mock update object
        mock_update = Update(update_id=0, message=update.message)
        mock_update.message.text = next_link
        mock_update.message.from_user.id = user_id
        await download_media(mock_update, context)

# Main Function
def main():
    """Starts the Telegram bot."""
    
    # Create the bot application instance
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send_users", send_users))  # Admin-only command
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))


#added this line 
def generate_progress_bar(progress, total, bar_length=20):
    filled_length = int(bar_length * progress // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    percentage = (progress / total) * 100
    return f"[{bar}] {percentage:.1f}%\n{progress} KB of {total} KB"

    # Define error handler
    async def error_handler(update, context):
        """Handles unexpected errors and prevents bot crashes."""
        logging.error(f"⚠️ Exception: {context.error}")
        await update.message.reply_text("❌ Oops! Something went wrong. Please try again later.")
# Job queue to process the download queue
    job_queue = application.job_queue
    job_queue.run_repeating(process_queue, interval=5)

    # Add the error handler after defining `application`
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()

# Ensure the script runs correctly
if __name__ == "__main__":
    main()
