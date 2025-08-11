# SVGToTGS Bot

A production-ready Telegram bot that converts 512×512 SVG files to TGS stickers with batch processing and admin management features.

## 🚀 Quick Setup

### 1. Configure Bot Token and Admin IDs

Open `config.py` and add your bot token and admin user ID:

```python
# Bot Token - Get from @BotFather on Telegram
DEFAULT_BOT_TOKEN = "123456789:AABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh"  # ← PUT YOUR BOT TOKEN HERE

# Admin User IDs - Get your Telegram user ID from @userinfobot
DEFAULT_ADMIN_IDS = [123456789]  # ← PUT YOUR ADMIN USER IDS HERE
```

### 2. Get Your Bot Token
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Copy the token that looks like: `123456789:AABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh`
4. Paste it in `config.py`

### 3. Get Your Admin User ID
1. Open Telegram and search for `@userinfobot`
2. Send `/start` to get your user ID (number like: `123456789`)
3. Add it to the `DEFAULT_ADMIN_IDS` list in `config.py`

### 4. Run the Bot
```bash
pip install python-telegram-bot==20.7 cairosvg Pillow
python main.py
```

## ✨ Features

### Core Functionality
- ✅ Accepts only SVG files that are exactly 512×512 pixels and under 5MB
- 🔄 Batch processing: handles multiple SVG files sent together
- 📤 Sequential delivery of converted TGS files without multiple reply messages
- ⏱️ Real-time status updates during conversion process
- 🎨 Converts SVG files to TGS format for Telegram stickers

### Admin Features (Admin Only)
- 📢 `/broadcast <message>` - Send messages to all users (supports text, images, videos, files)
- 🚫 `/ban <user_id>` - Ban users from using the bot
- ✅ `/unban <user_id>` - Unban previously banned users
- 📊 `/stats` - View total users, banned users, and conversion statistics

### User Commands
- `/start` - Welcome message and bot information
- `/help` - Detailed usage instructions and requirements

### User Experience
1. Bot responds with "Please wait..." for 3 seconds
2. Shows processing count: "Processing X files..."
3. Final message shows "Done ✅" before sending TGS files
4. Comprehensive error handling for invalid files and dimensions

## 🔧 Configuration Options

You can configure the bot either by:
1. **Direct code editing** (easiest for GitHub): Edit values in `config.py`
2. **Environment variables** (best for hosting): Set environment variables

### Environment Variables
```bash
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
MAX_FILE_SIZE=5242880
REQUIRED_WIDTH=512
REQUIRED_HEIGHT=512
LOG_LEVEL=INFO
```

## 📋 Requirements

### Python Dependencies
- `python-telegram-bot==20.7` - Telegram Bot API wrapper
- `cairosvg` - SVG to image conversion
- `Pillow` - Image processing
- `xml.etree.ElementTree` - SVG parsing (built-in)

### System Dependencies (for hosting)
- Cairo graphics library
- Pango text rendering
- GDK-PixBuf image loading

## 🚀 Deployment

### For GitHub + Render.com
1. Fork/upload this repository to GitHub
2. Edit `config.py` directly on GitHub to add your bot token and admin ID
3. Connect your GitHub repo to Render.com
4. Use these build settings:
   ```
   Build Command: pip install -r render_requirements.txt
   Start Command: python main.py
   ```

### For Other Hosting Platforms
1. Set environment variables for `BOT_TOKEN` and `ADMIN_IDS`
2. Install system dependencies: `cairo`, `pango`, `gdk-pixbuf`
3. Install Python dependencies: `pip install -r render_requirements.txt`
4. Run: `python main.py`

## 📁 Project Structure

```
svgtotgs-bot/
├── main.py          # Main bot application
├── config.py        # Configuration (EDIT HERE for GitHub)
├── database.py      # SQLite database management
├── utils.py         # SVG validation and TGS conversion
├── render_requirements.txt # Python dependencies for deployment
└── README.md        # This file
```

## 🔍 How It Works

1. **File Validation**: Checks SVG dimensions (512×512px) and file size (<5MB)
2. **Batch Processing**: Collects multiple files sent together
3. **SVG to TGS Conversion**: 
   - Converts SVG to PNG using CairoSVG
   - Creates Lottie animation JSON with the image
   - Compresses to TGS format (gzipped Lottie)
4. **User Management**: SQLite database tracks users and conversions
5. **Admin Tools**: Broadcasting, user management, and statistics

## 🐛 Troubleshooting

### Bot Won't Start
- Check that your bot token is correctly set in `config.py`
- Verify the token format: `123456789:AABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh`

### Conversion Fails
- Ensure SVG files are exactly 512×512 pixels
- Check file size is under 5MB
- Verify SVG format is valid

### Admin Commands Not Working
- Check your user ID is in the `DEFAULT_ADMIN_IDS` list
- Get your correct user ID from @userinfobot on Telegram

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the configuration in `config.py`
3. Ensure all requirements are properly installed
