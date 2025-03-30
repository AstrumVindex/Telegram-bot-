import time
from telegram import Update
from telegram.ext import CallbackContext
from handlers.config import ADMIN_ID  # ✅ Import admin ID from config.py

# ✅ Rate Limit Settings
MESSAGE_LIMIT = 4  # Max messages before warning
EXTRA_LIMIT = 2  # Additional messages allowed after warning before blocking
TIME_WINDOW = 10  # Time window in seconds
BLOCK_DURATION = 60  # Block duration in seconds

# ✅ User tracking
user_message_counts = {}  # {user_id: [timestamps]}
warned_users = {}  # {user_id: warning_timestamp}
blocked_users_list = {}  # {user_id: block_end_time}

async def enforce_rate_limit(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    current_time = time.time()

    # ✅ Check if user is blocked
    if user_id in blocked_users_list:
        block_end_time = blocked_users_list[user_id]
        if current_time < block_end_time:
            await update.message.reply_text(f"🚫 You are blocked! Wait {int(block_end_time - current_time)} seconds.")
            return False  # Deny message processing
        else:
            del blocked_users_list[user_id]  # ✅ Unblock user

    # ✅ Track user messages
    if user_id not in user_message_counts:
        user_message_counts[user_id] = []

    user_message_counts[user_id].append(current_time)

    # ✅ Remove old messages outside the time window
    user_message_counts[user_id] = [t for t in user_message_counts[user_id] if current_time - t <= TIME_WINDOW]

    # ✅ If user exceeds warning limit
    if len(user_message_counts[user_id]) >= MESSAGE_LIMIT:
        if user_id in warned_users:  # ✅ If user was already warned
            if len(user_message_counts[user_id]) >= MESSAGE_LIMIT + EXTRA_LIMIT:
                blocked_users_list[user_id] = current_time + BLOCK_DURATION  # ✅ Block user
                del warned_users[user_id]  # ✅ Remove warning after blocking
                await update.message.reply_text(f"🚫 You are blocked for {BLOCK_DURATION} seconds due to spam.")
                return False
        else:
            warned_users[user_id] = current_time  # ✅ Mark user as warned
            await update.message.reply_text("⚠️ Slow down! Sending too many messages quickly will get you blocked.")
            return True  # ✅ Allow the warning message

    return True  # ✅ Allow normal message processing

# ✅ Admin Commands
async def blocked_users(update: Update, context: CallbackContext):
    """Admin command to list blocked users."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if not blocked_users_list:
        await update.message.reply_text("✅ No users are currently blocked.")
    else:
        blocked_users_msg = "\n".join([f"🔴 User ID: {uid}" for uid in blocked_users_list])
        await update.message.reply_text(f"🚫 Blocked Users:\n{blocked_users_msg}")

async def unblock_user(update: Update, context: CallbackContext):
    """Admin command to unblock a user."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    try:
        user_id = int(context.args[0])
        if user_id in blocked_users_list:
            del blocked_users_list[user_id]
            await update.message.reply_text(f"✅ User {user_id} unblocked.")
        else:
            await update.message.reply_text("❌ This user is not blocked.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: /unblock <user_id>")

async def user_activity(update: Update, context: CallbackContext):
    """Admin command to check user activity."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    try:
        user_id = int(context.args[0])
        if user_id in user_message_counts:
            msg_count = len(user_message_counts[user_id])
            await update.message.reply_text(f"📊 User {user_id} sent {msg_count} messages recently.")
        else:
            await update.message.reply_text("✅ This user has not sent messages recently.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: /user_activity <user_id>")

async def set_limit(update: Update, context: CallbackContext):
    """Admin command to change rate limits dynamically."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    try:
        global MESSAGE_LIMIT, TIME_WINDOW
        MESSAGE_LIMIT = int(context.args[0])
        TIME_WINDOW = int(context.args[1])
        await update.message.reply_text(f"✅ Rate limits updated: {MESSAGE_LIMIT} messages per {TIME_WINDOW} seconds.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: /set_limit <messages> <time>")
