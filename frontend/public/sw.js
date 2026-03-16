const CACHE_VERSION = 'v5-20260316';
const CACHE_NAME = `zektrix-${CACHE_VERSION}`;
const STATIC_CACHE = `zektrix-static-${CACHE_VERSION}`;
const IMG_CACHE = `zektrix-img-${CACHE_VERSION}`;

// Static assets to pre-cache
const PRECACHE_URLS = [
    '/',
    '/manifest.json',
    '/favicon.png',
    '/icon-192.png'
];

// Install - pre-cache essential assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => {
            return cache.addAll(PRECACHE_URLS);
        }).then(() => self.skipWaiting())
    );
});

// Activate - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME && key !== STATIC_CACHE && key !== IMG_CACHE)
                    .map((key) => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch strategy
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Skip non-GET requests and API calls
    if (event.request.method !== 'GET') return;
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) return;
    if (url.hostname !== self.location.hostname) return;
    
    // Images: cache-first with long TTL
    if (event.request.destination === 'image' || url.pathname.match(/\.(png|jpg|jpeg|webp|svg|gif|ico)$/)) {
        event.respondWith(
            caches.open(IMG_CACHE).then((cache) => {
                return cache.match(event.request).then((cached) => {
                    if (cached) return cached;
                    return fetch(event.request).then((response) => {
                        if (response.ok) cache.put(event.request, response.clone());
                        return response;
                    });
                });
            })
        );
        return;
    }
    
    // JS/CSS: stale-while-revalidate (serve cache, update in background)
    if (url.pathname.match(/\.(js|css)$/) && url.pathname.includes('/static/')) {
        event.respondWith(
            caches.open(STATIC_CACHE).then((cache) => {
                return cache.match(event.request).then((cached) => {
                    const fetchPromise = fetch(event.request).then((response) => {
                        if (response.ok) cache.put(event.request, response.clone());
                        return response;
                    }).catch(() => cached);
                    return cached || fetchPromise;
                });
            })
        );
        return;
    }
    
    // HTML pages: network-first (always try fresh, fallback to cache)
    event.respondWith(
        fetch(event.request).then((response) => {
            if (response.ok) {
                const clone = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
            }
            return response;
        }).catch(() => {
            return caches.match(event.request).then((cached) => {
                return cached || caches.match('/');
            });
        })
    );
});

// Push notifications
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : { title: 'Zektrix UK', body: 'Ai o notificare nouă!' };
    event.waitUntil(
        self.registration.showNotification(data.title || 'Zektrix UK', {
            body: data.body || '',
            icon: '/icon-192.png',
            badge: '/icon-96.png',
            vibrate: [100, 50, 100],
            data: { url: data.url || '/' },
            actions: data.actions || []
        })
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(clients.openWindow(event.notification.data.url || '/'));
});
