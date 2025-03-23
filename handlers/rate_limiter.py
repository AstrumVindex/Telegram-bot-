import asyncio
import time
from collections import defaultdict
from telegram import Update
from telegram.ext import CallbackContext

# Rate limit settings
MAX_REQUESTS = 5  # Max messages allowed per user
TIME_WINDOW = 30  # Time window in seconds (0.5 minute)
BLOCK_TIME = 60  # Block user for 1 minute if they exceed the limit

# Dictionary to track user requests and block times
user_requests = defaultdict(list)
user_block_times = {}

async def enforce_rate_limit(update: Update, context: CallbackContext) -> bool:
    """Check if the user has exceeded the request limit and block them for 1 minute if so."""
    user_id = update.effective_user.id
    current_time = time.time()

    # Check if the user is currently blocked
    if user_id in user_block_times:
        block_end_time = user_block_times[user_id]
        if current_time < block_end_time:
            # User is still blocked
            remaining_time = int(block_end_time - current_time)
            await update.message.reply_text(
                f"⛔ You are blocked for {remaining_time} seconds. Please wait before sending more commands."
            )
            return False  # Deny request
        else:
            # Block time has expired, remove the user from the block list
            del user_block_times[user_id]

    # Remove old requests outside the time window
    user_requests[user_id] = [t for t in user_requests[user_id] if current_time - t < TIME_WINDOW]

    # Check if the user has exceeded the request limit
    if len(user_requests[user_id]) >= MAX_REQUESTS:
        # Block the user for 1 minute
        user_block_times[user_id] = current_time + BLOCK_TIME
        await update.message.reply_text(
            "⛔ Too many requests! You are blocked for 1 minute. Please wait before sending more commands."
        )
        return False  # Deny request

    # Append the new timestamp since it was allowed
    user_requests[user_id].append(current_time)
    return True  # Allow request