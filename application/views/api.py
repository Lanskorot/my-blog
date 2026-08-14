"""
API маршруты для внешних клиентов.

Содержит REST API эндпоинты для работы с постами,
аутентификацией и получением данных.
"""

import logging
import time
import traceback
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from application.db import get_db
from application.models.auth_tokens import LongTokenRepository
from application.models.categories import CategoriesRepository
from application.models.notification import NotificationRepository
from application.models.posts import PostRepository
from application.models.user import UserRepository
from application.services.limiter import limiter
from application.services.redis_service import get_cached_posts

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)


def api_auth_required(func):
    """
    Декоратор для проверки аутентификации в API.
    
    Проверяет наличие валидного Bearer токена в заголовке Authorization.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = get_db()
        repo = LongTokenRepository(db)
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return jsonify({'error': 'Требуется аутентификация'}), 401
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Неверный формат токена'}), 401
        
        token = auth_header[7:]
        user_id = repo.validate_auth_token(token)
        
        if not user_id:
            return jsonify({'error': 'Недействительный токен'}), 401
        
        g.current_user_id = user_id
        return func(*args, **kwargs)
    return wrapper


def api_admin_required(func):
    """
    Декоратор для проверки прав администратора в API.
    
    Проверяет, что текущий пользователь имеет роль администратора.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = get_db()
        repo = UserRepository(db)
        
        if not hasattr(g, 'current_user_id'):
            return jsonify({'error': 'Требуется аутентификация'}), 401
        
        if not repo.is_admin(g.current_user_id):
            return jsonify({'error': 'Недостаточно прав'}), 403
        
        return func(*args, **kwargs)
    return wrapper


