import os
import logging
import threading
from flask import Flask
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
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from handlers.mp3button import convert_instagram_to_mp3
from database import user_db  

# Logger Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ Flask Web Server to Keep Bot Alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    """Runs Flask web server on a separate thread."""
    app.run(host="0.0.0.0", port=8080)

async def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id == ADMIN_ID

async def send_users(update: Update, context: CallbackContext):
    """Sends the list of tracked users to the admin."""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    total_users, active_users = user_db.get_user_stats()
    message = (
        f"📊 Bot Statistics:\n"
        f"• Total users: {total_users}\n"
        f"• Active users (last 30 days): {active_users}"
    )
    await update.message.reply_text(message)

async def handle_button_click(update: Update, context: CallbackContext):
    """Handles button clicks with proper value unpacking"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("convert_mp3:"):
        instagram_url = query.data.split(":", 1)[1]
        
        new_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "➕ Add to Group", 
                url=f"https://t.me/{context.bot.username}?startgroup=true"
            )]
        ])
        await query.message.edit_reply_markup(reply_markup=new_markup)
        
        processing_msg = await query.message.reply_text("⏳ Converting Please Wait...")

        try:
            result = await convert_instagram_to_mp3(instagram_url)
            
            if result and len(result) >= 2:
                mp3_file_path = result[0]  
                
                if mp3_file_path and os.path.exists(mp3_file_path):
                    with open(mp3_file_path, "rb") as mp3_file:
                        await query.message.reply_audio(
                            audio=mp3_file,
                            caption="🎶 Here is your MP3",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    await processing_msg.delete()
                    os.remove(mp3_file_path)
                else:
                    await processing_msg.edit_text("❌ Conversion failed")
            else:
                await processing_msg.edit_text("❌ Conversion failed")

        except Exception as e:
            await processing_msg.edit_text(f"❌ Error: {str(e)}")

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
            "/help - Show help message"
        )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def set_bot_commands(application: Application):
    """Sets bot commands in the Telegram menu with proper scoping."""
    global_commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help message")
    ]
    
    admin_commands = global_commands + [
        BotCommand("send_users", "Get tracked users (admin only)"),
        BotCommand("blocked_users", "Show blocked users (admin only)"),
        BotCommand("unblock", "Unblock a user (admin only)"),
        BotCommand("user_activity", "Check user activity (admin only)"),
        BotCommand("set_limit", "Change rate limits (admin only)")
    ]
    
    await application.bot.set_my_commands(global_commands)
    
    await application.bot.set_my_commands(
        admin_commands,
        scope=BotCommandScopeChat(ADMIN_ID)
    )

async def post_init(application: Application):
    """Post-initialization tasks."""
    await set_bot_commands(application)

def main():
    """Starts the Telegram bot and web server."""
    # ✅ Start Flask web server in a separate thread
    threading.Thread(target=run_web_server, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", send_help))
    
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

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, rate_limited_process_message))
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_error_handler(error_handler)

    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
