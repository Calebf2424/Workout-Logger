// static/service-worker.js
self.addEventListener('install', e => {
  console.log('Service Worker installed');
  e.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', e => {
  console.log('Service Worker activated');
  return self.clients.claim();
});

self.addEventListener('fetch', function(event) {
  // Allow default fetch behavior for now
});
