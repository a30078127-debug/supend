// Supend Service Worker — Push уведомления
const CACHE = 'supend-v1';

self.addEventListener('install', e => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(clients.claim());
});

// Обработка push-уведомлений
self.addEventListener('push', e => {
  let data = { title: 'Supend', body: 'Новое сообщение', icon: '/logo', badge: '/logo' };
  try { if (e.data) data = { ...data, ...e.data.json() }; } catch(err) {}
  e.waitUntil(
    self.registration.showNotification(data.title, {
      body:    data.body,
      icon:    data.icon || '/logo',
      badge:   data.badge || '/logo',
      tag:     data.tag || 'supend-msg',
      renotify: true,
      vibrate: [200, 100, 200],
      data:    data,
    })
  );
});

// Клик на уведомление — открываем/фокусируем приложение
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if (c.url.includes(self.location.origin)) return c.focus();
      }
      return clients.openWindow('/');
    })
  );
});
