self.addEventListener('push', function (event) {
    console.log('[Service Worker] Push Recebido.');
    try {
        const data = event.data.json();
        const title = data.head;
        const options = {
            body: data.body,
            icon: data.icon,
            badge: data.icon,
            data: { url: data.url }
        };
        event.waitUntil(self.registration.showNotification(title, options));
    } catch (e) {
        console.error('[Service Worker] Erro ao processar o push:', e);
    }
});

self.addEventListener('notificationclick', function (event) {
    console.log('[Service Worker] Notificação clicada.');
    event.notification.close();
    event.waitUntil(clients.openWindow(event.notification.data.url));
});