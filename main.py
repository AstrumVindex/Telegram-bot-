import logging
import re
import asyncio
from instaloader import Instaloader, Post
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Logger Setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Instaloader
L = Instaloader()

# Telegram Bot Token (Replace with your actual token)
TOKEN = "8042848778:AAExr22gOgmvQ7O0nQ3qJHsUtCBfD6xOGbU"

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
async def start(update: Update, context: CallbackContext):
    """Handles the /start command."""
    track_user(update.effective_user.id)  # Track user
    await update.message.reply_text("👋 Hey there! Just send an Instagram post or reel link, and I'll fetch the media for you!")

# Async Download Function

import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Initialize a dictionary to keep track of active downloads
active_downloads = {}

# Define the download function
async def download_file(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    url = "your_file_url_here"  # replace with the actual file URL you want to download
    file_name = "your_file_name_here"  # replace with the actual file name you want to save

    # You can use a simple try-except block to handle errors during download
    try:
        # Notify user about the start of the download
        await update.message.reply_text("⏳ Download starting...")

        # Here you can write code to actually download the file from the URL
        # For example, using aiohttp or requests, but here is a mock for demonstration:
        await asyncio.sleep(5)  # simulate download time with asyncio sleep
        
        # Save the file or process it here
        with open(file_name, 'w') as file:
            file.write("Mock file content for your bot.")  # Replace with actual download code

        # Notify user that the download is complete
        await update.message.reply_text(f"✅ Download complete! Saved as {file_name}.")

    except Exception as e:
        # If any error occurs, notify the user
        await update.message.reply_text(f"❌ Download failed: {e}")

# Define the cancel download function
async def cancel_download(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    
    # If the user is in the active download list, cancel it
    if chat_id in active_downloads:
        active_downloads[chat_id].cancel()  # Cancel the download task
        del active_downloads[chat_id]  # Remove from active download tracking
        await update.message.reply_text("🚫 Download canceled.")
    else:
        await update.message.reply_text("❌ No active downloads to cancel.")

# Main function to set up bot
def main():
    # Initialize your bot here (replace 'your_bot_token' with your actual bot token)
    app = Application.builder().token('8042848778:AAExr22gOgmvQ7O0nQ3qJHsUtCBfD6xOGbU').build()

    # Add handlers for /download and /cancel commands
    app.add_handler(CommandHandler("download", download_file))
    app.add_handler(CommandHandler("cancel", cancel_download))

    # Run the bot
    app.run_polling()

if __name__ == '__main__':
    main()
