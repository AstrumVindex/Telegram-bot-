import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Fetch token securely

