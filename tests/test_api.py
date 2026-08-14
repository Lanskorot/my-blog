"""
Тесты для API эндпоинтов.

Проверяет работу аутентификации, CRUD операций с постами,
права доступа, пагинацию и AJAX эндпоинты.
"""


import sys
import os
import pytest
import tempfile
import sqlite3
import json
from werkzeug.security import generate_password_hash


from application import create_app
from application.db import get_db, init_db
from config import DATABASE


@pytest.fixture
def app():
    """Создаёт тестовое приложение с временной БД"""
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'DATABASE': db_path,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })
    
    with app.app_context():
        init_db()
    
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Создаёт тестовый клиент для отправки запросов"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Создаёт CLI runner для команд"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Создаёт тестового пользователя"""
    with app.app_context():
        db = get_db()
        user = db.execute(
            'SELECT id FROM users WHERE email = ?', ('test_user@example.com',)
        ).fetchone()
        
        if not user:
            db.execute(
                'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                ('Test User', 'test_user@example.com', generate_password_hash('password123'), 'user')
            )
            db.commit()


@pytest.fixture
def test_admin(app):
    """Создаёт тестового администратора"""
    with app.app_context():
        db = get_db()
        user = db.execute(
            'SELECT id FROM users WHERE email = ?', ('admin@example.com',)
        ).fetchone()
        
        if not user:
            db.execute(
                'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                ('Admin User', 'admin@example.com', generate_password_hash('admin123'), 'admin')
            )
            db.commit()


@pytest.fixture
def auth_token(client, test_user):
    """Возвращает токен для аутентифицированных запросов"""
    response = client.post("/api/v1/login", json={
        'email': 'test_user@example.com',
        'password': 'password123'
    })
    data = response.get_json()
    return data['data']['token']


@pytest.fixture
def admin_token(client, test_admin):
    """Возвращает токен для администратора"""
    response = client.post("/api/v1/login", json={
        'email': 'admin@example.com',
        'password': 'admin123'
    })
    data = response.get_json()
    return data['data']['token']


@pytest.fixture
def sample_post(app, test_user):
    """Создаёт тестовый пост от имени test_user и возвращает его ID"""
    with app.app_context():
        db = get_db()
        # Получаем ID test_user
        user = db.execute(
            'SELECT id FROM users WHERE email = ?', ('test_user@example.com',)
        ).fetchone()
        user_id = user[0] if user else 1
        
        # Создаём пост
        cur = db.execute(
            'INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)',
            ('Test Post', 'Test Content', user_id)
        )
        db.commit()
        return cur.lastrowid


@pytest.fixture
def sample_category(app):
    """Создаёт тестовую категорию и возвращает её ID"""
    with app.app_context():
        db = get_db()
        # Проверяем, существует ли категория
        existing = db.execute(
            'SELECT id FROM categories WHERE name = ?', ('Test Category',)
        ).fetchone()
        
        if existing:
            return existing[0]
        
        cur = db.execute(
            'INSERT INTO categories (name, description) VALUES (?, ?)',
            ('Test Category', 'Test Description')
        )
        db.commit()
        return cur.lastrowid



@pytest.fixture
def another_user(app):
    """Создаёт другого тестового пользователя"""
    with app.app_context():
        db = get_db()
        user = db.execute(
            'SELECT id FROM users WHERE email = ?', ('another@example.com',)
        ).fetchone()
        
        if not user:
            db.execute(
                'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                ('Another User', 'another@example.com', generate_password_hash('password123'), 'user')
            )
            db.commit()


@pytest.fixture
def another_token(client, another_user):
    """Возвращает токен для другого пользователя"""
    response = client.post("/api/v1/login", json={
        'email': 'another@example.com',
        'password': 'password123'
    })
    data = response.get_json()
    return data['data']['token']

# ==================== ТЕСТЫ ====================

def test_get_posts(client):
    """Проверяет получение списка постов"""
    response = client.get("/api/v1/posts")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert 'data' in json_data
    assert 'pagination' in json_data


def test_get_posts_with_pagination(client):
    """Проверяет пагинацию постов"""
    response = client.get("/api/v1/posts?page=1&per_page=2")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert json_data['pagination']['page'] == 1
    assert json_data['pagination']['per_page'] == 2


def test_get_single_post_not_found(client):
    """Проверяет обработку несуществующего поста"""
    response = client.get("/api/v1/posts/999")
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data['success'] is False
    assert json_data['error'] == 'Пост не найден'


def test_get_single_post_success(client, sample_post):
    """Проверяет получение существующего поста"""
    response = client.get(f"/api/v1/posts/{sample_post}")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert 'data' in json_data
    assert json_data['data']['id'] == sample_post


def test_login_success(client, test_user):
    """Проверяет успешный вход и получение токена"""
    response = client.post("/api/v1/login", json={
        'email': 'test_user@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert 'token' in json_data['data']
    assert 'user' in json_data['data']


def test_login_wrong_password(client, test_user):
    """Проверяет вход с неверным паролем"""
    response = client.post("/api/v1/login", json={
        'email': 'test_user@example.com',
        'password': 'wrong_password'
    })
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data['success'] is False
    assert json_data['error'] == 'Неверный пароль'


def test_login_user_not_found(client):
    """Проверяет вход с несуществующим email"""
    response = client.post("/api/v1/login", json={
        'email': 'nonexistent@example.com',
        'password': 'password123'
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert json_data['error'] == 'Пользователь не найден'


def test_login_missing_fields(client):
    """Проверяет вход с отсутствующими полями"""
    response = client.post("/api/v1/login", json={
        'email': 'test@example.com'
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False


def test_logout_success(client, test_user):
    """Проверяет успешный выход"""
    # Сначала получаем токен
    login_response = client.post("/api/v1/login", json={
        'email': 'test_user@example.com',
        'password': 'password123'
    })
    token = login_response.get_json()['data']['token']
    
    # Выходим
    response = client.post("/api/v1/logout", 
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True


def test_logout_without_token(client):
    """Проверяет выход без токена"""
    response = client.post("/api/v1/logout")
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data['error'] == 'Требуется аутентификация'


def test_me_success(client, test_user, auth_token):
    """Проверяет получение информации о текущем пользователе"""
    response = client.get("/api/v1/me",
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert json_data['data']['email'] == 'test_user@example.com'


def test_me_without_token(client):
    """Проверяет получение информации без токена"""
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data['error'] == 'Требуется аутентификация'


def test_create_post_success(client, test_user, auth_token, sample_category):
    """Проверяет успешное создание поста"""
    response = client.post("/api/v1/posts",
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'title': 'New Test Post',
            'content': 'This is a test post content',
            'category_id': sample_category
        }
    )
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['success'] is True
    assert json_data['data']['title'] == 'New Test Post'


def test_create_post_without_title(client, auth_token):
    """Проверяет создание поста без заголовка"""
    response = client.post("/api/v1/posts",
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'content': 'This is a test post content'
        }
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'Заголовок' in json_data['error']


def test_create_post_without_auth(client):
    """Проверяет создание поста без аутентификации"""
    response = client.post("/api/v1/posts", json={
        'title': 'New Post',
        'content': 'Content'
    })
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data['error'] == 'Требуется аутентификация'


def test_create_post_invalid_category(client, auth_token):
    """Проверяет создание поста с несуществующей категорией"""
    response = client.post("/api/v1/posts",
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'title': 'New Post',
            'content': 'Content',
            'category_id': 999
        }
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert json_data['error'] == 'Категория не найдена'


def test_update_post_success(client, test_user, auth_token, sample_post):
    """Проверяет успешное обновление поста (автор обновляет свой пост)"""
    response = client.put(f"/api/v1/posts/{sample_post}",
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'title': 'Updated Title',
            'content': 'Updated Content'
        }
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert json_data['data']['title'] == 'Updated Title'



def test_update_post_forbidden(client, another_token, sample_post):
    """Проверяет обновление чужого поста (должно быть запрещено)"""
    response = client.put(f"/api/v1/posts/{sample_post}",
        headers={'Authorization': f'Bearer {another_token}'},
        json={
            'title': 'Updated Title',
            'content': 'Updated Content'
        }
    )
    assert response.status_code == 403
    json_data = response.get_json()
    assert json_data['success'] is False
    assert json_data['error'] == 'Недостаточно прав'

def test_update_post_not_found(client, auth_token):
    """Проверяет обновление несуществующего поста"""
    response = client.put("/api/v1/posts/999",
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'title': 'Updated Title',
            'content': 'Updated Content'
        }
    )
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data['success'] is False
    assert json_data['error'] == 'Пост не найден'


def test_update_post_without_auth(client, sample_post):
    """Проверяет обновление поста без аутентификации"""
    response = client.put(f"/api/v1/posts/{sample_post}", json={
        'title': 'Updated Title',
        'content': 'Updated Content'
    })
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data['error'] == 'Требуется аутентификация'


def test_delete_post_as_admin(client, test_admin, admin_token, sample_post):
    """Проверяет удаление поста администратором"""
    response = client.delete(f"/api/v1/posts/{sample_post}",
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert json_data['message'] == 'Пост успешно удалён'


def test_delete_post_as_user(client, test_user, auth_token, sample_post):
    """Проверяет удаление поста обычным пользователем (должно быть запрещено)"""
    response = client.delete(f"/api/v1/posts/{sample_post}",
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 403
    json_data = response.get_json()
    assert json_data['error'] == 'Недостаточно прав'


def test_delete_post_not_found(client, admin_token):
    """Проверяет удаление несуществующего поста"""
    response = client.delete("/api/v1/posts/999",
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data['success'] is False
    assert json_data['error'] == 'Пост не найден'


def test_api_docs(client):
    """Проверяет страницу документации API"""
    response = client.get("/api/docs")
    assert response.status_code == 200
    
    # Получаем текст ответа как обычную строку
    html = response.get_data(as_text=True)
    assert 'Документация API' in html
    assert '<title>Документация API</title>' in html


def test_ajax_posts(client):
    """Проверяет AJAX эндпоинт для постов"""
    response = client.get("/api/posts?page=1&per_page=5")
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'html' in json_data
    assert 'page' in json_data
    assert 'total_pages' in json_data


def test_ajax_category_posts(client, sample_category):
    """Проверяет AJAX эндпоинт для постов категории"""
    response = client.get(f"/api/category/{sample_category}/posts?page=1&per_page=5")
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'posts' in json_data
    assert 'page' in json_data
    assert 'total_pages' in json_data