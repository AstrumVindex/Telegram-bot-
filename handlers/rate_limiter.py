import asyncio
import time
from collections import defaultdict
from telegram import Update
from telegram.ext import CallbackContext

# Rate limit settings
MAX_REQUESTS = 5  # Max messages allowed per user
TIME_WINDOW = 60  # Time window in seconds (1 minute)

# Dictionary to track user requests
user_requests = defaultdict(list)

async def enforce_rate_limit(update: Update, context: CallbackContext) -> bool:
    """Check if the user has exceeded the request limit."""
    user_id = update.effective_user.id
    current_time = time.time()

    # Remove old requests outside the time window
    user_requests[user_id] = [t for t in user_requests[user_id] if current_time - t < TIME_WINDOW]

    if len(user_requests[user_id]) >= MAX_REQUESTS:
        await update.message.reply_text("⛔ Too many requests! Please wait a minute before sending more commands.")
        return False  # Deny request

    # Append the new timestamp since it was allowed
    user_requests[user_id].append(current_time)
    return True  # Allow request


