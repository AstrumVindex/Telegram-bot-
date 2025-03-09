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

# Async Download Function
async def download(update: Update, context: CallbackContext):
    """Download Instagram media using Instaloader."""
    track_user(update.effective_user.id)  # Track user
    message = update.effective_message
    instagram_url = message.text.strip()

    # Check if URL is an Instagram post or reel
    if not re.search(r"instagram.com/(p|reel)/", instagram_url):
        await update.message.reply_text(" Please send a valid Instagram post or reel URL.")
        return

    try:
        # Extract shortcode
        shortcode_match = re.search(r"instagram.com/(p|reel)/([^/?]+)", instagram_url)
        if not shortcode_match:
            await update.message.reply_text(" Invalid Instagram URL format.")
            return
        
        shortcode = shortcode_match.group(2)

        # Send "Fetching..." message
        fetch_message = await update.message.reply_text("⏳ Fetching media...")

        # Fetch Instagram post details
        post = Post.from_shortcode(L.context, shortcode)

        # Delete "Fetching..." message
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=fetch_message.message_id)

        # Send the media
        if post.is_video:
            await update.message.reply_video(post.video_url)
        else:
            await update.message.reply_photo(post.url)

        # Send final success message
        await update.message.reply_text("? Download successful! Thank you for using this bot.")

    except Exception as e:
        logger.error(f"Error fetching Instagram post: {e}")
        await update.message.reply_text(f"? Error processing request: {e}")

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