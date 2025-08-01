// Função para pegar o token CSRF do cookie
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


// Função chamada ao clicar em + ou -
async function updateCart(produtoId, action) {
    // 1. Atualização visual imediata (lógica local)
    if (!(produtoId in sacola)) {
        sacola[produtoId] = { quantidade: 0 };
    }
    const nome = document.querySelector(`.product-card[data-id='${produtoId}']`).getAttribute('data-nome');
    const preco = document.querySelector(`.product-card[data-id='${produtoId}']`).getAttribute('data-preco');

    if (action === 'add') {
        sacola[produtoId].quantidade += 1;
        sacola[produtoId].nome = nome; // Garante que temos nome/preço na sacola
        sacola[produtoId].preco = preco;
    } else if (action === 'remove') {
        sacola[produtoId].quantidade -= 1;
    }
    
    if (sacola[produtoId].quantidade <= 0) {
        delete sacola[produtoId];
    }
    
    atualizarVisualSacola(); // Atualiza a tela localmente na hora

    // 2. Enviar a atualização para o backend (Django)
    try {
        const response = await fetch(`/add_carrinho/${produtoId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken, // Token de segurança
            },
            body: JSON.stringify({ action: action })
        });

        if (!response.ok) {
            console.error('Falha ao atualizar a sacola no servidor.');
            // Aqui você poderia reverter a mudança visual ou mostrar um erro
        }
        
        // Opcional: pode usar a resposta do servidor se ele retornar algo útil
        const data = await response.json();
        console.log('Sacola do servidor atualizada:', data);

    } catch (error) {
        console.error('Erro de rede:', error);
    }
}

// Renomeie 'atualizarSacola' para 'atualizarVisualSacola' para evitar confusão
function atualizarVisualSacola() {
    // A lógica desta função continua a mesma, mas sem salvar no localStorage.
    // Ela apenas lê o objeto 'sacola' e atualiza a tela.
    // ... (todo o seu código de manipulação do DOM)
}

// ...
document.addEventListener('DOMContentLoaded', atualizarVisualSacola);