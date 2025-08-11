# SVGToTGS Bot

## Overview

This is a production-ready Telegram bot that converts SVG files to TGS sticker format. The bot accepts 512×512 pixel SVG files and converts them to the TGS format required for Telegram stickers. It features batch processing capabilities, admin management tools, and comprehensive user management through a SQLite database.

## User Preferences

Preferred communication style: Simple, everyday language.
Configuration preference: Bot token and admin IDs must be easily editable in code for GitHub deployment.

## System Architecture

### Bot Framework
- **Technology**: Python with python-telegram-bot library for Telegram Bot API integration
- **Pattern**: Event-driven architecture using handlers for commands and messages
- **Rationale**: Provides robust async support and comprehensive Telegram API coverage

### File Processing Pipeline
- **Validation**: SVGValidator class ensures files meet 512×512 pixel requirements and size limits
- **Conversion**: TGSConverter handles SVG to TGS transformation using cairosvg and PIL
- **Batch Processing**: Supports multiple file uploads with sequential processing and delivery
- **Rationale**: Modular design separates concerns and enables easier testing and maintenance

### Data Storage
- **Database**: SQLite with custom Database class wrapper
- **Schema**: Two main tables - users (profile and ban status) and conversions (activity tracking)
- **Rationale**: SQLite chosen for simplicity and self-contained deployment, sufficient for bot-scale operations

### Configuration Management
- **Pattern**: Environment variable-based configuration through Config class
- **Settings**: Bot token, admin IDs, file size limits, dimensions, and processing delays
- **Rationale**: Enables deployment flexibility and security through externalized configuration

### Admin Features
- **Commands**: Broadcast messaging, user banning/unbanning, and statistics viewing
- **Authorization**: Role-based access using admin ID list validation
- **Rationale**: Provides operational control and monitoring capabilities for bot administrators

### Error Handling
- **File Validation**: Comprehensive SVG dimension and format checking
- **User Feedback**: Clear error messages and processing status updates
- **Logging**: Structured logging throughout the application
- **Rationale**: Ensures robust operation and good user experience

## External Dependencies

### Core Libraries
- **python-telegram-bot**: Telegram Bot API wrapper for bot functionality
- **cairosvg**: SVG to raster image conversion engine
- **PIL (Pillow)**: Image processing and manipulation
- **xml.etree.ElementTree**: SVG XML parsing for validation

### System Dependencies
- **SQLite**: Embedded database for user and conversion data
- **gzip**: File compression for TGS format generation
- **tempfile**: Temporary file handling during conversion process

### Telegram Bot API
- **Bot Token**: Required for authentication with Telegram services
- **File Upload/Download**: Direct integration with Telegram's file handling system
- **Message Handling**: Real-time message processing and response delivery