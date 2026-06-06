const CACHE_NAME = 'guest258-cache-v3-mobile';
const STATIC_ASSETS = [
  '/',
  '/properties/explorar/',
  '/static/offline.html',
  '/static/manifest.json',
  '/static/css/guest258-ui.css',
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

function shouldBypassCache(url) {
  return url.pathname.startsWith('/admin/') ||
    url.pathname.startsWith('/258-admin/') ||
    url.pathname.startsWith('/login/') ||
    url.pathname.startsWith('/logout/') ||
    url.pathname.includes('/cadastro/') ||
    url.pathname.includes('/pagamentos/') ||
    url.pathname.includes('/reservas/') ||
    url.pathname.includes('/notificacoes/') ||
    url.pathname.includes('/mensagens/') ||
    url.pathname.includes('/suporte/') ||
    url.pathname.includes('/reviews/meus-favoritos/') ||
    url.pathname.includes('/proprietario/');
}

self.addEventListener('fetch', function(event) {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (shouldBypassCache(url)) return;

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).then(function(response) {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(function(cache) { cache.put(event.request, clone); });
        return response;
      }).catch(function() {
        return caches.match(event.request).then(function(cached) {
          return cached || caches.match('/static/offline.html');
        });
      })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(function(cached) {
      return cached || fetch(event.request).then(function(response) {
        if (!response || response.status !== 200 || response.type === 'opaque') return response;
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then(function(cache) { cache.put(event.request, responseClone); });
        return response;
      });
    }).catch(function() { return caches.match('/static/offline.html'); })
  );
});
