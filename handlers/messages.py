from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from handlers.downloads import download_instagram, download_youtube
from handlers.rate_limiter import enforce_rate_limit  # ✅ Import rate limiter

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages from users and processes Instagram & YouTube downloads."""
    user_message = update.message.text.strip()

    if "instagram.com" in user_message:
        await download_instagram(update, context)  # ✅ Call Instagram download function

    elif "youtube.com" in user_message or "youtu.be" in user_message:
        # Attempt to download YouTube video
        video_info = await download_youtube(user_message)  # ✅ Call API function

        if video_info and "download_link" in video_info:
            video_link = video_info["download_link"]
            await update.message.reply_text(f"✅ *Download Link:* [Click Here]({video_link})", parse_mode=ParseMode.MARKDOWN)
        else:
            # Send apology message if YouTube download fails
            await update.message.reply_text(
                "🙏 *We apologize for the inconvenience!*\n\n"
                "Currently, YouTube downloads are temporarily unavailable.\n"
                "We’re working hard to restore this feature as soon as possible.\n\n"
                "In the meantime, feel free to send Instagram links, and we’ll be happy to assist you with those!\n\n"
                "Thank you for your patience and understanding. 😊",
                parse_mode=ParseMode.MARKDOWN
            )

    else:
        await update.message.reply_text("⚠️ *Please send a valid Instagram or YouTube link.*", parse_mode=ParseMode.MARKDOWN)