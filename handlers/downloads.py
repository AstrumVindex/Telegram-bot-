import os
import re
import logging
import asyncio
from telegram.ext import ContextTypes
from instaloader import Instaloader, Post
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from handlers.config import RAPIDAPI_KEY  # Import API credentials

# ✅ Define Instaloader globally for Instagram
L = Instaloader()
L.context.timeout = 60  # Increase timeout to 60 seconds
os.makedirs("downloads", exist_ok=True)  # Ensure downloads folder exists

# ✅ Instagram Download Function
async def download_instagram(update: Update, context: CallbackContext):
    """Downloads Instagram media (Reel, Post, Story)."""
    message = update.effective_message
    instagram_url = message.text.strip()

    INSTAGRAM_REGEX = r"(https?://(?:www\.)?instagram\.com/(?:p|reel|tv|stories)/[a-zA-Z0-9_-]+)"
    match = re.search(INSTAGRAM_REGEX, instagram_url)

    if not match:
        await message.reply_text("⚠️ Invalid Instagram URL.")
        return

    shortcode = match.group(1).split('/')[-1]

    # ✅ Detect Instagram link type
    if "reel" in instagram_url:
        media_type = "reel"
    elif "p" in instagram_url:
        media_type = "post"
    elif "tv" in instagram_url:
        media_type = "IGTV"
    elif "stories" in instagram_url:
        media_type = "story"
    else:
        media_type = "media"

    waiting_message = await message.reply_text(f"📥 Downloading {media_type}, please wait...")

    try:
        post = Post.from_shortcode(L.context, shortcode)

        # ✅ Download Media
        await asyncio.to_thread(L.download_post, post, target="downloads")

        # ✅ Ensure correct media path
        media_path = f"downloads/{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S_UTC')}"

        # ✅ Generate Message with Buttons
        # ✅ Generate Message with Title & Buttons
        # ✅ Extract only the first line of the caption as title
        post_caption = post.caption.split('\n')[0] if post.caption else "Untitled Post"

        # ✅ Compose caption
        caption = (
             f"📢 *{post_caption}*\n\n"
             f"📅 *Posted:* `{post.date_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"
             f"👤 *Author:* [{post.owner_username}](https://www.instagram.com/{post.owner_username})\n"
             f"🔗 *Original Post:* [Click Here]({instagram_url})\n\n"
             f"_Via @{context.bot.username}_"
        )


          # ✅ Generate Buttons Dynamically
        keyboard = [
           [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
         ]

        # Add "Convert to MP3" button only for reels (videos)
        if "reel" in instagram_url and post.is_video:
           keyboard.insert(0, [InlineKeyboardButton("🎵 Convert to MP3", callback_data=f"convert_mp3:{shortcode}")])

        reply_markup = InlineKeyboardMarkup(keyboard)


        # ✅ Check if media exists and send it
        if post.is_video:
            video_file = f"{media_path}.mp4"
            if os.path.exists(video_file):
                with open(video_file, "rb") as file:
                    await message.reply_video(video=file, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
                os.remove(video_file)  # Delete after sending
                print(f"✅ Deleted video file: {video_file}")
            else:
                await message.reply_text("❌ Video file not found!")
        else:
            photo_file = f"{media_path}.jpg"
            if os.path.exists(photo_file):
                with open(photo_file, "rb") as file:
                    await message.reply_photo(photo=file, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
                os.remove(photo_file)  # Delete after sending
                print(f"✅ Deleted photo file: {photo_file}")
            else:
                await message.reply_text("❌ Photo file not found!")

        await waiting_message.edit_text(f"✅ Here is your {media_type}!")

    except Exception as e:
        await waiting_message.edit_text(f"❌ Instagram error: {str(e)}")
