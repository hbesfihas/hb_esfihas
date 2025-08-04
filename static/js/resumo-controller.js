// Em static/js/gerenciador-sacola.js

// --- LÓGICA EXCLUSIVA DA PÁGINA DE RESUMO ---
const pageResumo = document.getElementById('listaResumo');
if (pageResumo) {

    // --- Seletores de Elementos ---
    const sacola = JSON.parse(localStorage.getItem('sacola') || '{}');
    const subtotalEl = document.getElementById('subtotalValor');
    const freteEl = document.getElementById('freteValor');
    const taxaEl = document.getElementById('taxaValor');
    const totalEl = document.getElementById('totalValor');
    const linhaTaxaEl = document.getElementById('linhaTaxaCartao');
    const linhaFreteEl = document.getElementById('linhaFrete');
    const contadorItensEl = document.getElementById('contadorItens');
    const tipoEntregaRadios = document.querySelectorAll('input[name="tipo_entrega"]');
    const camposEntregaDiv = document.getElementById('camposEntrega');
    const bairroSelect = document.getElementById('selectBairro');
    const formEl = document.getElementById('formPedido');
    const inputSacolaEl = document.getElementById('inputSacola');
    const radiosPagamento = document.querySelectorAll('input[name="forma_pagamento"]');
    const campoTrocoDiv = document.getElementById('campo-troco');

    // --- Funções ---
    function renderizarListaResumo() {
        let totalItens = 0;
        pageResumo.innerHTML = "";
        if (Object.keys(sacola).length === 0) {
            pageResumo.innerHTML = '<li class="list-group-item">Sua sacola está vazia.</li>';
            formEl.querySelector('button[type="submit"]').disabled = true;
        } else {
            for (const id in sacola) {
                const item = sacola[id];
                totalItens += item.quantidade;
                const li = document.createElement('li');
                li.className = "list-group-item d-flex justify-content-between lh-sm";
                li.innerHTML = `<div><h6 class="my-0">${item.nome}</h6><small class="text-muted">Quantidade: ${item.quantidade}</small></div><span class="text-muted">R$ ${(parseFloat(item.preco) * item.quantidade).toFixed(2)}</span>`;
                pageResumo.appendChild(li);
            }
        }
        contadorItensEl.textContent = totalItens;
    }

    function atualizarTotaisResumo() {
        let subtotal = 0;
        for (const id in sacola) {
            subtotal += parseFloat(sacola[id].preco) * parseInt(sacola[id].quantidade);
        }

        // LÓGICA DE VISIBILIDADE DO FRETE
        let frete = 0;
        const entregaSelecionada = document.querySelector('input[name="tipo_entrega"]:checked').value === 'entrega';
        if (entregaSelecionada) {
            linhaFreteEl.classList.remove('escondido'); // MOSTRA a linha
            const selectedBairro = bairroSelect.options[bairroSelect.selectedIndex];
            frete = parseFloat(selectedBairro.getAttribute('data-frete') || 0);
        } else {
            linhaFreteEl.classList.add('escondido'); // ESCONDE a linha
            frete = 0;
        }

        // LÓGICA DE VISIBILIDADE DA TAXA DO CARTÃO
        const pagamentoCredito = document.getElementById('credito');
        let taxa = 0;
        if (pagamentoCredito.checked) {
            linhaTaxaEl.classList.remove('escondido'); // MOSTRA a linha
            const taxaPercentual = parseFloat(pagamentoCredito.getAttribute('data-taxa') || 0);
            taxa = (subtotal + frete) * (taxaPercentual / 100);
        } else {
            linhaTaxaEl.classList.add('escondido'); // ESCONDE a linha
            taxa = 0;
        }

        const total = subtotal + frete + taxa;
        subtotalEl.textContent = `R$ ${subtotal.toFixed(2)}`;
        freteEl.textContent = `R$ ${frete.toFixed(2)}`;
        taxaEl.textContent = `R$ ${taxa.toFixed(2)}`;
        totalEl.textContent = `R$ ${total.toFixed(2)}`;
    }

    function gerenciarEscolha(radioInputs) {
        radioInputs.forEach(radio => {
            const card = radio.closest('.choice-card');
            if (card) {
                if (radio.checked) card.classList.add('selected');
                else card.classList.remove('selected');
            }
        });
    }

    function gerenciarVisuais() {
        gerenciarEscolha(tipoEntregaRadios);
        gerenciarEscolha(radiosPagamento);
        const entregaSelecionada = document.querySelector('input[name="tipo_entrega"]:checked').value === 'entrega';
        camposEntregaDiv.style.display = entregaSelecionada ? 'block' : 'none';
        bairroSelect.required = entregaSelecionada;
        if (!entregaSelecionada) bairroSelect.value = "";
        const pagamentoDinheiro = document.querySelector('input[name="forma_pagamento"][value="dinheiro"]');
        if (campoTrocoDiv) {
            campoTrocoDiv.style.display = pagamentoDinheiro.checked ? 'block' : 'none';
        }
        atualizarTotaisResumo();
    }

    // --- Listeners ---
    tipoEntregaRadios.forEach(radio => radio.addEventListener('change', gerenciarVisuais));
    radiosPagamento.forEach(radio => radio.addEventListener('change', gerenciarVisuais));
    bairroSelect.addEventListener('change', atualizarTotaisResumo);
    formEl.addEventListener('submit', () => { inputSacolaEl.value = JSON.stringify(sacola); });
    
    // --- Inicialização da Página ---
    renderizarListaResumo();
    gerenciarVisuais();
    if (bairroSelect.value || document.querySelector('input[name="endereco"]').value) {
        document.querySelector('input[name="tipo_entrega"][value="entrega"]').click();
    }
}