@api_bp.route('/v1/posts')
@limiter.limit('2 per minute')
def api_v1_posts():
    """
    Получение списка постов с пагинацией.
    
    GET /api/v1/posts?page=1&per_page=5
    """
    try:
        db = get_db()
        repo = PostRepository(db)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        posts = get_cached_posts(page, per_page)
        
        posts_list = []
        for post in posts:
            posts_list.append({
                'id': post[0],
                'title': post[1],
                'content': post[2],
                'author_id': post[3],
                'created_at': post[4],
                'author': post[5],
                'category': post[6] if post[6] else 'Без категории'
            })
        
        total = repo.count_posts()
        
        return jsonify({
            'success': True,
            'data': posts_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в API v1/posts: {e}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500


@api_bp.route('/v1/posts/<int:post_id>', methods=['GET'])
def api_v1_get_post(post_id):
    """Получение конкретного поста по ID."""
    try:
        db = get_db()
        repo = PostRepository(db)
        post = repo.get_by_id(post_id)
        
        if not post:
            return jsonify({'success': False, 'error': 'Пост не найден'}), 404
        
        post_data = {
            'id': post[0],
            'title': post[1],
            'content': post[2],
            'author_id': post[3],
            'author_name': post[5],
            'category_name': post[6] if post[6] else 'без категории',
            'created_at': post[4],
        }
        
        return jsonify({
            'success': True,
            'data': post_data,
        })
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в API v1/posts: {e}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500


@api_bp.route('/v1/login', methods=['POST'])
@limiter.limit('5 per minute')
def api_v1_login():
    """Вход в систему и получение токена доступа."""
    try:
        db = get_db()
        repo = UserRepository(db)
        note_repo = NotificationRepository(db)
        token_repo = LongTokenRepository(db)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Нет данных'}), 400
        
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'email и пароль обязательны'}), 400
        
        user = repo.get_by_email(email)
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 400
        
        if not check_password_hash(user[3], password):
            return jsonify({'success': False, 'error': 'Неверный пароль'}), 401
        
        token = token_repo.create_auth_token(user[0], remember=True)
        note_repo.log_notification(user[0], 'api_login', f'Пользователь {user[1]} вошел через API')
        
        role = user[4] if len(user) > 4 and user[4] else 'user'
        
        return jsonify({
            'success': True,
            'message': 'Вход выполнен успешно',
            'data': {
                'user': {
                    'id': user[0],
                    'name': user[1],
                    'email': user[2],
                    'role': role
                },
                'token': token,
                'expires_in': time.time() + 30 * 24 * 60 * 60
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в API /v1/login: {e}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500


@api_bp.route('/v1/logout', methods=['POST'])
@api_auth_required
def api_v1_logout():
    """Выход из системы (удаление токена)."""
    try:
        db = get_db()
        token_repo = LongTokenRepository(db)
        note_repo = NotificationRepository(db)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Токен не предоставлен'}), 400
        
        token = auth_header[7:]
        token_repo.delete_auth_token(token)
        
        note_repo.log_notification(
            g.current_user_id,
            'api_logout',
            'Пользователь вышел через API'
        )
        
        return jsonify({
            'success': True,
            'message': 'Выход выполнен успешно'
        })
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в API /v1/logout: {e}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500


@api_bp.route('/v1/me', methods=['GET'])
@api_auth_required
def api_v1_me():
    """Получение информации о текущем пользователе."""
    try:
        db = get_db()
        repo = UserRepository(db)
        
        user = repo.get_by_id(g.current_user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        role = user[4] if len(user) > 4 and user[4] else 'user'
        
        return jsonify({
            'success': True,
            'data': {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'role': role,
                'last_login': user[4] if len(user) > 4 else None
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в API /v1/me: {e}')
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500


@api_bp.route('/v1/posts', methods=['POST'])
@api_auth_required
def api_v1_create_post():
    """Создание нового поста."""
    try:
        db = get_db()
        post_repo = PostRepository(db)
        category_repo = CategoriesRepository(db)
        note_repo = NotificationRepository(db)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Нет данных'}), 400
        
        title = data.get('title')
        content = data.get('content')
        category_id = data.get('category_id')
        
        if not title or not content:
            return jsonify({'success': False, 'error': 'Заголовок и содержимое обязательны'}), 400
        
        if category_id:
            category = category_repo.get_all_data_categories_by_id(category_id)
            if not category:
                return jsonify({'success': False, 'error': 'Категория не найдена'}), 400
        
        post_id = post_repo.add(title, content, g.current_user_id)
        
        if category_id:
            db.execute(
                'INSERT INTO post_categories (post_id, category_id) VALUES (?, ?)',
                (post_id, category_id)
            )
            db.commit()
        
        note_repo.log_notification(
            g.current_user_id,
            'api_new_post',
            f'Создан пост через API: "{title}"'
        )
        
        current_app.logger.info(
            f'Создан новый пост через API: {post_id} пользователем {g.current_user_id}'
        )
        
        return jsonify({
            'success': True,
            'data': {
                'id': post_id,
                'title': title,
                'content': content,
                'category_id': category_id,
                'author_id': g.current_user_id
            },
            'message': 'Пост успешно создан'
        }), 201
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в API v1/posts (POST): {e}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500


@api_bp.route('/v1/posts/<int:post_id>', methods=['PUT'])
@api_auth_required
def api_v1_update_post(post_id):
    """Обновление поста (автор или администратор)."""
    try:
        db = get_db()
        post_repo = PostRepository(db)
        category_repo = CategoriesRepository(db)
        note_repo = NotificationRepository(db)
        user_repo = UserRepository(db)
        
        post = post_repo.get_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': 'Пост не найден'}), 404
        
        is_author = post[3] == g.current_user_id
        is_admin_user = user_repo.is_admin(g.current_user_id)
        
        if not (is_author or is_admin_user):
            return jsonify({'success': False, 'error': 'Недостаточно прав'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Нет данных'}), 400
        
        title = data.get('title', post[1])
        content = data.get('content', post[2])
        category_id = data.get('category_id')
        
        if category_id:
            category = category_repo.get_all_data_categories_by_id(category_id)
            if not category:
                return jsonify({'success': False, 'error': 'Категория не найдена'}), 400
        
        post_repo.add_edit_post(post_id, title, content, g.current_user_id)
        
        if category_id:
            db.execute('DELETE FROM post_categories WHERE post_id = ?', (post_id,))
            db.execute(
                'INSERT INTO post_categories (post_id, category_id) VALUES (?, ?)',
                (post_id, category_id)
            )
            db.commit()
        
        note_repo.log_notification(
            g.current_user_id,
            'api_update_post',
            f'Обновлён пост через API: "{title}" (ID: {post_id})'
        )
        
        current_app.logger.info(
            f'Обновлён пост через API: {post_id} пользователем {g.current_user_id}'
        )
        
        return jsonify({
            'success': True,
            'data': {
                'id': post_id,
                'title': title,
                'content': content,
                'category_id': category_id
            },
            'message': 'Пост успешно обновлён'
        })
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в API v1/posts/{post_id} (PUT): {e}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500


@api_bp.route('/v1/posts/<int:post_id>', methods=['DELETE'])
@api_auth_required
@api_admin_required
def api_v1_delete_post(post_id):
    """Удаление поста (только для администраторов)."""
    try:
        db = get_db()
        post_repo = PostRepository(db)
        note_repo = NotificationRepository(db)
        
        post = post_repo.get_by_id(post_id)
        if not post:
            return jsonify({'success': False, 'error': 'Пост не найден'}), 404
        
        post_repo.delete_by_id(post_id)
        
        note_repo.log_notification(
            g.current_user_id,
            'api_delete_post',
            f'Удалён пост через API (ID: {post_id})'
        )
        
        current_app.logger.info(
            f'Удалён пост через API: {post_id} администратором {g.current_user_id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Пост успешно удалён'
        })
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в API v1/posts/{post_id} (DELETE): {e}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500


@api_bp.route('/docs')
def api_docs():
    """Страница с документацией API."""
    user_name = session.get('name') if 'user_id' in session else None
    return render_template('api_docs.html', user_name=user_name)


@api_bp.route('/posts')
def api_posts():
    """AJAX эндпоинт для получения постов с пагинацией (возвращает HTML)."""
    try:
        db = get_db()
        repo = PostRepository(db)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        
        logger.info(f'AJAX запрос постов: страница {page}, постов на странице {per_page}')
        
        posts = get_cached_posts(page, per_page)
        total = repo.count_posts()
        total_pages = (total + per_page - 1) // per_page
        
        logger.info(f'AJAX ответ: {len(posts)} постов, всего {total}, страниц {total_pages}')
        
        html = render_template('_posts_list.html', posts=posts)
        
        return jsonify({
            'html': html,
            'page': page,
            'total_pages': total_pages,
            'total': total
        })
    
    except Exception as e:
        logger.error(f'Ошибка в AJAX /posts: {str(e)}')
        return jsonify({
            'error': 'Внутренняя ошибка сервера',
            'message': str(e) if current_app.debug else None
        }), 500


@api_bp.route('/category/<int:category_id>/posts')
def api_category_posts(category_id):
    """AJAX эндпоинт для получения постов категории с пагинацией (infinite scroll)."""
    try:
        db = get_db()
        post_repo = PostRepository(db)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        
        logger.info(
            f'AJAX запрос постов категории {category_id}: '
            f'страница {page}, постов на странице {per_page}'
        )
        
        posts = post_repo.get_posts_by_category_paginated(category_id, page, per_page)
        total = post_repo.count_posts_by_category(category_id)
        total_pages = (total + per_page - 1) // per_page
        
        logger.info(
            f'AJAX ответ для категории {category_id}: '
            f'{len(posts)} постов, всего {total}, страниц {total_pages}'
        )
        
        posts_html = []
        for post in posts:
            posts_html.append({
                'id': post[0],
                'title': post[1],
                'content': post[2][:200] + '...' if len(post[2]) > 200 else post[2],
                'author': post[5],
                'created_at': post[4],
                'html': render_template('_post_item.html', post=post)
            })
        
        return jsonify({
            'posts': posts_html,
            'page': page,
            'total_pages': total_pages,
            'has_next': page < total_pages
        })
    
    except Exception as e:
        logger.error(f'Ошибка в AJAX /category/{category_id}/posts: {str(e)}')
        return jsonify({
            'error': 'Внутренняя ошибка сервера',
            'message': str(e) if current_app.debug else None
        }), 500