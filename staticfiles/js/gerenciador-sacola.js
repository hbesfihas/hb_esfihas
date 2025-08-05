// Arquivo: static/js/gerenciador-sacola.js (Versão Final e Unificada)

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

    // --- ROTEADOR DE PÁGINA ---
    // Verifica em qual página estamos e executa o código correspondente.

    // SE ESTIVER NA PÁGINA INICIAL (home.html)
    if (document.getElementById('listaSacola')) {

        // NOVA FUNÇÃO DE VALIDAÇÃO
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
        validarSacolaAoCarregar(); // 1. Valida a sacola PRIMEIRO
        renderizarSacolaHome();   // 2. DEPOIS, renderiza a sacola já limpa
    }

    // SE ESTIVER NA PÁGINA INICIAL (home.html)
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

    // SE ESTIVER NA PÁGINA DE RESUMO (resumo.html)
    const pageResumo = document.getElementById('listaResumo');
    if (pageResumo) {
        const sacola = JSON.parse(localStorage.getItem('sacola') || '{}');
        const subtotalEl = document.getElementById('subtotalValor'),
            freteEl = document.getElementById('freteValor'),
            taxaEl = document.getElementById('taxaValor'),
            totalEl = document.getElementById('totalValor'),
            linhaTaxaEl = document.getElementById('linhaTaxaCartao'),
            linhaFreteEl = document.getElementById('linhaFrete'),
            contadorItensEl = document.getElementById('contadorItens'),
            tipoEntregaSelect = document.getElementById('tipoEntrega'),
            camposEntregaDiv = document.getElementById('camposEntrega'),
            bairroSelect = document.getElementById('selectBairro'),
            formEl = document.getElementById('formPedido'),
            inputSacolaEl = document.getElementById('inputSacola'),
            radiosPagamento = document.querySelectorAll('input[name="forma_pagamento"]');

        function renderizarListaResumo() {
            let e = 0; pageResumo.innerHTML = "";
            if (Object.keys(sacola).length === 0) {
                pageResumo.innerHTML = '<li class="list-group-item">Sua sacola está vazia.</li>';
                formEl.querySelector('button[type="submit"]').disabled = true
            } else {
                for (const t in sacola) {
                    const o = sacola[t];
                    e += o.quantidade; const l = document.createElement('li');
                    l.className = "list-group-item d-flex justify-content-between lh-sm";
                    l.innerHTML = `<div><h6 class="my-0">${o.nome}</h6><small class="text-muted">Quantidade: ${o.quantidade}</small></div><span class="text-muted">R$ ${(parseFloat(o.preco) * o.quantidade).toFixed(2)}</span>`;
                    pageResumo.appendChild(l)
                }
            } contadorItensEl.textContent = e
        }
        function atualizarTotaisResumo() {
            let e = 0;
            for (const t in sacola) e += parseFloat(sacola[t].preco) * parseInt(sacola[t].quantidade);
            let t = 0;
            if (tipoEntregaSelect.value === 'entrega') {
                const e = bairroSelect.options[bairroSelect.selectedIndex];
                t = parseFloat(e.getAttribute('data-frete') || 0);
                linhaFreteEl.classList.remove('escondido');
            } else {
                t = 0;
                linhaFreteEl.classList.add('escondido');
            }

            const o = document.getElementById('credito');

            let l = 0;

            if (o.checked) {
                linhaTaxaEl.classList.remove('escondido');
                const n = parseFloat(o.getAttribute('data-taxa') || 0);
                l = (e + t) * (n / 100);
            } else {
                linhaTaxaEl.classList.add('escondido');
                l = 0;
            }
            const n = e + t + l;
            subtotalEl.textContent = `R$ ${e.toFixed(2)}`;
            freteEl.textContent = `R$ ${t.toFixed(2)}`;
            taxaEl.textContent = `R$ ${l.toFixed(2)}`;
            totalEl.textContent = `R$ ${n.toFixed(2)}`;
        }
        tipoEntregaSelect.addEventListener('change', () => {
            const e = tipoEntregaSelect.value === 'entrega';
            camposEntregaDiv.style.display = e ? 'block' : 'none';
            bairroSelect.required = e;
            if (!e) bairroSelect.value = "";
            atualizarTotaisResumo()
        });

        bairroSelect.addEventListener('change', atualizarTotaisResumo);

        formEl.addEventListener('submit', () => { inputSacolaEl.value = JSON.stringify(sacola) });
        renderizarListaResumo();
        atualizarTotaisResumo();

        // Função para gerenciar o visual dos botões selecionados
        function gerenciarEscolha(radioInputs) {
            radioInputs.forEach(radio => {
                const card = radio.closest('.choice-card');
                if (radio.checked) card.classList.add('selected');
                else card.classList.remove('selected');
            });
        }

        // Função para mostrar/esconder o campo de troco
        function gerenciarCampoTroco() {
            const pagamentoDinheiro = document.querySelector('input[name="forma_pagamento"][value="dinheiro"]');
            const campoTrocoDiv = document.getElementById('campo-troco'); // Campo de troco
        
            if (pagamentoDinheiro.checked) {
                campoTrocoDiv.style.display = 'block';
            } else {
                campoTrocoDiv.style.display = 'none';
            }
        }
        radiosPagamento.forEach(radio => {
            radio.addEventListener('change', () => {
                gerenciarEscolha(radiosPagamento);
                gerenciarCampoTroco();
                atualizarTotaisResumo()
            });
        });
    }
}); 