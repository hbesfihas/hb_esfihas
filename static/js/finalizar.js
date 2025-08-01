document.addEventListener('DOMContentLoaded', () => {
    // Pega os elementos do DOM
    const resumoSacolaEl = document.getElementById('resumoSacola');
    const subtotalEl = document.getElementById('subtotalValor');
    const freteEl = document.getElementById('freteValor');
    const taxaEl = document.getElementById('taxaValor');
    const totalEl = document.getElementById('totalValor');
    const selectBairro = document.getElementById('selectBairro');
    const formFinalizar = document.getElementById('formFinalizar');
    const sacolaInput = document.getElementById('sacola_json_input');

    // Carrega a sacola do localStorage
    const sacola = JSON.parse(localStorage.getItem('sacola') || '{}');

    // Função para renderizar a sacola na tela
    function renderizarSacola() {
        if (Object.keys(sacola).length === 0) {
            resumoSacolaEl.innerHTML = '<p>Sua sacola está vazia.</p>';
            return;
        }
        
        let html = '<ul class="list-group">';
        for (const id in sacola) {
            const item = sacola[id];
            html += `<li class="list-group-item">${item.quantidade}x ${item.nome}</li>`;
        }
        html += '</ul>';
        resumoSacolaEl.innerHTML = html;
        
        atualizarCalculos();
    }

    // Função para calcular e atualizar todos os valores
    function atualizarCalculos() {
        let subtotal = 0;
        for (const id in sacola) {
            subtotal += parseFloat(sacola[id].preco) * parseInt(sacola[id].quantidade);
        }

        // Calcula o frete
        const selectedOption = selectBairro.options[selectBairro.selectedIndex];
        const valorFrete = parseFloat(selectedOption.getAttribute('data-frete') || 0);

        // Calcula a taxa do cartão
        let valorTaxa = 0;
        const pagamentoCartao = document.getElementById('pagamentoCartao');
        if (pagamentoCartao.checked) {
            const taxaPercentual = parseFloat(pagamentoCartao.getAttribute('data-taxa') || 0);
            valorTaxa = (subtotal + valorFrete) * (taxaPercentual / 100);
        }

        const total = subtotal + valorFrete + valorTaxa;

        // Atualiza os valores na tela
        subtotalEl.textContent = subtotal.toFixed(2);
        freteEl.textContent = valorFrete.toFixed(2);
        taxaEl.textContent = valorTaxa.toFixed(2);
        totalEl.textContent = total.toFixed(2);
    }
    
    // Event Listeners para atualizar os cálculos dinamicamente
    selectBairro.addEventListener('change', atualizarCalculos);
    document.querySelectorAll('input[name="forma_pagamento"]').forEach(radio => {
        radio.addEventListener('change', atualizarCalculos);
    });

    // Listener para o envio do formulário
    formFinalizar.addEventListener('submit', (e) => {
        // Antes de enviar, coloca a sacola do localStorage no campo hidden do formulário
        sacolaInput.value = JSON.stringify(sacola);
        
        // Opcional: Limpar a sacola do localStorage após o envio bem-sucedido
        // localStorage.removeItem('sacola'); 
        // Você faria isso na página de 'pedido_sucesso.html'
    });

    // Inicia a renderização
    renderizarSacola();
});