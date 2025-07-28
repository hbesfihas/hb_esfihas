// Carrega a sacola do localStorage ao iniciar a página
let sacola = JSON.parse(localStorage.getItem('sacola') || '{}');

// Atualiza os contadores visíveis e a lista da sacola
function atualizarSacola() {
    let total = 0;
    let lista = document.getElementById('listaSacola');
    if (lista) lista.innerHTML = '';

    for (let card of document.querySelectorAll('.product-card')) {
        const id = card.getAttribute('data-id');
        const nome = card.getAttribute('data-nome');
        const preco = parseFloat(card.getAttribute('data-preco'));

        const qtd = sacola[id]?.quantidade || 0;

        // Se não tem item, mostrar só botão "Adicionar"
        const controls = `
            <div class="d-flex justify-content-center align-items-center mt-2" id="controls-${id}">
                ${qtd > 0
                    ? `
                    <button class="btn btn-outline-danger btn-sm me-2" onclick="updateCart('${id}', 'remove')">−</button>
                    <span id="quantidade-${id}" class="mx-2">${qtd}</span>
                    <button class="btn btn-outline-success btn-sm ms-2" onclick="updateCart('${id}', 'add')">+</button>
                    `
                    : `
                    <button class="btn btn-outline-primary btn-sm" onclick="updateCart('${id}', 'add')">Adicionar</button>
                    `
                }
            </div>
        `;

        card.querySelector(`#controls-${id}`)?.remove(); // remove controles antigos
        card.insertAdjacentHTML('beforeend', controls);

        // Adiciona item à lista da sacola
        if (qtd > 0 && lista) {
            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div>
                    <strong>${nome}</strong><br>
                    <small>${qtd} x R$ ${preco.toFixed(2)}</small>
                </div>
                <button class="btn btn-sm btn-danger ms-2" onclick="removerItem('${id}')">&times;</button>
            `;
            lista.appendChild(item);

            total += qtd * preco;
        }
    }

    // Atualiza total da sacola
    const totalEl = document.getElementById('totalSacola');
    if (totalEl) totalEl.innerText = total.toFixed(2);

    // Atualiza localStorage
    localStorage.setItem('sacola', JSON.stringify(sacola));
}

// Função chamada ao clicar em + ou -
function updateCart(produtoId, action) {
    if (!(produtoId in sacola)) {
        sacola[produtoId] = { quantidade: 0 };
    }

    if (action === 'add') {
        sacola[produtoId].quantidade += 1;
    } else if (action === 'remove') {
        sacola[produtoId].quantidade -= 1;
        if (sacola[produtoId].quantidade <= 0) {
            delete sacola[produtoId];
        }
    }

    atualizarSacola();
}

// Remoção total via botão "x" na lista da sacola
function removerItem(produtoId) {
    delete sacola[produtoId];
    atualizarSacola();
}

// Atualiza sacola assim que a página é carregada
document.addEventListener('DOMContentLoaded', atualizarSacola);
