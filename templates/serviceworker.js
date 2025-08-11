// Este ficheiro corre em segundo plano

// Ouve por mensagens "push" vindas do servidor
self.addEventListener('push', function (event) {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: data.icon,
        badge: data.icon, // Ícone para Android
        data: {
            url: data.url // URL para abrir ao clicar
        }
    };
    event.waitUntil(
        self.registration.showNotification(data.head, options)
    );
});

// O que fazer quando o utilizador clica na notificação
self.addEventListener('notificationclick', function (event) {
    event.notification.close(); // Fecha a notificação
    // Abre a janela do painel de gerente ou foca nela se já estiver aberta
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});