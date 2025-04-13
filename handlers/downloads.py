import os
import re
import logging
import asyncio
import time
from telegram.ext import ContextTypes
from instaloader import Instaloader, Post
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, Application
from handlers.config import RAPIDAPI_KEY

class ProgressHandler:
    def __init__(self):
        self.active_trackers = {}
        self.progress_styles = {
            'blocks': ['▱', '▰'],
            'circles': ['○', '●'],
            'squares': ['□', '■'],
            'arrows': ['▹', '▶'],
            'classic': ['-', '='],
            'fancy': ['░', '▓']
        }

    async def init_progress(self, update, context, initial_text="Starting download...", style='blocks'):
        message = await update.effective_message.reply_text(initial_text)
        self.active_trackers[update.effective_user.id] = {
            'message': message,
            'last_update': 0,
            'start_time': time.time(),
            'style': style,
            'last_percentage': 0
        }
        return message

    async def update_progress(self, user_id, progress, text="Downloading"):
        if user_id not in self.active_trackers:
            return

        tracker = self.active_trackers[user_id]
        empty_char, filled_char = self.progress_styles[tracker['style']]
        progress_bar = (filled_char * int(progress / 10) + 
                       empty_char * (10 - int(progress / 10)))

        try:
            await tracker['message'].edit_text(
                f"🔄 **{text}...**\n{progress_bar} {progress}%",
                parse_mode=ParseMode.MARKDOWN
            )
            tracker['last_update'] = time.time()
            tracker['last_percentage'] = progress
        except Exception as e:
            logging.warning(f"Progress update failed: {e}")

    async def complete_progress(self, user_id, completion_text="✅ Download complete!"):
        if user_id not in self.active_trackers:
            return

        try:
            await self.active_trackers[user_id]['message'].edit_text(completion_text)
            self.cleanup_progress(user_id)
        except Exception as e:
            logging.error(f"Progress completion failed: {e}")

    def cleanup_progress(self, user_id):
        if user_id in self.active_trackers:
            del self.active_trackers[user_id]

# Global instances
progress_manager = ProgressHandler()
L = Instaloader()
L.context.timeout = 60
os.makedirs("downloads", exist_ok=True)

async def download_instagram(update: Update, context: CallbackContext):
    """Downloads Instagram media with progress tracking"""
    message = update.effective_message
    user_id = update.effective_user.id
    instagram_url = message.text.strip()

    # URL validation
    INSTAGRAM_REGEX = r"(https?://(?:www\.)?instagram\.com/(?:p|reel|tv|stories)/[a-zA-Z0-9_-]+)"
    if not (match := re.search(INSTAGRAM_REGEX, instagram_url)):
        await message.reply_text("⚠️ Invalid Instagram URL.")
        return

    # Determine media type
    media_type = ("reel" if "reel" in instagram_url else
                "post" if "p" in instagram_url else
                "IGTV" if "tv" in instagram_url else
                "story" if "stories" in instagram_url else
                "media")

    shortcode = match.group(1).split('/')[-1]

    try:
        # Initialize progress
        await progress_manager.init_progress(
            update, context,
            initial_text=f"🔍 Analyzing {media_type}...",
            style='fancy'
        )

        # Step 1: Fetch metadata
        await progress_manager.update_progress(user_id, 10, f"Fetching {media_type} info")
        post = Post.from_shortcode(L.context, shortcode)
        await progress_manager.update_progress(user_id, 30, "Preparing download")

        # Step 2: Download
        await asyncio.to_thread(L.download_post, post, target="downloads")
        
        # Simulate progress
        for percent in range(40, 91, 10):
            await progress_manager.update_progress(user_id, percent, f"Downloading {media_type}")
            await asyncio.sleep(0.3)

        # Step 3: Process media
        await progress_manager.update_progress(user_id, 90, "Processing media")
        media_path = f"downloads/{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S_UTC')}"

        # Prepare caption
        post_caption = post.caption.split('\n')[0] if post.caption else "Untitled Post"
        caption = (
            f"📢 *{post_caption}*\n\n"
            f"📅 *Posted:* `{post.date_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"
            f"👤 *Author:* [{post.owner_username}](https://www.instagram.com/{post.owner_username})\n"
            f"🔗 *Original Post:* [Click Here]({instagram_url})\n\n"
            f"_Via @{context.bot.username}_"
        )

        # Prepare keyboard
        keyboard = []
        if "reel" in instagram_url and post.is_video:
            keyboard.append([InlineKeyboardButton("🎵 Convert to MP3", callback_data=f"convert_mp3:{shortcode}")])
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        # Handle media
        try:
            if post.typename == 'GraphSidecar':
                await handle_carousel(message, media_path, caption, media_type)
            else:
                await handle_single_media(
                    message, 
                    media_path, 
                    caption, 
                    media_type, 
                    post.is_video, 
                    reply_markup
                )

            await progress_manager.complete_progress(user_id, f"✅ Here is your {media_type}!")

        except Exception as e:
            await progress_manager.complete_progress(user_id, f"❌ Failed to process {media_type}")
            await message.reply_text(f"Error processing media: {str(e)}")
            logging.error(f"Media processing failed: {str(e)}")

    except Exception as e:
        await progress_manager.complete_progress(user_id, f"❌ Failed to download {media_type}")
        await message.reply_text(f"Error: {str(e)}")
        logging.error(f"Instagram download failed: {str(e)}")

