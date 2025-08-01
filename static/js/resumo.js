document.addEventListener('DOMContentLoaded', () => {
    // === SELETORES DE ELEMENTOS ===
    const listaResumoEl = document.getElementById('listaResumo');
    const subtotalEl = document.getElementById('subtotalValor');
    const freteEl = document.getElementById('freteValor');
    const taxaEl = document.getElementById('taxaValor');
    const totalEl = document.getElementById('totalValor');
    const linhaTaxaEl = document.getElementById('linhaTaxaCartao');
    const contadorItensEl = document.getElementById('contadorItens'); // <-- Contador

    const tipoEntregaSelect = document.getElementById('tipoEntrega');
    const camposEntregaDiv = document.getElementById('camposEntrega');
    const bairroSelect = document.getElementById('selectBairro');
    const formEl = document.getElementById('formPedido');
    const inputSacolaEl = document.getElementById('inputSacola');
    const radiosPagamento = document.querySelectorAll('input[name="forma_pagamento"]');

    // === CARREGAR DADOS ===
    const sacola = JSON.parse(localStorage.getItem('sacola') || '{}');

    // === FUNÇÕES ===

    function renderizarListaItens() {
        listaResumoEl.innerHTML = '';
        let totalItens = 0;
        if (Object.keys(sacola).length === 0) {
            listaResumoEl.innerHTML = '<li class="list-group-item">Sua sacola está vazia.</li>';
            formEl.querySelector('button[type="submit"]').disabled = true;
        } else {
            for (const id in sacola) {
                const item = sacola[id];
                totalItens += item.quantidade; // Soma a quantidade de cada item
                const itemLi = document.createElement('li');
                itemLi.className = 'list-group-item d-flex justify-content-between lh-sm';
                itemLi.innerHTML = `
                    <div>
                        <h6 class="my-0">${item.nome}</h6>
                        <small class="text-muted">Quantidade: ${item.quantidade}</small>
                    </div>
                    <span class="text-muted">R$ ${(parseFloat(item.preco) * item.quantidade).toFixed(2)}</span>
                `;
                listaResumoEl.appendChild(itemLi);
            }
        }
        contadorItensEl.textContent = totalItens; // Atualiza o contador
    }

    function atualizarTotais() {
        let subtotal = 0;
        for (const id in sacola) {
            // Verifica se o preço e a quantidade são números válidos
            const preco = parseFloat(sacola[id].preco);
            const quantidade = parseInt(sacola[id].quantidade);
            if (!isNaN(preco) && !isNaN(quantidade)) {
                subtotal += preco * quantidade;
            }
        }
        let frete = 0;
        if (tipoEntregaSelect.value === 'entrega') {
            const selectedBairro = bairroSelect.options[bairroSelect.selectedIndex];
            frete = parseFloat(selectedBairro.getAttribute('data-frete') || 0);
        }

        const pagamentoCredito = document.getElementById('credito');
        let taxa = 0;
        if (pagamentoCredito.checked) {
            linhaTaxaEl.classList.remove('escondido');
            const taxaPercentual = 5;
            taxa = (subtotal + frete) * (taxaPercentual / 100);
        } else {
            linhaTaxaEl.classList.add('escondido');
            taxa = 0;
        }

        const total = subtotal + frete + taxa;
        // Atualiza os valores na tela
        subtotalEl.textContent = `R$ ${subtotal.toFixed(2)}`;
        freteEl.textContent = `R$ ${frete.toFixed(2)}`;
        taxaEl.textContent = `R$ ${taxa.toFixed(2)}`;
        totalEl.textContent = `R$ ${total.toFixed(2)}`;

        console.log("HTML foi atualizado."); // <-- Adicione esta linha
    }

    // === EVENT LISTENERS ===
    tipoEntregaSelect.addEventListener('change', () => {
        const ehEntrega = tipoEntregaSelect.value === 'entrega';
        camposEntregaDiv.style.display = ehEntrega ? 'block' : 'none';
        bairroSelect.required = ehEntrega;
        if (!ehEntrega) { bairroSelect.value = ""; }
        atualizarTotais();
    });

    bairroSelect.addEventListener('change', atualizarTotais);
    radiosPagamento.forEach(radio => radio.addEventListener('change', atualizarTotais));

    formEl.addEventListener('submit', () => {
        inputSacolaEl.value = JSON.stringify(sacola);
    });

    // === INICIALIZAÇÃO ===
    renderizarListaItens();
    atualizarTotais();
});