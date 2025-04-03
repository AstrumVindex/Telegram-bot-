import os
import logging
import requests
import asyncio
from instaloader import Instaloader, Post
from moviepy.video.io.VideoFileClip import VideoFileClip
from telegram.helpers import escape_markdown


# ✅ Initialize Instaloader
L = Instaloader()
L.context.timeout = 60  # Increase timeout

# Set up logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ Ensure directories exist
os.makedirs("downloads", exist_ok=True)
os.makedirs("mp3", exist_ok=True)

# ✅ Function to extract Instagram video URL and title
async def get_instagram_video_info(instagram_url):
    """Extracts the direct video URL and title from an Instagram post."""
    try:
        shortcode = instagram_url.strip("/").split("/")[-1]  # Extract shortcode
        post = Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            title = post.title if post.title else "Instagram_Reel"  # Default if no title
            safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)  # Remove special chars
            return post.video_url, safe_title  # ✅ Return video URL & safe title
        else:
            return None, None
    except Exception as e:
        logging.error(f"❌ Error getting Instagram video info: {e}")
        return None, None

# ✅ Function to download Instagram video
async def download_instagram_video(instagram_url):
    """Downloads the Instagram video locally and returns the file path & title."""
    try:
        direct_video_url, title = await get_instagram_video_info(instagram_url)
        if not direct_video_url:
            return None, None  # ❌ Video extraction failed

        file_path = os.path.join("downloads", f"{title}.mp4")
        response = requests.get(direct_video_url, stream=True)

        if response.status_code == 200:
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            logging.info(f"✅ Video downloaded successfully: {file_path}")
            return file_path, title  # ✅ Return file path & title
        else:
            logging.error("❌ Failed to download Instagram video.")
            return None, None
    except Exception as e:
        logging.error(f"❌ Download Error: {e}")
        return None, None

# ✅ Function to convert Instagram video to MP3

async def convert_instagram_to_mp3(instagram_url):
    """Returns tuple of (mp3_path, original_title, safe_filename)"""
    try:
        logger.info(f"Starting conversion for URL: {instagram_url}")
        video_path, title = await download_instagram_video(instagram_url)
        if not video_path:
            return None, None, None

        # Create safe filename
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
        mp3_path = os.path.join("mp3", f"{safe_title}.mp3")

        # Convert video to MP3
        video_clip = VideoFileClip(video_path)
        video_clip.audio.write_audiofile(mp3_path)
        video_clip.close()
        os.remove(video_path)
        logger.info("Successfully converted video to MP3")
        return mp3_path, title, f"{safe_title}.mp3"  # Return all three values

    except Exception as e:
        logger.error(f"MP3 Conversion Error: {str(e)}")
        return None, None, None