async def handle_carousel(message, media_path, caption, media_type):
    """Handle carousel posts (multiple images/videos) and clean up files"""
    photo_group = []
    files_to_cleanup = []
    
    try:
        index = 1
        while True:
            image_file = f"{media_path}_{index}.jpg"
            video_file = f"{media_path}_{index}.mp4"

            if os.path.exists(image_file):
                # Open file and immediately add to cleanup list
                file_handle = open(image_file, "rb")
                files_to_cleanup.append(image_file)
                
                if index == 1:
                    media = InputMediaPhoto(
                        media=file_handle,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    media = InputMediaPhoto(media=file_handle)
                photo_group.append(media)
                index += 1
            elif os.path.exists(video_file):
                # Open file and immediately add to cleanup list
                file_handle = open(video_file, "rb")
                files_to_cleanup.append(video_file)
                
                if index == 1:
                    media = InputMediaVideo(
                        media=file_handle,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    media = InputMediaVideo(media=file_handle)
                photo_group.append(media)
                index += 1
            else:
                break

        if photo_group:
            await message.reply_media_group(media=photo_group)
        else:
            await message.reply_text("❌ Couldn't find any media in this carousel!")
    except Exception as e:
        await message.reply_text(f"❌ Error processing carousel: {str(e)}")
        raise
    finally:
        # Clean up all files
        cleanup_files(files_to_cleanup)
        # Close all file handles
        for media in photo_group:
            if hasattr(media.media, 'close'):
                media.media.close()

async def handle_single_media(message, media_path, caption, media_type, is_video, reply_markup=None):
    """Handle single photo/video post and clean up file"""
    file_path = None
    try:
        if is_video:
            file_path = f"{media_path}.mp4"
            if os.path.exists(file_path):
                with open(file_path, "rb") as video_file:
                    await message.reply_video(
                        video=video_file,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
            else:
                await message.reply_text("❌ Video file not found!")
        else:
            file_path = f"{media_path}.jpg"
            if os.path.exists(file_path):
                with open(file_path, "rb") as photo_file:
                    await message.reply_photo(
                        photo=photo_file,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
            else:
                await message.reply_text("❌ Photo file not found!")
    except Exception as e:
        await message.reply_text(f"❌ Error processing media: {str(e)}")
        raise
    finally:
        if file_path and os.path.exists(file_path):
            cleanup_files([file_path])

def cleanup_files(file_list):
    """Safely clean up downloaded files with error handling"""
    for file_path in file_list:
        try:
            if isinstance(file_path, str) and os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"✅ Deleted: {file_path}")
        except Exception as e:
            logging.warning(f"❌ Failed to delete {file_path}: {e}")

def cleanup_files(file_list):
    """Clean up downloaded files safely"""
    for file_path in file_list:
        try:
            if isinstance(file_path, str) and os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Cleaned up: {file_path}")
        except Exception as e:
            logging.warning(f"Error cleaning up {file_path}: {e}")