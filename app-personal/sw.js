// Service worker: app offline (rede primeiro, cache como reserva) e notificações no celular.
// Arquivos de marca antigos usam "window.MARCA"; no service worker "window" não existe.
self.window = self;
try { importScripts('marca.js'); } catch (e) { /* sem marca: usa os padrões */ }
const MARCA = self.MARCA || {};
const CACHE = 'meu-personal-v7';
const ASSETS = ['./', './index.html', './marca.js', './config.js', './manifest.json', './icon-192.png', './badge-96.png', './vendor/qrcode.js'].concat([MARCA.logo, MARCA.logoEscuro].filter(Boolean).map(f => './' + f));
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

// ---- Notificações ----
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch { d = { body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || MARCA.nome || 'Meu Personal', {
    body: d.body || '', icon: 'icon-192.png', badge: 'badge-96.png',
    tag: d.tag || undefined, renotify: !!d.tag, data: { url: d.url || './' }
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = new URL((e.notification.data && e.notification.data.url) || './', self.registration.scope).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
    const open = list.find(c => c.url.startsWith(self.registration.scope));
    if (open) { open.postMessage({ open: url }); return open.focus(); }
    return self.clients.openWindow(url);
  }));
});
