import sqlite3
import logging
from datetime import datetime
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        is_banned INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Conversion activity table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        files_requested INTEGER,
                        files_converted INTEGER,
                        conversion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, last_activity)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name, datetime.now()))
                
                conn.commit()
                logger.info(f"User {user_id} added/updated in database")
                
        except sqlite3.Error as e:
            logger.error(f"Error adding user {user_id}: {e}")
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                
                return result[0] == 1 if result else False
                
        except sqlite3.Error as e:
            logger.error(f"Error checking ban status for user {user_id}: {e}")
            return False
    
    def ban_user(self, user_id: int):
        """Ban a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    'UPDATE users SET is_banned = 1 WHERE user_id = ?', 
                    (user_id,)
                )
                
                if cursor.rowcount == 0:
                    # User doesn't exist, create entry
                    cursor.execute('''
                        INSERT INTO users (user_id, is_banned) VALUES (?, 1)
                    ''', (user_id,))
                
                conn.commit()
                logger.info(f"User {user_id} banned successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Error banning user {user_id}: {e}")
    
    def unban_user(self, user_id: int):
        """Unban a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    'UPDATE users SET is_banned = 0 WHERE user_id = ?', 
                    (user_id,)
                )
                
                conn.commit()
                logger.info(f"User {user_id} unbanned successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Error unbanning user {user_id}: {e}")
    
    def get_all_users(self) -> List[Tuple[int, str, str, str]]:
        """Get all non-banned users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT user_id, username, first_name, last_name 
                    FROM users 
                    WHERE is_banned = 0
                ''')
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def get_user_count(self) -> int:
        """Get total user count"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM users')
                result = cursor.fetchone()
                
                return result[0] if result else 0
                
        except sqlite3.Error as e:
            logger.error(f"Error getting user count: {e}")
            return 0
    
    def get_banned_user_count(self) -> int:
        """Get banned user count"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 1')
                result = cursor.fetchone()
                
                return result[0] if result else 0
                
        except sqlite3.Error as e:
            logger.error(f"Error getting banned user count: {e}")
            return 0
    
    def log_conversion_activity(self, user_id: int, files_requested: int, files_converted: int):
        """Log conversion activity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO conversions (user_id, files_requested, files_converted)
                    VALUES (?, ?, ?)
                ''', (user_id, files_requested, files_converted))
                
                conn.commit()
                logger.info(f"Logged conversion activity for user {user_id}")
                
        except sqlite3.Error as e:
            logger.error(f"Error logging conversion activity: {e}")
    
    def get_total_conversions(self) -> int:
        """Get total conversion count"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT SUM(files_converted) FROM conversions')
                result = cursor.fetchone()
                
                return result[0] if result and result[0] else 0
                
        except sqlite3.Error as e:
            logger.error(f"Error getting total conversions: {e}")
            return 0
    
    def update_user_activity(self, user_id: int):
        """Update user's last activity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    'UPDATE users SET last_activity = ? WHERE user_id = ?',
                    (datetime.now(), user_id)
                )
                
                conn.commit()
                
        except sqlite3.Error as e:
            logger.error(f"Error updating activity for user {user_id}: {e}")
