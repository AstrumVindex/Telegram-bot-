import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Fetch bot token
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # Fetch YouTube API key
RAPIDAPI_HOST_YT = os.getenv("RAPIDAPI_HOST_YT")
RAPIDAPI_HOST = "all-video-downloader3.p.rapidapi.com"

# ✅ Admin Telegram ID
ADMIN_ID = 1262827267  # Replace with your Telegram ID

# ✅ Rate Limit Settings
MAX_MESSAGES_BEFORE_WARNING = 5  # Number of messages before warning
EXTRA_MESSAGES_BEFORE_BLOCK = 4  # Extra messages after warning before blocking
TIME_WINDOW = 10  # Time window in seconds
BLOCK_TIME = 60  # Block duration in seconds
UESTS = 15  # Higher limits for admins
ADMIN_TIME_WINDOW = 30

