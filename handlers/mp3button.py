import os
import re
import logging
import requests
import asyncio
from instaloader import Instaloader, Post
from moviepy.video.io.VideoFileClip import VideoFileClip


# ✅ Initialize Instaloader
L = Instaloader()
L.context.timeout = 60  # Increase timeout

# ✅ Ensure the downloads and MP3 directories exist
os.makedirs("downloads", exist_ok=True)
os.makedirs("mp3", exist_ok=True)

# ✅ Function to extract Instagram video URL
async def get_instagram_video_url(instagram_url):
    """Extracts the direct video URL from an Instagram post."""
    try:
        shortcode = instagram_url.strip("/").split("/")[-1]  # Extract shortcode from URL
        post = Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            return post.video_url  # ✅ Return direct video URL
        else:
            return None
    except Exception as e:
        logging.error(f"❌ Error getting Instagram video URL: {e}")
        return None

# ✅ Function to download Instagram video
async def download_instagram_video(instagram_url):
    """Downloads the Instagram video locally."""
    try:
        # ✅ Step 1: Extract the direct video URL
        direct_video_url = await get_instagram_video_url(instagram_url)
        if not direct_video_url:
            return None  # ❌ Video extraction failed

        response = requests.get(direct_video_url, stream=True)
        if response.status_code == 200:
            file_path = os.path.join("downloads", "instagram_video.mp4")
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            logging.info(f"✅ Video downloaded successfully: {file_path}")
            return file_path
        else:
            logging.error("❌ Failed to download Instagram video.")
            return None
    except Exception as e:
        logging.error(f"❌ Download Error: {e}")
        return None

# ✅ Function to convert Instagram video to MP3
async def convert_instagram_to_mp3(instagram_url):
    """Downloads Instagram video, extracts audio, and converts it to MP3."""
    try:
        # ✅ Step 1: Download Instagram video
        video_path = await download_instagram_video(instagram_url)
        if not video_path:
            print("❌ Failed to download video.")
            return None

        # ✅ Step 2: Convert Video to MP3
        mp3_path = "mp3/instagram_audio.mp3"
        video_clip = VideoFileClip(video_path)

        print(f"🔹 Extracting audio from: {video_path}")
        print(f"🔹 Saving MP3 to: {mp3_path}")

        video_clip.audio.write_audiofile(mp3_path)

        # ✅ Cleanup: Remove the original video file
        os.remove(video_path)

        print(f"✅ MP3 saved: {mp3_path}")  # Debug log
        return mp3_path

    except Exception as e:
        print(f"❌ MP3 Conversion Error: {str(e)}")
        return None


