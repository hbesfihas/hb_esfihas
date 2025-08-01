// Carrega a sacola do localStorage ao iniciar a página
let sacola = JSON.parse(localStorage.getItem('sacola') || '{}');

// Função chamada ao clicar em + ou -
function updateCart(produtoId, action) {
    // Busca o card do produto na página para pegar os dados
    const productCard = document.querySelector(`.product-card[data-id='${produtoId}']`);
    if (!productCard) {
        console.error('Card do produto não encontrado! Verifique o HTML.');
        return;
    }
    const nome = productCard.getAttribute('data-nome');
    const preco = productCard.getAttribute('data-preco');

    // Se o produto não está na sacola, inicializa ele com todas as informações
    if (!(produtoId in sacola)) {
        // PONTO CRÍTICO DA CORREÇÃO ESTÁ AQUI:
        sacola[produtoId] = { 
            quantidade: 0,
            nome: nome,
            preco: preco
        };
    }

    if (action === 'add') {
        sacola[produtoId].quantidade += 1;
    } else if (action === 'remove') {
        sacola[produtoId].quantidade -= 1;
    }
    
    // Se a quantidade for zero ou menos, remove o item da sacola
    if (sacola[produtoId]?.quantidade <= 0) {
        delete sacola[produtoId];
    }

    atualizarSacola();
}


// Atualiza a interface da página principal (home)
function atualizarSacola() {
    const sacolaResumo = document.getElementById('sacolaResumo');
    if (sacolaResumo) {
        let lista = document.getElementById('listaSacola');
        if (lista) lista.innerHTML = '';
        
        let total = 0;
        for(const id in sacola) {
            const item = sacola[id];
            if (item.quantidade > 0) {
                total += item.quantidade * parseFloat(item.preco);
            }
        }
        
        const totalEl = document.getElementById('totalSacola');
        if (totalEl) totalEl.innerText = total.toFixed(2);
    }
    
    for (let card of document.querySelectorAll('.product-card')) {
        const id = card.getAttribute('data-id');
        const qtd = sacola[id]?.quantidade || 0;
        const controlsContainer = card.querySelector(`#controls-${id}`);
        if(controlsContainer){
            const controls = `
                ${qtd > 0
                    ? `<button class="btn btn-outline-danger btn-sm me-2" onclick="updateCart('${id}', 'remove')">−</button>
                       <span class="mx-2">${qtd}</span>
                       <button class="btn btn-outline-success btn-sm ms-2" onclick="updateCart('${id}', 'add')">+</button>`
                    : `<button class="btn btn-outline-primary btn-sm" onclick="updateCart('${id}', 'add')">Adicionar</button>`
                }
            `;
            controlsContainer.innerHTML = controls;
        }
    }

    // Salva a sacola completa no localStorage
    localStorage.setItem('sacola', JSON.stringify(sacola));
}

// Atualiza a sacola assim que a página é carregada
document.addEventListener('DOMContentLoaded', atualizarSacola);