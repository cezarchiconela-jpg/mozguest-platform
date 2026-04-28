const CACHE_NAME = 'mozguest-cache-v2';
const STATIC_ASSETS = [
  '/',
  '/properties/explorar/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

self.addEventListener('install', function(event) {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(STATIC_ASSETS).catch(function() { return null; });
    })
  );
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.filter(function(key) { return key !== CACHE_NAME; }).map(function(key) { return caches.delete(key); }));
    }).then(function() { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(event) {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/admin/') || url.pathname.startsWith('/moz-admin/') || url.pathname.startsWith('/login/') || url.pathname.startsWith('/logout/') || url.pathname.includes('/cadastro/')) {
    return;
  }
  event.respondWith(
    fetch(event.request).then(function(response) {
      if (!response || response.status !== 200 || response.type === 'opaque') return response;
      const responseClone = response.clone();
      caches.open(CACHE_NAME).then(function(cache) { cache.put(event.request, responseClone); });
      return response;
    }).catch(function() { return caches.match(event.request); })
  );
});
