# database.py
import sqlite3
from datetime import datetime
from typing import Optional, Tuple

class UserDatabase:
    def __init__(self, db_name: str = 'bot_users.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                         (user_id INTEGER PRIMARY KEY,
                          username TEXT,
                          first_name TEXT,
                          last_name TEXT,
                          first_seen TIMESTAMP,
                          last_seen TIMESTAMP,
                          usage_count INTEGER DEFAULT 1)''')
        self.conn.commit()
    
    # Updated tracking method
def track_user(self, user_id: int, **kwargs):
    """Smart tracking that handles partial user data"""
    self.cursor.execute(
        """INSERT OR REPLACE INTO users 
        (user_id, username, first_name, last_name, first_seen, last_seen, usage_count) 
        VALUES (?, ?, ?, ?, 
                COALESCE((SELECT first_seen FROM users WHERE user_id=?), CURRENT_TIMESTAMP),
                CURRENT_TIMESTAMP,
                COALESCE((SELECT usage_count FROM users WHERE user_id=?)+1, 1))""",
        (user_id, kwargs.get('username'), kwargs.get('first_name'), kwargs.get('last_name'), 
         user_id, user_id)
    )
    self.conn.commit()
    
    def get_user_stats(self) -> Tuple[int, int]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        cursor.execute('''SELECT COUNT(*) FROM users 
                        WHERE last_seen > datetime('now', '-30 days')''')
        active = cursor.fetchone()[0]
        return total, active
    
    def close(self):
        self.conn.close()

# Create the database instance that will be imported
user_db = UserDatabase()