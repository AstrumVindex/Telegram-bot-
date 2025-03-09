import logging
import re
import asyncio
import os
from dotenv import load_dotenv
from instaloader import Instaloader, Post
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load environment variables
load_dotenv()

# Get the bot token
import os

# Load bot token from Render environment variables
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ Bot token is missing! Make sure it is set in Render.")
    exit(1)


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

import time
import math

async def update_progress(update, context, current, total, speed):
    """Update the progress bar message dynamically"""
    progress = min(int((current / total) * 10), 10)  # Convert to a 10-block scale
    bar = "🟩" * progress + "⬜" * (10 - progress)  # Create progress bar

    text = f"📥 Downloading...\n{bar} {math.ceil((current / total) * 100)}%\n{current} MB of {total} MB ({speed} MB/s)"
    
    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data["progress_message"].message_id,
            text=text
        )
    except Exception:
        pass  # Ignore errors if message updates too frequently


# Async Download Function
import os
import requests
import instaloader
import asyncio

from telegram import Update
from telegram.ext import CallbackContext

L = instaloader.Instaloader()

# Ensure the 'downloads' directory exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

async def download(update: Update, context: CallbackContext):
    message = await update.message.reply_text("⏳ Preparing to download...")

    # Extract URL from user message
    instagram_url = update.message.text.strip()

    try:
        # Get the post using Instaloader
        shortcode_match = re.search(r"instagram\.com/(p|reel)/(\w+)", instagram_url)
        if not shortcode_match:
            await update.message.reply_text("⚠️ Invalid Instagram URL!")
            return
        
        shortcode = shortcode_match.group(2)
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # Get media URL (image or video)
        media_url = post.url  

        # Fetch file size
        response = requests.head(media_url)
        file_size = int(response.headers.get('content-length', 0))

        # Set up progress tracking
        file_name = f"downloads/{shortcode}.mp4" if post.is_video else f"downloads/{shortcode}.jpg"
        downloaded = 0

        # Start downloading with progress bar
        with open(file_name, "wb") as file:
            response = requests.get(media_url, stream=True)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    
                    # Calculate progress
                    progress = int((downloaded / file_size) * 100)
                    progress_bar = "⬜️" * (10 - progress // 10) + "🟩" * (progress // 10)

                    # Update Telegram message every 5%
                    if progress % 5 == 0:
                        await message.edit_text(
                            f"📥 Downloading... {progress}%\n{progress_bar}\n{downloaded // 1024} KB of {file_size // 1024} KB"
                        )

        # Send media after successful download
        if post.is_video:
            await update.message.reply_video(video=open(file_name, "rb"))
        else:
            await update.message.reply_photo(photo=open(file_name, "rb"))

        await message.delete()  # Remove progress bar when done

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Main Function
def main():
    """Starts the Telegram bot."""
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send_users", send_users))  # Admin-only command
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

    # Start the bot
    application.run_polling()

# Start the bot
if __name__ == "__main__":
    main()
