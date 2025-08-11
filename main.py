import asyncio
import os
import json
import sqlite3
import tempfile
import gzip
import logging
from io import BytesIO
from xml.etree import ElementTree as ET
from datetime import datetime
import base64
from threading import Thread

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.constants import ChatAction
import cairosvg
from PIL import Image
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import custom modules
from database import Database
from config import Config
from utils import SVGValidator, TGSConverter

# Create Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'status': 'running',
        'bot': 'SVGToTGS Bot',
        'message': 'Bot is running successfully!'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

class SVGToTGSBot:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.svg_validator = SVGValidator()
        self.tgs_converter = TGSConverter()
        self.pending_conversions = {}  # Store batch processing data
        
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Handle /start command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Register user in database
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_message = (
            "🎨 Welcome to SVGToTGS Bot!\n\n"
            "I can convert your 512×512 SVG files into TGS stickers for Telegram.\n\n"
            "📋 **Requirements:**\n"
            "• SVG files only\n"
            "• Exactly 512×512 pixels\n"
            "• Maximum 5MB file size\n"
            "• Batch processing supported\n\n"
            "📤 Just send me your SVG file(s) and I'll convert them to TGS!\n\n"
            "Use /help for more information."
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Handle /help command"""
        help_text = (
            "🔧 **How to use SVGToTGS Bot:**\n\n"
            "1️⃣ Send me SVG file(s) that are exactly 512×512 pixels\n"
            "2️⃣ Wait for conversion to complete\n"
            "3️⃣ Download your TGS sticker files\n\n"
            "📏 **Requirements:**\n"
            "• File format: SVG only\n"
            "• Dimensions: Exactly 512×512 pixels\n"
            "• File size: Maximum 5MB\n\n"
            "⚡ **Batch Processing:**\n"
            "Send multiple SVG files at once for batch conversion!\n\n"
            "❌ **Common Issues:**\n"
            "• Wrong dimensions → Resize to 512×512px\n"
            "• Not SVG format → Convert to SVG first\n"
            "• File too large → Optimize/compress SVG\n\n"
            "Need help? Contact support!"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: CallbackContext) -> None:
        """Handle document uploads"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if user is banned
        if self.db.is_user_banned(user_id):
            await update.message.reply_text("❌ You are banned from using this bot.")
            return
        
        document = update.message.document
        
        # Validate file type
        if not document.file_name.lower().endswith('.svg'):
            await update.message.reply_text(
                "❌ Please send only SVG files.\n"
                "Use /help for more information about requirements."
            )
            return
        
        # Validate file size
        if document.file_size > 5 * 1024 * 1024:  # 5MB
            await update.message.reply_text(
                "❌ File too large! Maximum size is 5MB.\n"
                "Please compress your SVG file and try again."
            )
            return
        
        # Initialize or update batch processing
        if user_id not in self.pending_conversions:
            self.pending_conversions[user_id] = {
                'files': [],
                'chat_id': chat_id,
                'timer': None,
                'status_message': None
            }
        
        # Add file to batch
        self.pending_conversions[user_id]['files'].append({
            'document': document,
            'message': update.message
        })
        
        # Cancel previous timer if exists
        if self.pending_conversions[user_id]['timer']:
            self.pending_conversions[user_id]['timer'].cancel()
        
        # Set new timer for batch processing (3 seconds delay)
        self.pending_conversions[user_id]['timer'] = asyncio.create_task(
            self.process_batch_after_delay(user_id, 3)
        )
    
    async def process_batch_after_delay(self, user_id: int, delay: int) -> None:
        """Process batch after delay"""
        await asyncio.sleep(delay)
        await self.process_user_batch(user_id)
    
    async def process_user_batch(self, user_id: int) -> None:
        """Process all files for a user"""
        if user_id not in self.pending_conversions:
            return
        
        batch_data = self.pending_conversions[user_id]
        files = batch_data['files']
        chat_id = batch_data['chat_id']
        
        if not files:
            return
        
        # Send initial status message
        status_message = await self.send_message(
            chat_id, "⏳ Please wait..."
        )
        
        await asyncio.sleep(3)  # Wait 3 seconds as requested
        
        # Update status with file count
        file_count = len(files)
        await self.edit_message(
            chat_id, status_message.message_id,
            f"🔄 Processing {file_count} file{'s' if file_count > 1 else ''}..."
        )
        
        successful_conversions = 0
        
        # Process each file
        for i, file_data in enumerate(files, 1):
            document = file_data['document']
            
            try:
                # Download file
                file_obj = await document.get_file()
                file_content = await file_obj.download_as_bytearray()
                
                # Validate SVG dimensions
                is_valid, error_msg = self.svg_validator.validate_svg(file_content)
                
                if not is_valid:
                    # Send error message for this specific file
                    await self.send_message(
                        chat_id,
                        f"❌ **{document.file_name}**: {error_msg}\n"
                        "Use /help for dimension requirements."
                    )
                    continue
                
                # Convert to TGS
                tgs_data = await self.tgs_converter.convert_svg_to_tgs(file_content)
                
                if tgs_data:
                    # Create TGS filename
                    tgs_filename = document.file_name.rsplit('.', 1)[0] + '.tgs'
                    
                    # Send TGS file
                    await self.send_document(
                        chat_id, tgs_data, tgs_filename
                    )
                    successful_conversions += 1
                else:
                    await self.send_message(
                        chat_id,
                        f"❌ **{document.file_name}**: Conversion failed. Please try again."
                    )
                
                # Update progress
                await self.edit_message(
                    chat_id, status_message.message_id,
                    f"🔄 Processing {i}/{file_count} files..."
                )
                
            except Exception as e:
                logger.error(f"Error processing file {document.file_name}: {e}")
                await self.send_message(
                    chat_id,
                    f"❌ **{document.file_name}**: Processing error occurred."
                )
        
        # Final status update
        if successful_conversions > 0:
            await self.edit_message(
                chat_id, status_message.message_id,
                f"✅ Done! Successfully converted {successful_conversions}/{file_count} file{'s' if file_count > 1 else ''}."
            )
        else:
            await self.edit_message(
                chat_id, status_message.message_id,
                "❌ No files were successfully converted."
            )
        
        # Clean up
        del self.pending_conversions[user_id]
        
        # Log activity
        self.db.log_conversion_activity(user_id, file_count, successful_conversions)
    
    async def broadcast_command(self, update: Update, context: CallbackContext) -> None:
        """Admin command to broadcast message"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **Broadcast Command Usage:**\n\n"
                "`/broadcast <message>`\n\n"
                "You can also reply to a message (text, photo, video, or document) "
                "with `/broadcast` to forward it to all users."
            )
            return
        
        # Get message to broadcast
        if update.message.reply_to_message:
            # Broadcasting replied message
            reply_msg = update.message.reply_to_message
            users = self.db.get_all_users()
            
            success_count = 0
            for user_id, _, _, _ in users:
                try:
                    if reply_msg.text:
                        await context.bot.send_message(user_id, reply_msg.text)
                    elif reply_msg.photo:
                        await context.bot.send_photo(
                            user_id, reply_msg.photo[-1].file_id, 
                            caption=reply_msg.caption
                        )
                    elif reply_msg.video:
                        await context.bot.send_video(
                            user_id, reply_msg.video.file_id,
                            caption=reply_msg.caption
                        )
                    elif reply_msg.document:
                        await context.bot.send_document(
                            user_id, reply_msg.document.file_id,
                            caption=reply_msg.caption
                        )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send broadcast to user {user_id}: {e}")
        else:
            # Broadcasting text message
            message = ' '.join(context.args)
            users = self.db.get_all_users()
            
            success_count = 0
            for user_id, _, _, _ in users:
                try:
                    await context.bot.send_message(user_id, message)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send broadcast to user {user_id}: {e}")
        
        await update.message.reply_text(
            f"📢 Broadcast sent to {success_count} users."
        )
    
    async def ban_command(self, update: Update, context: CallbackContext) -> None:
        """Admin command to ban user"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/ban <user_id>`", parse_mode='Markdown')
            return
        
        try:
            user_id = int(context.args[0])
            self.db.ban_user(user_id)
            await update.message.reply_text(f"✅ User {user_id} has been banned.")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error banning user: {str(e)}")
    
    async def unban_command(self, update: Update, context: CallbackContext) -> None:
        """Admin command to unban user"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/unban <user_id>`", parse_mode='Markdown')
            return
        
        try:
            user_id = int(context.args[0])
            self.db.unban_user(user_id)
            await update.message.reply_text(f"✅ User {user_id} has been unbanned.")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error unbanning user: {str(e)}")
    
    async def stats_command(self, update: Update, context: CallbackContext) -> None:
        """Admin command to view stats"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        total_users = self.db.get_user_count()
        banned_users = self.db.get_banned_user_count()
        active_users = total_users - banned_users
        total_conversions = self.db.get_total_conversions()
        
        stats_text = (
            "📊 **Bot Statistics:**\n\n"
            f"👥 Total Users: {total_users}\n"
            f"✅ Active Users: {active_users}\n"
            f"🚫 Banned Users: {banned_users}\n"
            f"🔄 Total Conversions: {total_conversions}\n\n"
            f"📅 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.config.ADMIN_IDS
    
    async def send_message(self, chat_id: int, text: str):
        """Send message helper"""
        return await self.application.bot.send_message(
            chat_id, text, parse_mode='Markdown'
        )
    
    async def edit_message(self, chat_id: int, message_id: int, text: str):
        """Edit message helper"""
        try:
            await self.application.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, 
                text=text, parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
    
    async def send_document(self, chat_id: int, document_data: bytes, filename: str):
        """Send document helper"""
        await self.application.bot.send_document(
            chat_id, document=BytesIO(document_data), filename=filename
        )
    
    async def error_handler(self, update: object, context: CallbackContext) -> None:
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")

# Global bot instance
bot_instance = None

def run_bot():
    """Initialize and run the bot"""
    global bot_instance
    bot_instance = SVGToTGSBot()
    
    # Create application
    application = Application.builder().token(bot_instance.config.BOT_TOKEN).build()
    bot_instance.application = application
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot_instance.start))
    application.add_handler(CommandHandler("help", bot_instance.help_command))
    application.add_handler(CommandHandler("broadcast", bot_instance.broadcast_command))
    application.add_handler(CommandHandler("ban", bot_instance.ban_command))
    application.add_handler(CommandHandler("unban", bot_instance.unban_command))
    application.add_handler(CommandHandler("stats", bot_instance.stats_command))
    application.add_handler(MessageHandler(filters.Document.ALL, bot_instance.handle_document))
    
    # Add error handler
    application.add_error_handler(bot_instance.error_handler)
    
    logger.info("Bot started successfully!")
    
    # Run the bot with polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Start Flask server in a separate thread
    def run_flask():
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask web server started on port 5000")
    
    # Run the bot in the main thread
    run_bot()
