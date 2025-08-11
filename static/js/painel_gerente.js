document.addEventListener('DOMContentLoaded', () => {

    const listaPedidosEl = document.getElementById('lista-pedidos');
    const somNotificacao = document.getElementById('som-notificacao');
    const toggleLojaCheckbox = document.getElementById('toggle-loja-checkbox');
    const statusAbertaEl = document.getElementById('status-aberta');
    const statusFechadaEl = document.getElementById('status-fechada');

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    function atualizarVisualStatusLoja(lojaAberta) {
        if (!statusAbertaEl || !statusFechadaEl || !toggleLojaCheckbox) return;
        if (lojaAberta) {
            statusAbertaEl.style.opacity = '1';
            statusFechadaEl.style.opacity = '0.3';
            toggleLojaCheckbox.checked = true;
        } else {
            statusAbertaEl.style.opacity = '0.3';
            statusFechadaEl.style.opacity = '1';
            toggleLojaCheckbox.checked = false;
        }
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${wsProtocol}://${window.location.host}/ws/painel-gerente/`);

    socket.onopen = () => console.log("✅ Conexão WebSocket estabelecida.");
    socket.onclose = () => console.error("❌ Socket fechado.");

    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        if (data.type === 'new_order') {
            if (somNotificacao) somNotificacao.play().catch(err => console.warn("Som bloqueado.", err));
            const msgSemPedidos = document.getElementById('sem-pedidos-msg');
            if (msgSemPedidos) msgSemPedidos.remove();
            listaPedidosEl.insertAdjacentHTML('afterbegin', data.pedido_html);
        }
        if (data.type === 'status_update') {
            const { pedido_id, novo_status, nova_cor_classe } = data.message;
            const cardPedido = document.getElementById(`pedido-${pedido_id}`);
            const statusElement = document.getElementById(`status-text-${pedido_id}`);
            if (cardPedido && statusElement) {
                statusElement.textContent = novo_status;
                const classesDeCor = ['bg-light', 'bg-warning', 'bg-info', 'bg-primary', 'bg-success', 'bg-secondary', 'text-dark', 'text-white', 'bg-opacity-10', 'bg-opacity-25', 'bg-opacity-50', 'bg-opacity-75'];
                cardPedido.classList.remove(...classesDeCor);
                cardPedido.classList.add(...nova_cor_classe.split(' '));
            }
            if (novo_status === 'Cancelado') {
                console.log(`🗑️ Removendo pedido cancelado #${pedido_id} da tela.`);

                // Adiciona uma animação suave
                cardPedido.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                cardPedido.style.opacity = '0';
                cardPedido.style.transform = 'scale(0.95)';

                // Remove o elemento do HTML depois que a animação terminar
                setTimeout(() => { cardPedido.remove(); }, 500);
            }
        }
        if (data.type === 'store_status_update') {
            atualizarVisualStatusLoja(data.message.loja_aberta);
        }
    };

    if (toggleLojaCheckbox) {
        toggleLojaCheckbox.addEventListener('change', () => {
            const url = '/api/toggle-loja-status/';
            fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken }
            })
                .then(response => response.json())
                .then(data => {
                    atualizarVisualStatusLoja(data.loja_aberta);
                })
                .catch(error => console.error('Erro ao mudar status da loja:', error));
        });
    }

    if (listaPedidosEl) {
        listaPedidosEl.addEventListener('click', function (event) {
            const target = event.target;
            if (target && target.classList.contains('btn-atualizar-status')) {
                const pedidoId = target.dataset.pedidoId;
                const novoStatus = target.dataset.novoStatus;
                const url = `/atualizar-status/${pedidoId}/${novoStatus}/`;
                fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrftoken } });
            }
            if (target && target.classList.contains('btn-imprimir-pedido')) {
                const pedidoId = target.dataset.pedidoId;
                const url = `/imprimir-pedido/${pedidoId}/`;
                const iframeAntigo = document.getElementById('iframe-impressao');
                if (iframeAntigo) iframeAntigo.remove();
                const iframe = document.createElement('iframe');
                iframe.id = 'iframe-impressao';
                iframe.style.display = 'none';
                document.body.appendChild(iframe);
                iframe.src = url;
                iframe.onload = function () {
                    try {
                        iframe.contentWindow.focus();
                        iframe.contentWindow.print();
                    } catch (error) {
                        console.error('Erro ao tentar imprimir:', error);
                    }
                };
            }
            if (target && target.classList.contains('btn-toggle-pago')) {
                const button = target;
                const pedidoId = button.dataset.pedidoId;
                const url = `/api/toggle-pago-status/${pedidoId}/`;
                fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrftoken } })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'ok') {
                            const statusBadge = document.getElementById(`status-pago-${pedidoId}`);
                            if (data.pago) {
                                statusBadge.textContent = 'PAGO';
                                statusBadge.classList.remove('bg-danger');
                                statusBadge.classList.add('bg-success');
                                button.textContent = 'Marcar como Não Pago';
                                button.classList.remove('btn-outline-success');
                                button.classList.add('btn-outline-danger');
                            } else {
                                statusBadge.textContent = 'NÃO PAGO';
                                statusBadge.classList.remove('bg-success');
                                statusBadge.classList.add('bg-danger');
                                button.textContent = 'Marcar como Pago';
                                button.classList.remove('btn-outline-danger');
                                button.classList.add('btn-outline-success');
                            }
                        }
                    });
            }
        });
    }

    if (toggleLojaCheckbox) {
        atualizarVisualStatusLoja(toggleLojaCheckbox.checked);
    }


});
// =================================================================================
// --- LÓGICA DE PUSH NOTIFICATIONS (separada para maior clareza) ---
// =================================================================================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// Função principal de subscrição (CORRIGIDA)
async function subscribeUserToPush() {
    try {
        const vapidKeyElement = document.getElementById('lista-pedidos');
        if (!vapidKeyElement) return;

        const vapidPublicKey = vapidKeyElement.dataset.vapidKey;
        if (!vapidPublicKey) {
            console.error("ERRO: VAPID Public Key está vazia no HTML!");
            return;
        }
        const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);

        // 1. Regista o Service Worker
        await navigator.serviceWorker.register('/serviceworker.js');
        console.log('Service Worker registado com sucesso.');

        // 2. ESPERA até que o Service Worker esteja pronto e ativo
        const registration = await navigator.serviceWorker.ready;
        console.log('Service Worker está ativo e pronto.');

        // 3. AGORA SIM, faz a subscrição com segurança
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
        });
        console.log('Subscrição Push obtida:', subscription);

        await fetch('/api/save-subscription/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(subscription),
        });
        console.log("Inscrito para notificações push com sucesso!");

    } catch (error) {
        console.error("Falha ao se inscrever para notificações push:", error);
    }
}


// Inicia o processo quando a página do painel carrega
if ('serviceWorker' in navigator && 'PushManager' in window) {
    Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
            console.log("Permissão para notificações concedida.");
            subscribeUserToPush();
        }
    });
}




