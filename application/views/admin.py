"""
Административные маршруты.

Содержит обработчики для управления пользователями, постами,
логами и просмотра статистики.
"""

import os
import time
import traceback
from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from .errors import forbidden_error, internal_server_error, page_not_found
from application.db import get_db
from application.models.auth_tokens import LongTokenRepository
from application.models.categories import CategoriesRepository
from application.models.notification import NotificationRepository
from application.models.posts import PostRepository
from application.models.user import UserRepository
from application.services.redis_service import get_active_user_ids, get_active_users_count

admin_bp = Blueprint('admin', __name__,
                     template_folder='templates',
                     static_folder='../static')


def admin_required(func):
    """Декоратор для проверки прав администратора."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = get_db()
        user_repo = UserRepository(db)
        
        if not session.get('user_id'):
            current_app.logger.warning('Попытка доступа к админ-панели без авторизации')
            return redirect(url_for('auth.login'))
        
        if not user_repo.is_admin(session.get('user_id')):
            current_app.logger.warning(
                f'Попытка несанкционированного доступа к админ-панели '
                f'пользователем {session.get("user_id")}'
            )
            return forbidden_error()
        
        return func(*args, **kwargs)
    return wrapper


@admin_bp.route('/')
@admin_required
def admin_dashboard():
    """Главная страница админ панели."""
    db = get_db()
    note_repo = NotificationRepository(db)
    
    try:
        stats = get_extended_stats()
        recent_actions = note_repo.last_5_notification()
        
        current_app.logger.info(f'Админ панель открыта пользователем {session.get("user_id")}')
        
        return render_template(
            'admin/admin_dashboard.html',
            stats=stats,
            recent_actions=recent_actions,
            user_name=session.get('name')
        )
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в админ панели {e}')
        current_app.logger.error(traceback.format_exc())
        return internal_server_error(e)


@admin_bp.route('/users/')
@admin_required
def admin_users():
    """Страница управления пользователями."""
    try:
        db = get_db()
        user_repo = UserRepository(db)
        
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        users = user_repo.get_paginated_users(per_page, offset)
        total_users = user_repo.count_users()
        total_pages = (total_users + per_page - 1) // per_page
        
        return render_template(
            'admin/admin_users.html',
            users=users,
            current_page=page,
            total_pages=total_pages,
            user_name=session.get('name')
        )
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в управлении пользователями {e}')
        current_app.logger.error(traceback.format_exc())
        return internal_server_error(e)


@admin_bp.route('/posts/')
@admin_required
def admin_posts():
    """Страница управления постами."""
    try:
        db = get_db()
        repo = PostRepository(db)
        
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        posts = repo.get_all_with_categories(page, per_page)
        total_posts = repo.count_posts()
        total_pages = (total_posts + per_page - 1) // per_page
        
        return render_template(
            'admin/admin_posts.html',
            posts=posts,
            current_page=page,
            total_pages=total_pages,
            user_name=session.get('name')
        )
    
    except Exception as e:
        current_app.logger.error(f'Ошибка в управлении постами {e}')
        current_app.logger.error(traceback.format_exc())
        return internal_server_error(e)


@admin_bp.route('/posts/delete/<int:post_id>', methods=['POST'])
@admin_required
def admin_delete_posts(post_id):
    """Удаление поста администратором."""
    try:
        db = get_db()
        repo = PostRepository(db)
        note_repo = NotificationRepository(db)
        
        post = repo.get_by_id(post_id)
        if not post:
            current_app.logger.warning(f'Попытка удаления несуществующего поста {post_id}')
            flash('Пост не найден', 'error')
            return redirect(url_for('admin.admin_posts'))
        
        repo.delete_by_id(post_id)
        note_repo.log_notification(
            session['user_id'],
            'admin_post_delete',
            f'Администратор удалил пост "{post[1]}" (ID: {post_id})'
        )
        current_app.logger.info(f'Администратор {session["user_id"]} удалил пост "{post_id}"')
        flash('Пост успешно удалён', 'success')
        return redirect(url_for('admin.admin_posts'))
    
    except Exception as e:
        current_app.logger.error(f'Ошибка при удалении поста {e}')
        current_app.logger.error(traceback.format_exc())
        return internal_server_error(e)


@admin_bp.route('/posts/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_posts(post_id):
    """Редактирование поста администратором."""
    try:
        db = get_db()
        repo = PostRepository(db)
        note_repo = NotificationRepository(db)
        
        post = repo.get_by_id(post_id)
        if not post:
            current_app.logger.warning(f'Попытка редактирования несуществующего поста {post_id}')
            flash('Пост не найден', 'error')
            return redirect(url_for('admin.admin_posts'))
        
        if request.method == 'POST':
            title = request.form.get('title', post[1])
            content = request.form.get('content', post[2])
            repo.add_edit_post(post_id, title, content, session.get('name'))
            
            note_repo.log_notification(
                session['user_id'],
                'admin_post_edit',
                f'Администратор отредактировал пост "{title}" (ID: {post_id})'
            )
            current_app.logger.info(f'Администратор {session["user_id"]} отредактировал пост "{post_id}"')
            flash('Пост успешно отредактирован', 'success')
            return redirect(url_for('admin.admin_posts'))
        
        edit_count = repo.get_edit_count(post_id)
        return render_template(
            'admin/admin_edit_post.html',
            post=post,
            edit_count=edit_count,
            user_name=session.get('name')
        )
    
    except Exception as e:
        current_app.logger.error(f'Ошибка при редактировании поста {post_id}: {e}')
        current_app.logger.error(traceback.format_exc())
        return internal_server_error(e)


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Удаление пользователя администратором."""
    try:
        db = get_db()
        user_repo = UserRepository(db)
        note_repo = NotificationRepository(db)
        
        if user_id == session['user_id']:
            current_app.logger.warning(f'Попытка самоудаления администратором {user_id}')
            flash('Нельзя удалить самого себя', 'warning')
            return redirect(url_for('admin.admin_users'))
        
        user = user_repo.get_by_id(user_id)
        if not user:
            current_app.logger.warning(f'Попытка удаления несуществующего пользователя {user_id}')
            flash('Пользователь не найден', 'error')
            return redirect(url_for('admin.admin_users'))
        
        user_repo.delete_user_by_id(user_id)
        note_repo.log_notification(
            session['user_id'],
            'admin_user_delete',
            f'Администратор удалил пользователя "{user[1]}" ({user[2]}: ID: {user_id})'
        )
        current_app.logger.info(f'Администратор {session["user_id"]} удалил пользователя "{user_id}"')
        flash(f'Пользователь {user[1]} успешно удалён', 'success')
        return redirect(url_for('admin.admin_users'))
    
    except Exception as e:
        current_app.logger.error(f'Ошибка при удалении пользователя {user_id}: {e}')
        current_app.logger.error(traceback.format_exc())
        return internal_server_error(e)


