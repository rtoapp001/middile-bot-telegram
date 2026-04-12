from aiogram import types
import logging

logger = logging.getLogger(__name__)

class UIHelper:
    """Helper for creating better UI with inline keyboards"""
    
    @staticmethod
    def get_start_keyboard() -> types.InlineKeyboardMarkup:
        """Main start menu keyboard"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("📱 APK Download", callback_data="get_apk"),
            types.InlineKeyboardButton("📊 My Stats", callback_data="my_stats")
        )
        keyboard.add(
            types.InlineKeyboardButton("❓ Help", callback_data="help"),
            types.InlineKeyboardButton("ℹ️ About", callback_data="about")
        )
        return keyboard
    
    @staticmethod
    def get_help_message() -> str:
        """Help message"""
        return """
🤖 **APK Download Bot - Help**

**कैसे APK download करें:**
1. Code भेजो (ex: U12345)
2. Bot APK को queue में लगाएगा
3. Processing के दौरान status मिलती रहेगी
4. APK ready हो तो file मिल जाएगी

**Commands:**
/start - मुख्य मेनू
/stats - आपका statistics
/help - यह सहायता
/about - Bot के बारे में

**Format:**
✅ Valid: U12345
❌ Invalid: U, 12345, ABC123

Questions? DM Support 👨‍💼
"""
    
    @staticmethod
    def get_about_message() -> str:
        """About message"""
        return """
ℹ️ **About Bot**

Bot का काम:
• Android APKs को encrypt करना
• Queue management
• Real-time status updates
• Multiple user support

**Features:**
🔒 Secure download
📊 Track statistics  
⚡ Fast delivery
🔄 Auto-restart on crash
📈 Analytics

Version: 2.0
Developed: 2026
"""
    
    @staticmethod
    def get_stats_message(stats: dict) -> str:
        """Format user stats"""
        if not stats:
            return "❌ कोई data नहीं"
        
        return f"""
📊 **Your Statistics**

📥 Total Downloads: {stats['downloads']}
📋 Total Requests: {stats['total_requests']}
✅ Completed: {stats['completed']}
📅 Joined: {stats['joined_at'][:10]}

Last Update: Just now
"""
    
    @staticmethod
    def get_admin_keyboard() -> types.InlineKeyboardMarkup:
        """Admin panel keyboard"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats"),
            types.InlineKeyboardButton("👥 Users", callback_data="admin_users")
        )
        keyboard.add(
            types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            types.InlineKeyboardButton("🚫 Block User", callback_data="admin_block")
        )
        return keyboard
    
    @staticmethod
    def get_stats_keyboard() -> types.InlineKeyboardMarkup:
        """Stats menu keyboard"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("↩️ Back", callback_data="back"))
        return keyboard
    
    @staticmethod
    def format_request_status(status: str) -> str:
        """Format request status with emoji"""
        status_map = {
            'pending': '⏳ Processing...',
            'in_queue': '📍 In Queue',
            'processing': '🔄 Processing',
            'completed': '✅ Completed',
            'error': '❌ Error'
        }
        return status_map.get(status, status)


class MessageFormatter:
    """Helper for formatting long messages"""
    
    @staticmethod
    def bold(text: str) -> str:
        return f"<b>{text}</b>"
    
    @staticmethod
    def italic(text: str) -> str:
        return f"<i>{text}</i>"
    
    @staticmethod
    def code(text: str) -> str:
        return f"<code>{text}</code>"
    
    @staticmethod
    def link(text: str, url: str) -> str:
        return f'<a href="{url}">{text}</a>'
    
    @staticmethod
    def format_welcome_message(username: str) -> str:
        """Format welcome message"""
        return f"""
👋 नमस्ते {username}!

🎉 Bot में आपका स्वागत है

📱 APK download करने के लिए:
`U12345` जैसे code भेजो

अन्य commands:
/stats - आपका statistics देखो
/help - सहायता लो
/about - Bot के बारे में जानो

Happy downloading! 🚀
"""
    
    @staticmethod
    def format_processing_message(code: str) -> str:
        """Format processing message"""
        return f"""
⏳ <b>Processing Request</b>

Code: <code>{code}</code>

Status: 🔄 Finding APK...

शीघ्र ही queue position मिलेगी 📍
"""
    
    @staticmethod
    def format_error_message(error_msg: str) -> str:
        """Format error message"""
        return f"""
❌ <b>Error Occurred</b>

Message: {error_msg}

Please try again or contact support.
"""


class InlineNotifications:
    """Notification helpers"""
    
    @staticmethod
    def show_notification(text: str, alert: bool = False) -> str:
        """Show notification"""
        return text
    
    @staticmethod
    def format_processing_notification(position: int, total: int) -> str:
        """Format processing notification"""
        percentage = int((position / total) * 100)
        progress_bar = "█" * (percentage // 10) + "░" * (10 - (percentage // 10))
        
        return f"""
📍 <b>Queue Position</b>

Position: {position}/{total}
Progress: {progress_bar} {percentage}%

Estimated time: {(total - position) * 2} minutes ⏱️
"""


# Initialize helpers
ui = UIHelper()
formatter = MessageFormatter()
notifications = InlineNotifications()
