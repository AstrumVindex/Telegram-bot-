import os
import re
import logging
import asyncio
import requests
import time
from instaloader import Instaloader, Post
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

# ✅ Define Instaloader globally for Instagram
L = Instaloader()
L.context.timeout = 60  # Increase timeout to 60 seconds
os.makedirs("downloads", exist_ok=True)  # Ensure downloads folder exists

# ✅ Progress Bar Handling
async def update_progress(message: Message, progress: int):
    """Updates the progress bar in the bot message."""
    progress_bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
    await message.edit_text(f"📥 Downloading media...\n[{progress_bar}] {progress}%")

# ✅ YouTube Download Function
async def download_youtube(video_url):
    """Downloads YouTube media using an API."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", video_url)
    if not match:
        return {"error": "Invalid YouTube URL. Could not extract video ID."}

    video_id = match.group(1)
    url = "https://youtube-media-downloader.p.rapidapi.com/v2/misc/list-items"
    headers = {
        "x-rapidapi-key": "API-KEY",
        "x-rapidapi-host": "youtube-media-downloader.p.rapidapi.com"
    }
    params = {"videoId": video_id}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data.get("status") and "download_link" in data:
        return {"download_link": data["download_link"]}
    else:
        return {"error": "Failed to fetch video. Check API response."}

# ✅ Instagram Download Function with Progress Bar
async def download_instagram(update: Update, context: CallbackContext):
    """Downloads Instagram media with real-time progress updates."""
    message = update.effective_message
    instagram_url = message.text.strip()

    INSTAGRAM_REGEX = r"(https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[a-zA-Z0-9_-]+)"
    match = re.search(INSTAGRAM_REGEX, instagram_url)

    if not match:
        await message.reply_text("⚠️ Invalid Instagram URL.")
        return

    shortcode = match.group(1).split('/')[-1]

    try:
        progress_message = await message.reply_text("🎦 Fetching Media...")

        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                post = Post.from_shortcode(L.context, shortcode)
                break  # Exit loop if successful
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    await message.reply_text(f"❌ Instagram error: {str(e)}")
                    return
                await message.reply_text("⚠️ Retrying... Please wait...")
                time.sleep(3)  # Wait before retrying

        # ✅ Set Progress Bar (0% Start)
        await update_progress(progress_message, 0)

        # ✅ Download Media
        await asyncio.to_thread(L.download_post, post, target="downloads")

        # ✅ Set Progress Bar (50% Done)
        await update_progress(progress_message, 50)

        # ✅ Ensure correct media path
        media_path = f"downloads/{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S_UTC')}"
        print(f"Checking in: {os.path.abspath(media_path)}")
        
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
            [InlineKeyboardButton("🤖 Invite Bot", url=f"https://t.me/share/url?url=https://t.me/{context.bot.username}&text=Join%20this%20awesome%20bot!")]
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
                # Delete the video file after sending
                os.remove(video_file)
                print(f"✅ Deleted video file: {video_file}")
            else:
                await message.reply_text("❌ Video file not found!")
        else:
            photo_file = f"{media_path}.jpg"
            if os.path.exists(photo_file):
                with open(photo_file, "rb") as file:
                    await message.reply_photo(photo=file, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
                # Delete the photo file after sending
                os.remove(photo_file)
                print(f"✅ Deleted photo file: {photo_file}")
            else:
                await message.reply_text("❌ Photo file not found!")

        # ✅ Set Progress Bar to 100% & Show Completion Message
        await update_progress(progress_message, 100)
        await progress_message.edit_text("✅ Here is your media 👇")

    except Exception as e:
        await message.reply_text(f"❌ Instagram error: {str(e)}")