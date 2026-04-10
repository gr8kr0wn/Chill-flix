/* ═══════════════════════════════════════════════════
   CHILLFLIX SERVICE WORKER — OFFLINE PWA
════════════════════════════════════════════════════ */

const CACHE_NAME = 'chillflix-v3';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/auth.html',
  '/movies.html',
  '/movie.html',
  '/watch.html',
  '/watchlist.html',
  '/settings.html',
  '/profile.html',
  '/upgrade.html',
  '/search.html',
  '/history.html',
  '/person.html',
  '/downloads.html',
  '/watch-party.html',
  '/error.html',
  '/manifest.json',
  'https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600;700&display=swap',
  'https://cdn.tailwindcss.com'
];

// Install event — cache all core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching core assets');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event — clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== 'chillflix-videos') {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event — serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Skip TMDB API and YouTube — let them go to network
  if (url.hostname.includes('tmdb.org') || 
      url.hostname.includes('youtube.com') || 
      url.hostname.includes('googlevideo.com') ||
      url.hostname.includes('ytimg.com')) {
    return;
  }
  
  // Handle HTML navigation requests (SPA fallback)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match('/error.html');
        })
    );
    return;
  }
  
  // Cache-first strategy for static assets
  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        
        return fetch(event.request)
          .then((networkResponse) => {
            // Cache new assets for future offline use
            if (networkResponse && networkResponse.status === 200) {
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseClone);
              });
            }
            return networkResponse;
          })
          .catch(() => {
            // Return a fallback for failed requests
            if (event.request.destination === 'image') {
              return new Response(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 300"><rect width="200" height="300" fill="#141420"/><text x="100" y="160" text-anchor="middle" fill="#8a8aaa" font-size="40">🎬</text></svg>',
                { headers: { 'Content-Type': 'image/svg+xml' } }
              );
            }
            return null;
          });
      })
  );
});

// Background sync for offline actions (premium feature)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-watch-history') {
    event.waitUntil(syncWatchHistory());
  }
});

async function syncWatchHistory() {
  // This would sync offline watch history when back online
  console.log('[SW] Syncing watch history...');
}

// Push notifications (premium feature — can be added later)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data?.text() || 'New movie added to Chillflix!',
    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect width="192" height="192" rx="32" fill="%230a0a0f"/><text x="96" y="128" font-size="72" font-weight="900" fill="%23e50914" text-anchor="middle">C</text></svg>',
    badge: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><circle cx="96" cy="96" r="96" fill="%23e50914"/></svg>',
    vibrate: [200, 100, 200]
  };
  
  event.waitUntil(
    self.registration.showNotification('Chillflix', options)
  );
});