# 🤖 Bot 24/7 Setup Guide

## समस्या (Problem)
Bot automatically बंद हो जा रहा है। आप इसे 24/7 चलाना चाहते हो।

## समाधान (Solution)

### विकल्प 1: मैनुअल तरीका (Simple - Terminal)
```bash
cd /Users/vivekkumar/Desktop/manage/middile\ bot\ telegram
chmod +x run.sh
./run.sh
```
यह terminal में bot चलाएगा और अगर crash हो तो auto-restart कर देगा।

---

### विकल्प 2: macOS LaunchAgent (Best - 24/7 Automatic)
यह तरीका system startup पर bot को automatically शुरू करेगा।

#### Step 1: logs folder बनाओ
```bash
mkdir -p /Users/vivekkumar/Desktop/manage/middile\ bot\ telegram/logs
```

#### Step 2: LaunchAgent register करो
```bash
cp /Users/vivekkumar/Desktop/manage/middile\ bot\ telegram/com.telegrambot.middle.plist ~/Library/LaunchAgents/

# File permissions सेट करो
chmod 644 ~/Library/LaunchAgents/com.telegrambot.middle.plist

# Bot load करो
launchctl load ~/Library/LaunchAgents/com.telegrambot.middle.plist
```

#### Step 3: Bot status चेक करो
```bash
# Bot चल रहा है या नहीं देखो
launchctl list | grep telegrambot

# Logs देखो
tail -f /Users/vivekkumar/Desktop/manage/middile\ bot\ telegram/logs/bot.log
tail -f /Users/vivekkumar/Desktop/manage/middile\ bot\ telegram/logs/bot_error.log

# भी bot.log देखो (main_bot.py में बनता है)
tail -f /Users/vivekkumar/Desktop/manage/middile\ bot\ telegram/bot.log
```

---

### विकल्प 3: Screen/Tmux (Temporary - अगर Mac बंद न हो)
```bash
# Screen session में चलाओ
screen -S telegram_bot
cd /Users/vivekkumar/Desktop/manage/middile\ bot\ telegram
python3 main_bot.py

# Detach करने के लिए: Ctrl + A फिर D
# Reattach करने के लिए: screen -r telegram_bot
```

---

## Bot को बंद करना
```bash
# LaunchAgent से remove करो
launchctl unload ~/Library/LaunchAgents/com.telegrambot.middle.plist
```

---

## Improvements किए गए:

✅ **Auto-restart**: अगर bot crash हो तो automatically restart होगा  
✅ **Logging**: सभी errors bot.log में save होंगे  
✅ **Error Handling**: बेहतर error handling  
✅ **Graceful Shutdown**: cleanly बंद हो सकता है  

---

## Troubleshooting

### Bot शुरू नहीं हो रहा?
```bash
# LaunchAgent logs देखो
log stream --predicate 'process == "python3"' --level debug

# या manually run करो to check errors
python3 main_bot.py
```

### Bot बार-बार crash हो रहा है?
```bash
# bot.log को पूरा पढ़ो
cat /Users/vivekkumar/Desktop/manage/middile\ bot\ telegram/bot.log
```

---

## Important Notes:
- Mac बंद न हो तो LaunchAgent काम करेगा
- Production के लिए cloud server (AWS, Digital Ocean, Heroku) बेहतर है
- अभी local Mac में है तो 24/7 के लिए Mac को हमेशा on रखना होगा
