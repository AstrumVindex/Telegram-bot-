import yt_dlp
import os
import re
import logging
import pytube
from instaloader import Instaloader, Post
from telegram import Update
from telegram.ext import CallbackContext

# ✅ Define Instaloader globally for Instagram
L = Instaloader()
os.makedirs("downloads", exist_ok=True)  # Ensure downloads folder exists


# ✅ YouTube Download Function

# Set the correct FFmpeg path
FFMPEG_PATH = "./ffmpeg.exe"  # Update if necessary

async def download_youtube(update, context):
    message = update.effective_message
    youtube_url = message.text.strip()

    # Ensure downloads directory exists
    os.makedirs("downloads", exist_ok=True)

    # Define yt-dlp options
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
        'ffmpeg_location': FFMPEG_PATH,  # Ensure yt-dlp finds FFmpeg
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'quiet': False
    }

    try:
        await update.message.reply_text("⏳ Downloading your video...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            file_name = ydl.prepare_filename(info_dict)

        # Send the downloaded video
        await update.message.reply_video(video=open(file_name, "rb"), caption="✅ Download complete!")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to download video: {str(e)}")


# ✅ Instagram Download Function
async def download_instagram(update: Update, context: CallbackContext):
    message = update.effective_message
    instagram_url = message.text.strip()

    INSTAGRAM_REGEX = r"(https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[a-zA-Z0-9_-]+)"
    match = re.search(r"/(p|reel|tv)/([A-Za-z0-9_-]+)", instagram_url)

    if match:
        shortcode = match.group(2)
    else:
        await update.message.reply_text("⚠️ Failed to extract shortcode.")
        return

    try:
        fetch_message = await update.message.reply_text("⏳ Fetching Instagram media...")

        # ✅ Fetch Instagram post using Instaloader
        post = Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target="downloads")

        # ✅ Delete "Fetching..." message
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=fetch_message.message_id)

        # ✅ Send media
        media_path = f"downloads/{shortcode}/{post.date_utc.strftime('%Y%m%d_%H%M%S')}"
        if post.is_video:
            video_file = f"{media_path}.mp4"
            if os.path.exists(video_file):
                await update.message.reply_video(video=open(video_file, "rb"))
            else:
                await update.message.reply_text("❌ Video file not found!")
        else:
            photo_file = f"{media_path}.jpg"
            if os.path.exists(photo_file):
                await update.message.reply_photo(photo=open(photo_file, "rb"))
            else:
                await update.message.reply_text("❌ Photo file not found!")

    except Exception as e:
        await update.message.reply_text(f"❌ Instagram error: {str(e)}")
