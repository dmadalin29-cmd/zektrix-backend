const CACHE_VERSION = 'v8-20260321';
const CACHE_NAME = `zektrix-${CACHE_VERSION}`;
const STATIC_CACHE = `zektrix-static-${CACHE_VERSION}`;
const IMG_CACHE = `zektrix-img-${CACHE_VERSION}`;

const PRECACHE_URLS = [
    '/',
    '/manifest.json',
    '/favicon.png',
    '/icon-192.png'
];

// Install
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => cache.addAll(PRECACHE_URLS))
            .then(() => self.skipWaiting())
    );
});

// Activate - clean old caches aggressively
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => !key.includes(CACHE_VERSION))
                    .map((key) => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch strategy
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    if (event.request.method !== 'GET') return;
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) return;
    if (url.hostname !== self.location.hostname) return;

    // Images: cache-first
    if (event.request.destination === 'image' || url.pathname.match(/\.(png|jpg|jpeg|webp|svg|gif|ico)$/)) {
        event.respondWith(
            caches.open(IMG_CACHE).then((cache) => {
                return cache.match(event.request).then((cached) => {
                    if (cached) return cached;
                    return fetch(event.request).then((response) => {
                        if (response.ok) cache.put(event.request, response.clone());
                        return response;
                    }).catch(() => cached);
                });
            })
        );
        return;
    }

    // JS/CSS: network-first
    if (url.pathname.match(/\.(js|css)$/) && url.pathname.includes('/static/')) {
        event.respondWith(
            fetch(event.request).then((response) => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(STATIC_CACHE).then((cache) => cache.put(event.request, clone));
                }
                return response;
            }).catch(() => caches.open(STATIC_CACHE).then((cache) => cache.match(event.request)))
        );
        return;
    }

    // HTML: network-first
    event.respondWith(
        fetch(event.request).then((response) => {
            if (response.ok) {
                const clone = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
            }
            return response;
        }).catch(() => caches.match(event.request).then((cached) => cached || caches.match('/')))
    );
});

// ====== PUSH NOTIFICATIONS ======
self.addEventListener('push', (event) => {
    let data = { title: 'Zektrix UK', body: 'Ai o notificare noua!' };
    
    try {
        if (event.data) {
            const parsed = event.data.json();
            data = { ...data, ...parsed };
        }
    } catch (e) {
        // If JSON parsing fails, try text
        if (event.data) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body || '',
        icon: data.icon || '/icon-192.png',
        badge: '/icon-96.png',
        image: data.image || undefined,
        vibrate: [200, 100, 200, 100, 200],
        tag: data.tag || 'zektrix-notification',
        renotify: true,
        requireInteraction: data.requireInteraction !== false,
        silent: false,
        data: {
            url: data.url || 'https://zektrix.uk',
            dateOfArrival: Date.now()
        },
        actions: data.actions || [
            { action: 'open', title: data.actionTitle || 'Deschide' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'Zektrix UK', options)
    );
});

// Notification click - open the app
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    const urlToOpen = event.notification.data?.url || 'https://zektrix.uk';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
            // Try to focus an existing window
            for (const client of windowClients) {
                if (client.url.includes('zektrix') && 'focus' in client) {
                    client.navigate(urlToOpen);
                    return client.focus();
                }
            }
            // Otherwise open a new window
            return clients.openWindow(urlToOpen);
        })
    );
});

// Notification close tracking
self.addEventListener('notificationclose', (event) => {
    // Could track dismissed notifications
});

// Background sync (for offline actions)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-notifications') {
        event.waitUntil(Promise.resolve());
    }
});

// Listen for skip waiting messages
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
