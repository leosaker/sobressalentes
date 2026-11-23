// Service worker: permite abrir o app offline (rede primeiro, cache como reserva).
const CACHE = 'meu-personal-v2';
const ASSETS = ['./', './index.html', './config.js', './manifest.json', './icon.svg'];
const CDN = 'https://cdn.jsdelivr.net';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // Só o próprio app e a biblioteca do Supabase vão para o cache — nunca os dados da API.
  if (e.request.method !== 'GET' || (url.origin !== location.origin && url.origin !== CDN)) return;
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
      return r;
    }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || caches.match('./index.html')))
  );
});
