// Em static/js/gerenciador-sacola.js

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
    const enderecoInput = document.getElementById('endereco');
    const btnConfirmar = document.getElementById('btn-confirmar-pedido'); // Seletor para o botão
    const clienteUltimoBairro = document.getElementById('clienteUltimoBairro')?.value || null;
    console.log("Cliente último bairro:", clienteUltimoBairro);

    // --- Funções ---
    function renderizarListaResumo() {
        let totalItens = 0;
        pageResumo.innerHTML = "";
        if (Object.keys(sacola).length === 0) {
            pageResumo.innerHTML = '<li class="list-group-item">Sua sacola está vazia.</li>';
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
        // ... (esta função continua exatamente como a sua, sem alterações) ...
        let subtotal = 0;
        for (const id in sacola) {
            subtotal += parseFloat(sacola[id].preco) * parseInt(sacola[id].quantidade);
        }
        let frete = 0;
        const entregaSelecionada = document.querySelector('input[name="tipo_entrega"]:checked')?.value === 'entrega';
        if (entregaSelecionada) {
            linhaFreteEl.classList.remove('escondido');
            const selectedBairro = bairroSelect.options[bairroSelect.selectedIndex];
            frete = parseFloat(selectedBairro.getAttribute('data-frete') || 0);
        } else {
            linhaFreteEl.classList.add('escondido');
            frete = 0;
        }
        const pagamentoCredito = document.getElementById('credito');
        let taxa = 0;
        if (pagamentoCredito && pagamentoCredito.checked) {
            linhaTaxaEl.classList.remove('escondido');
            const taxaPercentual = parseFloat(pagamentoCredito.getAttribute('data-taxa') || 0);
            taxa = (subtotal + frete) * (taxaPercentual / 100);
        } else {
            linhaTaxaEl.classList.add('escondido');
            taxa = 0;
        }
        const total = subtotal + frete + taxa;
        subtotalEl.textContent = `R$ ${subtotal.toFixed(2)}`;
        freteEl.textContent = `R$ ${frete.toFixed(2)}`;
        taxaEl.textContent = `R$ ${taxa.toFixed(2)}`;
        totalEl.textContent = `R$ ${total.toFixed(2)}`;
    }

    function gerenciarEscolha(radioInputs) {
        // ... (esta função continua exatamente como a sua, sem alterações) ...
        radioInputs.forEach(radio => {
            const card = radio.closest('.choice-card');
            if (card) {
                if (radio.checked) card.classList.add('selected');
                else card.classList.remove('selected');
            }
        });
    }

    // --- NOVA FUNÇÃO DE VALIDAÇÃO ---
    function validarFormulario() {
        let isValido = true;
        const tipoEntrega = document.querySelector('input[name="tipo_entrega"]:checked');
        const formaPagamento = document.querySelector('input[name="forma_pagamento"]:checked');

        if (!formaPagamento) {
            isValido = false;
        }

        if (tipoEntrega && tipoEntrega.value === 'entrega') {
            if (!bairroSelect.value || !enderecoInput.value.trim()) {
                isValido = false;
            }
        }

        // Não pode finalizar com a sacola vazia
        if (Object.keys(sacola).length === 0) {
            isValido = false;
        }

        // Habilita ou desabilita o botão
        btnConfirmar.disabled = !isValido;
    }

    function gerenciarVisuais() {
        gerenciarEscolha(tipoEntregaRadios);
        gerenciarEscolha(radiosPagamento);
        const entregaSelecionada = document.querySelector('input[name="tipo_entrega"]:checked')?.value === 'entrega';
        camposEntregaDiv.style.display = entregaSelecionada ? 'block' : 'none';
        bairroSelect.required = entregaSelecionada;
        enderecoInput.required = entregaSelecionada;
        if (!entregaSelecionada) bairroSelect.value = clienteUltimoBairro || "";
        const pagamentoDinheiro = document.querySelector('input[name="forma_pagamento"][value="dinheiro"]');
        if (campoTrocoDiv && pagamentoDinheiro) {
            campoTrocoDiv.style.display = pagamentoDinheiro.checked ? 'block' : 'none';
        }
        atualizarTotaisResumo();
        validarFormulario(); // <-- Chama a validação aqui
    }

    // --- Listeners ---
    tipoEntregaRadios.forEach(radio => radio.addEventListener('change', gerenciarVisuais));
    radiosPagamento.forEach(radio => radio.addEventListener('change', gerenciarVisuais));

    bairroSelect.addEventListener('change', () => {
        atualizarTotaisResumo();
        validarFormulario();
    });
    // Adiciona o listener que faltava para o campo de endereço
    enderecoInput.addEventListener('input', validarFormulario);

    formEl.addEventListener('submit', () => {
        btnConfirmar.disabled = true;
        btnConfirmar.textContent = 'Enviando...';
        inputSacolaEl.value = JSON.stringify(sacola);
    });

    // --- Inicialização da Página ---
    renderizarListaResumo();
    // Verifica se o Django já selecionou um bairro.
    const bairroJaSelecionado = bairroSelect.value !== "";

    if (bairroJaSelecionado) {
        // Se sim, marca o radio 'entrega' como selecionado no código
        document.querySelector('input[name="tipo_entrega"][value="entrega"]').checked = true;
    }

    // Agora, chama a função principal que atualiza todo o visual
    // Ela vai ler o estado dos botões (incluindo o que acabamos de marcar) e agir de acordo
    gerenciarVisuais();
}