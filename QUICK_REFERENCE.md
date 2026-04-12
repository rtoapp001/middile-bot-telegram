# ⚡ Quick Reference - Multi-User Bot

## 🚀 Start Bot
```bash
cd /Users/vivekkumar/Desktop/manage/middile\ bot\ telegram
python3 main_bot.py
```

## 📊 View Stats (Admin)
```bash
# Telegram में
/admin

# या Terminal से
sqlite3 bot_database.db
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM requests;
```

## 🔧 Rate Limit Config
**File:** `rate_limiter.py`
```python
MAX_REQUESTS_PER_HOUR = 10
MAX_REQUESTS_PER_DAY = 50
COOLDOWN_SECONDS = 60
```

## 📁 New Files
- `database.py` - User & request tracking
- `rate_limiter.py` - Rate limiting
- `ui_helper.py` - UI components & formatting
- `bot_database.db` - SQLite database (auto-created)

## 🎨 Customize Messages
**File:** `ui_helper.py`
- `get_welcome_message()` - Welcome text
- `get_help_message()` - Help text
- `get_about_message()` - About text
- Color/emoji: Edit directly in functions

## 📝 Database Backup
```bash
# Backup
cp bot_database.db bot_database.db.backup

# Restore
cp bot_database.db.backup bot_database.db

# Export
sqlite3 bot_database.db ".mode csv" ".output data.csv" "SELECT * FROM users;"
```

## 🛡️ Block User (Admin)
Edit `main_bot.py` and add:
```python
@dp.message_handler(commands=["block"])
async def block_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_id = int(message.get_args())
    db.block_user(user_id)
    await message.reply(f"✅ User {user_id} blocked")
```

## 📊 Admin Commands
```
/start   - Welcome menu
/stats   - Your stats
/admin   - Admin panel (requires ADMIN_ID)
/help    - Help
/about   - About
```

## 🔍 Monitoring
```bash
# Real-time logs
tail -f bot.log

# Count requests
watch "sqlite3 bot_database.db 'SELECT status, COUNT(*) FROM requests GROUP BY status;'"

# Check database size
du -h bot_database.db
```

## 🆘 Troubleshooting
```bash
# Check if database corrupted
sqlite3 bot_database.db "PRAGMA integrity_check;"

# Optimize database
sqlite3 bot_database.db "VACUUM;"

# Clear old data (30 days)
sqlite3 bot_database.db "DELETE FROM requests WHERE completed_at < datetime('now', '-30 days');"
```

## 💾 Database Schema
```sql
-- Users
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    joined_at TIMESTAMP,
    total_downloads INTEGER,
    is_blocked INTEGER,
    last_request_at TIMESTAMP
);

-- Requests
CREATE TABLE requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    requested_at TIMESTAMP,
    status TEXT,
    queue_position INTEGER,
    completed_at TIMESTAMP
);

-- Queue Status
CREATE TABLE queue_status (
    request_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    queue_message TEXT,
    updated_at TIMESTAMP
);
```

## 🎯 Key Functions
```python
# database.py
db.add_user(user_id, username, first_name)
db.create_request(user_id, code)
db.update_request_status(request_id, status)
db.complete_request(request_id)
db.get_user_stats(user_id)
db.get_admin_stats()
db.is_user_blocked(user_id)
db.block_user(user_id)

# rate_limiter.py
rate_limiter.check_rate_limit(user_id)
rate_limiter.get_user_limits(user_id)

# ui_helper.py
ui.get_start_keyboard()
formatter.bold(text)
formatter.format_welcome_message(name)
notifications.format_processing_notification(pos, total)
```

## 🌐 Special Features

### Inline Keyboard Buttons
Already implemented in:
- `/start` - Shows menu
- `/stats` - Shows stats
- `/help` - Help button
- `/about` - About button

### Rate Limiting Smart Messages
Hindi/Urdu messages automatically shown:
```
⏳ कृपया 45 सेकंड रुकें
(Please wait 45 seconds)
```

### Request Tracking
Each request gets:
- Unique request_id
- Status tracking
- Completion time
- User reference

## ✨ What's Happening Behind the Scenes

1. **User sends code** → Database creates request
2. **Bot sends to android_protect_bot** → Status tracks as "in_queue"
3. **Status updates come** → User gets real-time messages
4. **APK ready** → Sent to user, marked "completed"
5. **Stats updated** → Database increments user downloads

## 🚀 Deploy to Cloud (Optional)
```bash
# Heroku
git init
git add .
git commit -m "Bot with advanced features"
heroku create your-bot-name
git push heroku main
heroku logs -t

# Or AWS Lambda
# Or Digital Ocean
# Or any VPS
```

## 📞 Quick Debug
```bash
# Most common issues
grep -E "ERROR|ERROR|block_user|rate_limit" bot.log

# Check specific user
sqlite3 bot_database.db "SELECT * FROM users WHERE user_id=123456789;"

# Check pending requests
sqlite3 bot_database.db "SELECT * FROM requests WHERE status='pending';"
```

---

**Everything ready to go!** 🎉

Any questions? Check `ADVANCED_FEATURES.md` for detailed guide.
