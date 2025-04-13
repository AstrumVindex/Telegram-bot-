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

# 🚀 Add at the top
from telegram import InputMediaPhoto, InputMediaVideo

async def download_instagram(update: Update, context: CallbackContext):
    """Downloads Instagram media (Reel, Post, Story, or Carousel)."""
    message = update.effective_message
    instagram_url = message.text.strip()

    INSTAGRAM_REGEX = r"(https?://(?:www\.)?instagram\.com/(?:p|reel|tv|stories)/[a-zA-Z0-9_-]+)"
    match = re.search(INSTAGRAM_REGEX, instagram_url)

    if not match:
        await message.reply_text("⚠️ Invalid Instagram URL.")
        return

    shortcode = match.group(1).split('/')[-1]

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

        await asyncio.to_thread(L.download_post, post, target="downloads")

        media_path = f"downloads/{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S_UTC')}"

        post_caption = post.caption.split('\n')[0] if post.caption else "Untitled Post"
        caption = (
            f"📢 *{post_caption}*\n\n"
            f"📅 *Posted:* `{post.date_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"
            f"👤 *Author:* [{post.owner_username}](https://www.instagram.com/{post.owner_username})\n"
            f"🔗 *Original Post:* [Click Here]({instagram_url})\n\n"
            f"_Via @{context.bot.username}_"
        )

        # Remove "Add to Group" button if it's a carousel
        keyboard = []
        if "reel" in instagram_url and post.is_video:
            keyboard.append([InlineKeyboardButton("🎵 Convert to MP3", callback_data=f"convert_mp3:{shortcode}")])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        # 🧠 Detect carousel or single
        is_carousel = post.typename == 'GraphSidecar'
        photo_group = []
        files_to_cleanup = []  # Track files for cleanup

        if is_carousel:
            index = 1
            while True:
                image_file = f"{media_path}_{index}.jpg"
                video_file = f"{media_path}_{index}.mp4"

                if os.path.exists(image_file):
                    photo_group.append(InputMediaPhoto(media=open(image_file, "rb")))
                    files_to_cleanup.append(image_file)
                    index += 1
                elif os.path.exists(video_file):
                    photo_group.append(InputMediaVideo(media=open(video_file, "rb")))
                    files_to_cleanup.append(video_file)
                    index += 1
                else:
                    break  # No more files

            if photo_group:
                # Add caption to the first media
                photo_group[0] = InputMediaPhoto(
                    media=photo_group[0].media,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN
                )

                await message.reply_media_group(media=photo_group)
                await waiting_message.edit_text(f"✅ Here is your {media_type}!")

                # Cleanup
                for file_path in files_to_cleanup:
                    try:
                        os.remove(file_path)
                        print(f"✅ Deleted: {file_path}")
                    except Exception as e:
                        print(f"❌ Error deleting {file_path}: {e}")

                # Close all file handles
                for media in photo_group:
                    if hasattr(media.media, 'close'):
                        media.media.close()

            else:
                await waiting_message.edit_text("❌ Couldn't find any media in this post!")

        else:
            if post.is_video:
                video_file = f"{media_path}.mp4"
                if os.path.exists(video_file):
                    try:
                        with open(video_file, "rb") as file:
                            await message.reply_video(video=file, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
                        await waiting_message.edit_text(f"✅ Here is your {media_type}!")
                    finally:
                        try:
                            os.remove(video_file)
                            print(f"✅ Deleted video file: {video_file}")
                        except Exception as e:
                            print(f"❌ Error deleting video file: {e}")
                else:
                    await waiting_message.edit_text("❌ Video file not found!")
            else:
                photo_file = f"{media_path}.jpg"
                if os.path.exists(photo_file):
                    try:
                        with open(photo_file, "rb") as file:
                            await message.reply_photo(photo=file, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
                        await waiting_message.edit_text(f"✅ Here is your {media_type}!")
                    finally:
                        try:
                            os.remove(photo_file)
                            print(f"✅ Deleted photo file: {photo_file}")
                        except Exception as e:
                            print(f"❌ Error deleting photo file: {e}")
                else:
                    await waiting_message.edit_text("❌ Photo file not found!")

    except Exception as e:
        await waiting_message.edit_text(f"❌ Instagram error: {str(e)}")