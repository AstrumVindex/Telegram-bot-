# import logging
# from telegram import Message
# from telegram.constants import ParseMode

# logger = logging.getLogger(__name__)

# class ProgressHandler:
#     def __init__(self):
#         self.active_trackers = {}

#     async def init_progress(self, update, context, initial_text="Starting download..."):
#         """Initialize progress tracking for a user"""
#         message = await update.effective_message.reply_text(initial_text)
#         self.active_trackers[update.effective_user.id] = {
#             'message': message,
#             'last_update': 0
#         }
#         return message

#     async def update_progress(self, user_id, progress, text="Downloading"):
#         """Update progress for a user"""
#         if user_id not in self.active_trackers:
#             return

#         progress_bar = "🟩" * (progress // 10) + "⬜" * (10 - (progress // 10))
#         try:
#             await self.active_trackers[user_id]['message'].edit_text(
#                 f"{text}...\n{progress_bar} {progress}%",
#                 parse_mode=ParseMode.MARKDOWN
#             )
#         except Exception as e:
#             logger.warning(f"Progress update failed: {e}")

#     async def complete_progress(self, user_id, completion_text="✅ Download complete!"):
#         """Mark progress as complete"""
#         if user_id not in self.active_trackers:
#             return

#         try:
#             await self.active_trackers[user_id]['message'].edit_text(completion_text)
#             self.cleanup_progress(user_id)
#         except Exception as e:
#             logger.error(f"Progress completion failed: {e}")

#     def cleanup_progress(self, user_id):
#         """Clean up progress tracking"""
#         if user_id in self.active_trackers:
#             del self.active_trackers[user_id]

# # Global instance to be imported
# progress_manager = ProgressHandler()