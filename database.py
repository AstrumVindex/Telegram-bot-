import sqlite3
from datetime import datetime
from typing import Optional, Tuple


class UserDatabase:
    def __init__(self, db_name: str = 'bot_users.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                usage_count INTEGER DEFAULT 1
            )
        ''')
        self.conn.commit()

    def track_user(self, user_id: int, **kwargs):
        """Track or update user info."""
        self.cursor.execute('''
            INSERT OR REPLACE INTO users (
                user_id, username, first_name, last_name,
                first_seen, last_seen, usage_count
            ) VALUES (
                ?, ?, ?, ?,
                COALESCE((SELECT first_seen FROM users WHERE user_id = ?), CURRENT_TIMESTAMP),
                CURRENT_TIMESTAMP,
                COALESCE((SELECT usage_count FROM users WHERE user_id = ?) + 1, 1)
            )
        ''', (
            user_id,
            kwargs.get('username'),
            kwargs.get('first_name'),
            kwargs.get('last_name'),
            user_id,  # for first_seen
            user_id   # for usage_count
        ))
        self.conn.commit()

    def get_user_stats(self) -> Tuple[int, int]:
        """Return total and active user count (active = last_seen within 30 days)."""
        self.cursor.execute("SELECT COUNT(*) FROM users")
        total_users = self.cursor.fetchone()[0]

        self.cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE last_seen > datetime('now', '-30 days')
        ''')
        active_users = self.cursor.fetchone()[0]

        return total_users, active_users

    def close(self):
        self.conn.close()


# Singleton instance to be used throughout the bot
user_db = UserDatabase()
