// Seleção dos elementos do DOM
const commentForm = document.getElementById('comment-form');
const usernameInput = document.getElementById('username');
const commentTextInput = document.getElementById('comment-text');
const commentsSection = document.getElementById('comments-section');
const commentCount = document.getElementById('comment-count');

// Carregar comentários iniciais do LocalStorage (ou criar um array vazio se não houver nenhum)
let comments = JSON.parse(localStorage.getItem('forum_comments')) || [];

// Função para salvar os comentários no LocalStorage e atualizar a tela
function saveAndRender() {
    localStorage.setItem('forum_comments', JSON.stringify(comments));
    renderComments();
}

// Função para exibir os comentários na tela
function renderComments() {
    // Limpa a seção de comentários atual
    commentsSection.innerHTML = '';
    
    // Atualiza o contador de comentários
    commentCount.textContent = comments.length;

    if (comments.length === 0) {
        commentsSection.innerHTML = '<p style="color: #888;">Nenhum comentário ainda. Seja o primeiro a comentar!</p>';
        return;
    }

    // Passa por cada comentário (do mais recente ao mais antigo)
    comments.forEach((comment, index) => {
        const commentCard = document.createElement('div');
        commentCard.classList.add('comment-card');

        commentCard.innerHTML = `
            <div class="comment-header">
                <span class="comment-author">${escapeHTML(comment.author)}</span>
                <span class="comment-date">${comment.date}</span>
            </div>
            <div class="comment-body">${escapeHTML(comment.text)}</div>
            <button class="delete-btn" onclick="deleteComment(${index})">Excluir</button>
        `;

        commentsSection.appendChild(commentCard);
    });
}

// Função para adicionar um novo comentário
commentForm.addEventListener('submit', function(event) {
    event.preventDefault(); // Impede a página de recarregar ao enviar o formulário

    const author = usernameInput.value.trim();
    const text = commentTextInput.value.trim();
    
    // Formatação de data simples
    const date = new Date().toLocaleString('pt-BR', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    });

    // Cria o objeto do comentário
    const newComment = {
        author: author,
        text: text,
        date: date
    };

    // Adiciona o novo comentário no INÍCIO do array (para aparecer primeiro)
    comments.unshift(newComment);

    // Salva e renderiza
    saveAndRender();

    // Limpa apenas o campo de texto do comentário (mantém o nome do usuário para facilitar o próximo comentário)
    commentTextInput.value = '';
    commentTextInput.focus();
});

// Função para excluir um comentário
function deleteComment(index) {
    if (confirm("Tem certeza que deseja excluir este comentário?")) {
        comments.splice(index, 1); // Remove o item do array pelo índice
        saveAndRender();
    }
}

// Função de segurança para evitar Cross-Site Scripting (XSS) caso digitem código HTML nos inputs
function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

// Renderiza os comentários assim que a página abre
renderComments();