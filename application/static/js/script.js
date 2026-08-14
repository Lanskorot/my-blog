// ============================================
// КОНСТАНТЫ
// ============================================
const API_URL = '/api/posts';
const POSTS_CONTAINER_ID = 'posts-container';
const PAGINATION_ID = 'pagination';

// ============================================
// ЗАГРУЗКА ПОСТОВ
// ============================================
function loadPosts(page = 1) {
    const container = document.getElementById(POSTS_CONTAINER_ID);
    if (!container) {
        console.error('Контейнер для постов не найден');
        return;
    }
    
    // Показываем индикатор загрузки
    container.innerHTML = `
        <div class="loading-indicator">
            <div class="spinner"></div>
            <p>Загрузка...</p>
        </div>
    `;
    
    // Отправляем AJAX-запрос
    fetch(`${API_URL}?page=${page}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.html) {
                container.innerHTML = data.html;
                updatePagination(data.page, data.total_pages);
                
                // Обновляем URL в браузере без перезагрузки
                const newUrl = window.location.pathname + `?page=${page}`;
                window.history.pushState({ page: page }, '', newUrl);
            } else {
                throw new Error('Нет данных от сервера');
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки постов:', error);
            container.innerHTML = `
                <div class="empty-state">
                    <p>❌ Ошибка загрузки постов</p>
                    <button onclick="loadPosts(${page})" class="btn-primary" style="margin-top: 10px; padding: 8px 20px; border-radius: 8px; border: none; background: #2563eb; color: white; cursor: pointer;">
                        🔄 Попробовать снова
                    </button>
                </div>
            `;
        });
}

// ============================================
// ПАГИНАЦИЯ
// ============================================
function updatePagination(currentPage, totalPages) {
    const pagination = document.getElementById(PAGINATION_ID);
    if (!pagination) return;
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '<div class="pagination">';
    
    // Кнопка "Предыдущая"
    if (currentPage > 1) {
        html += `<a href="#" onclick="loadPosts(${currentPage - 1}); return false;" class="page-link">← Предыдущая</a>`;
    }
    
    // Текущая страница
    html += `<span class="page-current">Страница ${currentPage} из ${totalPages}</span>`;
    
    // Кнопка "Следующая"
    if (currentPage < totalPages) {
        html += `<a href="#" onclick="loadPosts(${currentPage + 1}); return false;" class="page-link">Следующая →</a>`;
    }
    
    html += '</div>';
    pagination.innerHTML = html;
}

// ============================================
// ОБРАБОТЧИК КНОПОК "НАЗАД"/"ВПЕРЁД"
// ============================================
window.addEventListener('popstate', function(event) {
    if (event.state && event.state.page) {
        loadPosts(event.state.page);
    }
});

// ============================================
// ЗАГРУЗКА ПРИ СТАРТЕ
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const page = parseInt(urlParams.get('page')) || 1;
    
    // Если есть параметр page > 1, загружаем через AJAX
    if (page > 1) {
        loadPosts(page);
    }
});