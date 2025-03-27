import os
import re
import logging
import asyncio
import requests
import time
from telegram.ext import ContextTypes
from instaloader import Instaloader, Post
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from handlers.config import RAPIDAPI_KEY, RAPIDAPI_HOST, RAPIDAPI_HOST_YT  # Import API credentials

# ✅ Define Instaloader globally for Instagram
L = Instaloader()
L.context.timeout = 60  # Increase timeout to 60 seconds
os.makedirs("downloads", exist_ok=True)  # Ensure downloads folder exists

# ✅ Function to Extract YouTube Video ID from URL
def extract_youtube_id(url):
    """Extracts the YouTube video ID from different link formats."""
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    elif "youtube.com/watch?v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtube.com/shorts/" in url:
        return url.split("/shorts/")[-1].split("?")[0]
    return None  # Invalid URL

# ✅ Function to Download YouTube Video
async def download_youtube(update, context):
    """Fetches the YouTube video download link."""
    message = update.message.text.strip()
    video_id = extract_youtube_id(message)

    if not video_id:
        await update.message.reply_text("⚠️ Invalid YouTube link. Please try again.")
        return

    # ✅ Detect YouTube link type (Shorts, Video, etc.)
    if "shorts" in message:
        media_type = "shorts"
    else:
        media_type = "video"

    waiting_message = await update.message.reply_text(f"📥 Downloading {media_type}, please wait...")

    # ✅ API Request
    url = "https://ytstream-download-youtube-videos.p.rapidapi.com/dl"
    querystring = {"id": video_id}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST_YT
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()

        # ✅ Check for a valid response
        if "formats" in data and len(data["formats"]) > 0:
            video_link = data["formats"][0]["url"]
            await waiting_message.edit_text(f"✅ Here is your {media_type}: [Click Here]({video_link})", parse_mode="Markdown")
        else:
            await waiting_message.edit_text("❌ Could not fetch video. Try again.")

    except Exception as e:
        await waiting_message.edit_text(f"❌ API Error: {str(e)}")

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
        caption = (
            "🎬 *Instagram Media Downloaded!*\n\n"
            "📅 *Posted:* `{time}`\n"
            "👤 *Author:* [{author}](https://www.instagram.com/{author})\n"
            "🔗 *Original Post:* [Click Here]({post_url})\n\n"
            "_Enjoy your media! Powered by [@{bot_username}](https://t.me/{bot_username})_"
        ).format(
            time=post.date_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
            author=post.owner_username,
            post_url=instagram_url,
            bot_username=context.bot.username
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
