import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Fetch bot token
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # Fetch YouTube API key
RAPIDAPI_HOST_YT = os.getenv("RAPIDAPI_HOST_YT")
RAPIDAPI_HOST = "all-video-downloader3.p.rapidapi.com"


