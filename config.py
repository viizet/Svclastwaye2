import os
import logging
from typing import List

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        """Initialize configuration from environment variables or defaults"""
        
        # =================================================================
        # EASY CONFIGURATION - Change these values directly on GitHub
        # =================================================================
        
        # Bot Token - Get from @BotFather on Telegram
        # Example: "123456789:AABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh"
        DEFAULT_BOT_TOKEN = "8435159197:AAG4xNOnPbB2Aqj7wou8NM01JRerjABJ7ao"  # ← PUT YOUR BOT TOKEN HERE
        
        # Admin User IDs - Get your Telegram user ID from @userinfobot
        # You can add multiple admin IDs separated by commas
        # Example: [123456789, 987654321]
        DEFAULT_ADMIN_IDS = [1096693642]  # ← PUT YOUR ADMIN USER IDS HERE
        
        # =================================================================
        # Bot token (priority: environment variable, then default)
        self.BOT_TOKEN = os.getenv('BOT_TOKEN', DEFAULT_BOT_TOKEN)
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN not set! Please add your bot token in config.py or set BOT_TOKEN environment variable")
        
        # Admin user IDs (priority: environment variable, then default)
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if admin_ids_str:
            try:
                self.ADMIN_IDS = [int(uid.strip()) for uid in admin_ids_str.split(',') if uid.strip()]
            except ValueError as e:
                logger.error(f"Invalid ADMIN_IDS format: {e}")
                self.ADMIN_IDS = DEFAULT_ADMIN_IDS
        else:
            self.ADMIN_IDS = DEFAULT_ADMIN_IDS
        
        # File size limits
        self.MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '5242880'))  # 5MB default
        
        # SVG validation settings
        self.REQUIRED_WIDTH = int(os.getenv('REQUIRED_WIDTH', '512'))
        self.REQUIRED_HEIGHT = int(os.getenv('REQUIRED_HEIGHT', '512'))
        
        # Database settings
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot_database.db')
        
        # Conversion settings
        self.BATCH_DELAY = int(os.getenv('BATCH_DELAY', '3'))  # seconds
        
        # Logging level
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.LOG_LEVEL = getattr(logging, log_level, logging.INFO)
        
        logger.info("Configuration loaded successfully")
        logger.info(f"Admin IDs: {self.ADMIN_IDS}")
        logger.info(f"Max file size: {self.MAX_FILE_SIZE} bytes")
        logger.info(f"Required dimensions: {self.REQUIRED_WIDTH}x{self.REQUIRED_HEIGHT}")
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.ADMIN_IDS
    
    def add_admin(self, user_id: int):
        """Add admin user ID"""
        if user_id not in self.ADMIN_IDS:
            self.ADMIN_IDS.append(user_id)
            logger.info(f"Added admin: {user_id}")
    
    def remove_admin(self, user_id: int):
        """Remove admin user ID"""
        if user_id in self.ADMIN_IDS:
            self.ADMIN_IDS.remove(user_id)
            logger.info(f"Removed admin: {user_id}")
