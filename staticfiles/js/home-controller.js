// Ficheiro: static/js/home-controller.js (O seu código funcional + a nova lógica de scroll)

// =================================================================================
// FUNÇÕES GLOBAIS - Acessíveis em todo o site
// =================================================================================

// Função para pegar o token CSRF dos cookies do navegador
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

// Função global para adicionar/remover itens, chamada pelos botões `onclick` na home
window.updateCart = function (produtoId, action) {
    const productCard = document.querySelector(`.product-card[data-id='${produtoId}']`);
    if (!productCard) return;

    let sacola = JSON.parse(localStorage.getItem('sacola') || '{}');
    const nome = productCard.getAttribute('data-nome');
    const preco = productCard.getAttribute('data-preco');

    if (!(produtoId in sacola)) {
        sacola[produtoId] = { quantidade: 0, nome: nome, preco: preco };
    }

    if (action === 'add') sacola[produtoId].quantidade += 1;
    else if (action === 'remove') sacola[produtoId].quantidade -= 1;

    if (sacola[produtoId]?.quantidade <= 0) delete sacola[produtoId];

    localStorage.setItem('sacola', JSON.stringify(sacola));
    renderizarSacolaHome();
}

// Função para renderizar a sacola na PÁGINA INICIAL
function renderizarSacolaHome() {
    const listaSacolaHome = document.getElementById('listaSacola');
    if (!listaSacolaHome) return;

    let sacola = JSON.parse(localStorage.getItem('sacola') || '{}');
    listaSacolaHome.innerHTML = '';
    let subtotal = 0;

    for (const id in sacola) {
        const item = sacola[id];
        subtotal += parseFloat(item.preco) * item.quantidade;
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center py-1 px-2';
        li.innerHTML = `<small>${item.quantidade}x ${item.nome}</small> <small>R$ ${(parseFloat(item.preco) * item.quantidade).toFixed(2)}</small>`;
        listaSacolaHome.appendChild(li);
    }

    document.getElementById('totalSacola').textContent = subtotal.toFixed(2);

    document.querySelectorAll('.product-card').forEach(card => {
        const id = card.getAttribute('data-id');
        const controlsContainer = card.querySelector(`#controls-${id}`);
        if (!controlsContainer) return;

        const estoque = parseInt(controlsContainer.getAttribute('data-estoque'));
        const qtdNaSacola = sacola[id]?.quantidade || 0;

        if (estoque > 0) {
            controlsContainer.innerHTML = qtdNaSacola > 0
                ? `<button class="btn btn-outline-danger btn-sm" onclick="updateCart('${id}', 'remove')">−</button> <span class="mx-2">${qtdNaSacola}</span> <button class="btn btn-outline-success btn-sm" onclick="updateCart('${id}', 'add')">+</button>`
                : `<button class="btn btn-primary btn-sm" onclick="updateCart('${id}', 'add')">Adicionar</button>`;
        } else {
            controlsContainer.innerHTML = `<button class="btn btn-secondary btn-sm" disabled>Esgotado</button>`;
        }
    });
}

// =================================================================================
// LÓGICA EXECUTADA QUANDO A PÁGINA É CARREGADA
// =================================================================================
document.addEventListener('DOMContentLoaded', () => {

    // SE ESTIVER NA PÁGINA INICIAL (home.html)
    const accordionElement = document.getElementById('accordionCategorias');
    if (accordionElement) {

        // --- VALIDAÇÃO DA SACOLA ---
        function validarSacolaAoCarregar() {
            console.log("Validando sacola contra o estoque atual...");
            let sacola = JSON.parse(localStorage.getItem('sacola') || '{}');
            const itensNaPagina = document.querySelectorAll('.product-card');
            let sacolaFoiModificada = false;
            let itensRemovidos = [];

            // Cria um mapa de estoque para consulta rápida
            const mapaDeEstoque = {};
            itensNaPagina.forEach(card => {
                const id = card.dataset.id;
                const estoqueDiv = card.querySelector(`#controls-${id}`);
                const estoque = parseInt(estoqueDiv.dataset.estoque);
                mapaDeEstoque[id] = estoque;
            });

            // Itera sobre os itens na sacola
            for (const id in sacola) {
                const estoqueAtual = mapaDeEstoque[id];
                // Remove se o produto não existe mais na página ou se o estoque é zero
                if (estoqueAtual === undefined || estoqueAtual <= 0) {
                    itensRemovidos.push(sacola[id].nome); // Guarda o nome para o alerta
                    delete sacola[id];
                    sacolaFoiModificada = true;
                }
            }

            // Se a sacola foi alterada, salva a nova versão e avisa o usuário
            if (sacolaFoiModificada) {
                localStorage.setItem('sacola', JSON.stringify(sacola));
                alert(`Alguns itens da sua sacola ficaram sem estoque e foram removidos:\n\n- ${itensRemovidos.join('\n- ')}`);
            }
        }

        // --- INICIALIZAÇÃO DA PÁGINA INICIAL ---
        validarSacolaAoCarregar();
        renderizarSacolaHome();

        // --- LÓGICA DO SCROLL SUAVE DO ACCORDION (CORRIGIDA E DEFINITIVA) ---
        // "Ouve" o evento que o Bootstrap dispara DEPOIS de um item ser mostrado
        accordionElement.addEventListener('shown.bs.collapse', function (event) {
            // 'event.target' é o div .accordion-collapse que acabou de abrir.
            // O que queremos é o cabeçalho que vem antes dele.
            const header = event.target.previousElementSibling;

            if (header) {
                // Rola suavemente para que o topo do cabeçalho
                // fique alinhado com o topo da janela.
                header.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });

        // --- Listener do botão finalizar ---
        const btnFinalizar = document.getElementById('btn-finalizar-pedido');
        if (btnFinalizar) {
            renderizarSacolaHome(); // Renderiza a sacola ao carregar a página

            btnFinalizar.addEventListener('click', () => {
                const sacola = JSON.parse(localStorage.getItem('sacola') || '{}');
                if (Object.keys(sacola).length === 0) {
                    alert("Sua sacola está vazia!");
                    return;
                }

                btnFinalizar.textContent = 'Verificando estoque...';
                btnFinalizar.disabled = true;
                const csrftoken = getCookie('csrftoken'); // Pega o token de segurança

                fetch('/api/validar-estoque/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify(sacola)
                })
                    .then(response => response.json().then(data => ({ ok: response.ok, data })))
                    .then(({ ok, data }) => {
                        if (ok) {
                            window.location.href = "/finalizar/"; // Redireciona se o estoque estiver OK
                        } else {
                            alert(data.message);
                            btnFinalizar.textContent = 'Finalizar Pedido';
                            btnFinalizar.disabled = false;
                        }
                    })
                    .catch(error => {
                        console.error('Erro na requisição de validação:', error);
                        alert('Ocorreu um erro ao verificar o estoque. Tente novamente.');
                        btnFinalizar.textContent = 'Finalizar Pedido';
                        btnFinalizar.disabled = false;
                    });
            });
        }
    }


});