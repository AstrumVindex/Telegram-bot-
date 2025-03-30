import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeChat
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackContext, filters, CallbackQueryHandler
)
from handlers.config import BOT_TOKEN, ADMIN_ID
from handlers.downloads import download_instagram
from handlers.rate_limiter import enforce_rate_limit, blocked_users, unblock_user, set_limit, user_activity
from handlers.start import start
from handlers.messages import process_message
from handlers.errors import error_handler
from handlers.mp3button import convert_instagram_to_mp3

# Logger Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# File to Track Users
USER_TRACKING_FILE = "users.txt"

def track_user(user_id: int):
    """Tracks users who interact with the bot."""
    try:
        with open(USER_TRACKING_FILE, "r") as file:
            users = file.read().splitlines()
    except FileNotFoundError:
        users = []

    if str(user_id) not in users:
        with open(USER_TRACKING_FILE, "a") as file:
            file.write(f"{user_id}\n")

async def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id == ADMIN_ID

async def send_users(update: Update, context: CallbackContext):
    """Sends the list of tracked users to the admin."""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        with open(USER_TRACKING_FILE, "r") as file:
            users = file.read()
        message = f"📜 User List:\n{users}" if users.strip() else "📂 No users have used the bot yet."
        await update.message.reply_text(message)
    except FileNotFoundError:
        await update.message.reply_text("📂 No users have used the bot yet.")

async def handle_button_click(update: Update, context: CallbackContext):
    """Handles button clicks for MP3 conversion."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("convert_mp3:"):
        instagram_url = query.data.split(":", 1)[1]
        status_message = await query.message.reply_text("🎵 Converting video to MP3... Please wait... ⏳")

        try:
            mp3_file_path = await convert_instagram_to_mp3(instagram_url)

            if mp3_file_path and os.path.exists(mp3_file_path):  # ✅ Double-check existence
                await query.message.reply_audio(
                    audio=open(mp3_file_path, "rb"), 
                    caption="🎶 Here is your MP3 file!"
                )
                os.remove(mp3_file_path)  # ✅ Cleanup
            else:
                await status_message.edit_text(f"❌ Failed to convert to MP3. File not found at: {mp3_file_path}")

        except Exception as e:
            await status_message.edit_text(f"❌ Error during conversion: {str(e)}")
            print(f"MP3 conversion error: {e}")


async def rate_limited_process_message(update: Update, context: CallbackContext):
    """Checks rate limit before processing any user message."""
    is_allowed = await enforce_rate_limit(update, context)
    if is_allowed:
        await process_message(update, context)
    else:
        await update.message.reply_text("⚠️ You're sending messages too fast. Please wait.")

async def send_help(update: Update, context: CallbackContext):
    """Sends appropriate help message based on user role."""
    if await is_admin(update.effective_user.id):
        help_text = (
            "🛠 *Admin Commands:*\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n\n"
            "🔒 *Admin Only Commands:*\n"
            "/send_users - Get tracked users\n"
            "/blocked_users - Show blocked users\n"
            "/unblock <user_id> - Unblock a user\n"
            "/user_activity <user_id> - Check user activity\n"
            "/set_limit <messages> <time> - Change rate limits"
        )
    else:
        help_text = (
            "🛠 *Available Commands:*\n"
            "/start - Start the bot\n"
            "/help - Show this help message"
        )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def set_bot_commands(application: Application):
    """Sets bot commands in the Telegram menu with proper scoping."""
    # Commands for all users
    global_commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help message")
    ]
    
    # Admin-specific commands
    admin_commands = global_commands + [
        BotCommand("send_users", "Get tracked users (admin only)"),
        BotCommand("blocked_users", "Show blocked users (admin only)"),
        BotCommand("unblock", "Unblock a user (admin only)"),
        BotCommand("user_activity", "Check user activity (admin only)"),
        BotCommand("set_limit", "Change rate limits (admin only)")
    ]
    
    # Set commands for all users
    await application.bot.set_my_commands(global_commands)
    
    # Set admin commands specifically for admin
    await application.bot.set_my_commands(
        admin_commands,
        scope=BotCommandScopeChat(ADMIN_ID)
    )

async def post_init(application: Application):
    """Post-initialization tasks."""
    await set_bot_commands(application)

def main():
    """Starts the Telegram bot."""
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", send_help))
    
    # Admin commands with restriction
    admin_commands = [
        ("send_users", send_users),
        ("blocked_users", blocked_users),
        ("unblock", unblock_user),
        ("user_activity", user_activity),
        ("set_limit", set_limit)
    ]
    
    for cmd, handler in admin_commands:
        application.add_handler(
            CommandHandler(
                cmd,
                handler,
                filters=filters.User(ADMIN_ID)
            )
        )

    # Other handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, rate_limited_process_message))
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()