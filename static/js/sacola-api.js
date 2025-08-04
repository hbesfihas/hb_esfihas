// Este arquivo é nossa "biblioteca" para gerenciar os dados da sacola.
// Ele não toca no HTML, apenas nos dados.

// Carrega a sacola do localStorage de forma segura
export function getSacola() {
    try {
        const sacolaStorage = localStorage.getItem('sacola');
        if (sacolaStorage) {
            const sacola = JSON.parse(sacolaStorage);
            return (typeof sacola === 'object' && sacola !== null) ? sacola : {};
        }
    } catch (e) {
        console.error("Erro ao ler a sacola do localStorage. Limpando dados corrompidos.", e);
        localStorage.removeItem('sacola');
    }
    return {};
}

// Salva a sacola no localStorage
function saveSacola(sacola) {
    localStorage.setItem('sacola', JSON.stringify(sacola));
}

// Adiciona ou remove itens da sacola
export function updateItem(produtoId, action, produtoInfo) {
    let sacola = getSacola();

    if (!(produtoId in sacola) && action === 'add') {
        sacola[produtoId] = { 
            quantidade: 0, 
            nome: produtoInfo.nome, 
            preco: produtoInfo.preco 
        };
    }

    if (sacola[produtoId]) {
        if (action === 'add') {
            sacola[produtoId].quantidade += 1;
        } else if (action === 'remove') {
            sacola[produtoId].quantidade -= 1;
        }

        if (sacola[produtoId].quantidade <= 0) {
            delete sacola[produtoId];
        }
    }
    
    saveSacola(sacola);
    return sacola; // Retorna a sacola atualizada
}

// Limpa a sacola inteira
export function limparSacola() {
    localStorage.removeItem('sacola');
}

// Função para pegar o token CSRF dos cookies do navegador
export function getCookie(name) {
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