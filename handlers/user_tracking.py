import logging

USER_TRACKING_FILE = "users.txt"

def track_user(user_id: int):
    """Track users who use the bot."""
    try:
        with open(USER_TRACKING_FILE, "a") as file:
            file.write(f"{user_id}\n")
    except Exception as e:
        logging.error(f"Error tracking user: {e}")