@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    """Редактирование пользователя администратором."""
    try:
        db = get_db()
        user_repo = UserRepository(db)
        note_repo = NotificationRepository(db)
        
        user = user_repo.get_by_id(user_id)
        if not user:
            current_app.logger.warning(f'Попытка редактирования несуществующего пользователя {user_id}')
            flash('Пользователь не найден', 'error')
            return redirect(url_for('admin.admin_users'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            role = request.form.get('role')
            
            if email != user[2]:
                existing_user = user_repo.get_user_by_email(email)
                if existing_user and existing_user[0] != user_id:
                    return render_template(
                        'admin/admin_edit_user.html',
                        user=user,
                        error='Пользователь с таким email уже существует',
                        user_name=session.get('name')
                    )
            
            user_repo.update_user(user_id, name, email, role)
            note_repo.log_notification(
                session['user_id'],
                'admin_user_edit',
                f'Администратор отредактировал пользователя "{name}" (ID: {user_id})'
            )
            current_app.logger.info(f'Администратор {session["user_id"]} отредактировал пользователя "{user_id}"')
            flash(f'Пользователь {name} успешно обновлён', 'success')
            return redirect(url_for('admin.admin_users'))
        
        return render_template(
            'admin/admin_edit_user.html',
            user=user,
            user_name=session.get('name')
        )
    
    except Exception as e:
        current_app.logger.error(f'Ошибка при редактировании пользователя {user_id}: {e}')
        current_app.logger.error(traceback.format_exc())
        return internal_server_error(e)


@admin_bp.route('/users/change_role/<int:user_id>', methods=['POST'])
@admin_required
def change_role(user_id):
    """Изменение роли пользователя."""
    try:
        db = get_db()
        user_repo = UserRepository(db)
        notification_repo = NotificationRepository(db)
        
        if user_id == session['user_id']:
            flash('Нельзя изменить свою роль', 'warning')
            return redirect(url_for('admin.admin_users'))
        
        current_role = user_repo.get_current_user_role(user_id)
        new_role = 'user' if current_role == 'admin' else 'admin'
        user = user_repo.get_by_id(user_id)
        
        db.execute(
            'UPDATE users SET role = ? WHERE id = ?',
            (new_role, user_id)
        )
        db.commit()
        
        notification_repo.log_notification(
            session.get('user_id'),
            'Изменение роли',
            f'Пользователь {user[1]} стал {new_role}'
        )
        
        current_app.logger.info(
            f'Пользователь ID: {session["user_id"]} изменил роль пользователя {user[1]} на {new_role}'
        )
        flash(f'Роль пользователя {user[1]} изменена на {new_role}', 'success')
    
    except Exception as e:
        current_app.logger.error(f'Ошибка при изменении роли: {str(e)}')
        flash('Произошла ошибка при изменении роли', 'error')
    
    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/logs')
@admin_required
def admin_logs():
    """Страница просмотра логов."""
    try:
        log_file_path = 'logs/blog.log'
        logs = []
        
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logs = lines[-100:] if len(lines) > 100 else lines
                logs.reverse()
        else:
            current_app.logger.warning('Файл логов не найден')
            flash('Файл логов не найден', 'warning')
        
        return render_template(
            'admin/admin_logs.html',
            logs=logs,
            total_lines=len(logs),
            user_name=session.get('name')
        )
    
    except Exception as e:
        current_app.logger.error(f'Ошибка при загрузке логов: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        flash('Произошла ошибка при загрузке логов', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/logs/clear', methods=['POST'])
@admin_required
def clear_logs():
    """Очистка файла логов."""
    try:
        log_file_path = 'logs/blog.log'
        if os.path.exists(log_file_path):
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write(f'# Логи очищены администратором {session.get("name")} в {datetime.now()}\n')
            current_app.logger.info(f'Логи очищены администратором {session.get("user_id")}')
            return jsonify({'success': True, 'message': 'Логи очищены'})
        else:
            return jsonify({'success': False, 'error': 'Файл логов не найден'}), 404
    
    except Exception as e:
        current_app.logger.error(f'Ошибка при очистке логов: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/notifications')
@admin_required
def get_all_notifications():
    """Страница просмотра всех уведомлений."""
    repo = NotificationRepository(get_db())
    notifications = repo.get_full_info() or []
    return render_template('notifications.html', notifications=notifications)


@admin_bp.route('/stats')
@admin_required
def stats():
    """Страница статистики активных пользователей."""
    active_count = get_active_users_count()
    active_ids = get_active_user_ids()
    
    db = get_db()
    user_repo = UserRepository(db)
    token_users = LongTokenRepository(db)
    
    active_token_users = token_users.get()
    active_users = []
    
    for uid in active_ids:
        user = user_repo.get_by_id(uid)
        if user:
            active_users.append(user[1])
    
    formatted_tokens = []
    for token in active_token_users:
        formatted_token = {
            'id': token[0],
            'user_id': token[1],
            'token': token[2],
            'expires_at_raw': token[3],
            'expires_at_str': datetime.fromtimestamp(token[3]).strftime('%d.%m.%Y %H:%M'),
            'name': token[4]
        }
        formatted_tokens.append(formatted_token)
    
    return render_template(
        'stats.html',
        active_count=active_count,
        active_users=active_users,
        active_token_users=formatted_tokens,
        now=time.time()
    )


def get_extended_stats() -> dict:
    """Возвращает расширенную статистику."""
    db = get_db()
    user_repo = UserRepository(db)
    posts_repo = PostRepository(db)
    note_repo = NotificationRepository(db)
    category_repo = CategoriesRepository(db)
    
    stats = {
        'user_count': user_repo.count_users(),
        'post_count': posts_repo.count_posts(),
        'category_count': category_repo.count_categories(),
        'logging_count': note_repo.count_notification(),
        'posts_by_day': posts_repo.get_posts_by_day(),
        'active_users': user_repo.get_active_users(),
        'posts_by_category': category_repo.get_posts_by_category()
    }
    
    return stats