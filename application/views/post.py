"""
Модуль с маршрутами для работы с постами.

Содержит обработчики для создания, просмотра, редактирования,
удаления постов, а также поиска и фильтрации по категориям.
"""

import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for, current_app
from marshmallow import ValidationError

from application.db import get_db
from application.models.categories import CategoriesRepository
from application.models.notification import NotificationRepository
from application.models.posts import PostRepository
from application.models.user import UserRepository
from application.schemas.post import PostRegistrationSchema
from application.services.mail_service import send_new_post_email

logger = logging.getLogger(__name__)
post_bp = Blueprint('post', __name__)


@post_bp.route('/add_post/', methods=['GET', 'POST'])
def add_post():
    """
    Добавить новый пост.
    
    GET: Показывает форму создания поста.
    POST: Обрабатывает отправку формы и создаёт пост.
    """
    if 'user_id' not in session:
        logger.warning(f'Попытка создания поста без авторизации. IP: {request.remote_addr}')
        flash('Необходимо авторизоваться для создания поста', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        db = get_db()
        cat_repo = CategoriesRepository(db)
        
        if request.method == 'POST':
            categories_raw = request.form.getlist('categories')
            logger.info(f'Попытка создания поста. Категории: {categories_raw}')
            
            form_data = dict(request.form)
            form_data['categories'] = categories_raw
            
            schema = PostRegistrationSchema()
            try:
                validated_data = schema.load(form_data)
                logger.debug(f'Данные поста прошли валидацию: {validated_data}')
            except ValidationError as err:
                logger.warning(f'Ошибка валидации при создании поста: {err.messages}')
                return render_template('new_post.html',
                                     errors=err.messages,
                                     form_data=request.form,
                                     categories=cat_repo.get_all_categories())
            
            title = validated_data['title']
            content = validated_data['content']
            category_ids = validated_data['categories']
            user_id = session['user_id']
            
            repo = PostRepository(db)
            post_id = repo.add(title, content, user_id)
            logger.info(f'Создан пост ID: {post_id}, заголовок: "{title}", автор ID: {user_id}')
            
            for cat_id in category_ids:
                db.execute(
                    'INSERT INTO post_categories (post_id, category_id) VALUES (?, ?)',
                    (post_id, cat_id)
                )
            db.commit()
            
            notification_repo = NotificationRepository(db)
            category_names = []
            for cat_id in category_ids:
                name = cat_repo.get_categories_by_id(cat_id)
                if name != 'Неизвестно':
                    category_names.append(name)
            categories_str = ', '.join(category_names)
            notification_repo.log_notification(
                user_id,
                'Новый пост',
                f'Создан пост "{title}" в категориях: {categories_str}'
            )
            
            try:
                send_new_post_email(session.get('email'))
                logger.info(f'Email о новом посте отправлен на {session.get("email")}')
            except Exception as e:
                logger.error(f'Ошибка отправки email о новом посте: {str(e)}')
            
            flash('Пост успешно создан!', 'success')
            logger.info(f'Пост "{title}" успешно создан пользователем ID: {user_id}')
            return redirect(url_for("main.index"))
        
        categories = cat_repo.get_all_categories()
        return render_template('new_post.html', categories=categories)
    
    except Exception as e:
        logger.error(f'Ошибка при создании поста: {str(e)}')
        flash('Произошла ошибка при создании поста. Попробуйте позже.', 'error')
        return redirect(url_for('main.index'))


@post_bp.route('/post/<int:post_id>')
def show_post(post_id):
    """Отображает пост по его ID."""
    try:
        repo = PostRepository(get_db())
        post = repo.get_by_id(post_id)
        
        if post is None:
            logger.warning(f'Запрос несуществующего поста ID: {post_id}')
            flash('Пост не найден', 'error')
            return redirect(url_for('main.index'))
        
        logger.info(f'Просмотр поста ID: {post_id}, заголовок: "{post[1]}"')
        return render_template('post.html', post=post)
    
    except Exception as e:
        logger.error(f'Ошибка при просмотре поста ID {post_id}: {str(e)}')
        flash('Произошла ошибка при загрузке поста', 'error')
        return redirect(url_for('main.index'))


@post_bp.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    """Удаляет пост по ID (только для автора)."""
    if 'user_id' not in session:
        logger.warning(f'Попытка удаления поста без авторизации. Пост ID: {post_id}')
        flash('Необходимо авторизоваться', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        db = get_db()
        notification_repo = NotificationRepository(db)
        repo = PostRepository(db)
        post = repo.get_by_id(post_id)
        
        if post is None:
            logger.warning(f'Попытка удаления несуществующего поста ID: {post_id}')
            flash('Пост не найден', 'error')
            return redirect(url_for('main.profile'))
        
        if post[3] == session.get('user_id'):
            logger.info(f'Пользователь ID: {session["user_id"]} удаляет пост "{post[1]}" (ID: {post_id})')
            
            notification_repo.log_notification(
                post[3],
                'Удаление поста',
                f'Вы успешно удалили пост "{post[1]}"'
            )
            
            repo.delete_by_id(post_id)
            logger.info(f'Пост ID: {post_id} успешно удалён')
            flash('Пост успешно удалён', 'success')
            return redirect(url_for('main.profile'))
        else:
            logger.warning(f'Попытка удаления чужого поста. Пользователь ID: {session["user_id"]}, '
                         f'Автор поста ID: {post[3]}, Пост ID: {post_id}')
            flash('Недостаточно прав для удаления', 'error')
            return redirect(url_for('main.profile'))
    
    except Exception as e:
        logger.error(f'Ошибка при удалении поста ID {post_id}: {str(e)}')
        flash('Произошла ошибка при удалении поста', 'error')
        return redirect(url_for('main.profile'))


@post_bp.route('/edit_post/<int:post_id>', methods=['POST', 'GET'])
def edit_post(post_id):
    """
    Редактирует пост по ID (только для автора).
    
    GET: Показывает форму редактирования.
    POST: Обрабатывает отправку формы и обновляет пост.
    """
    if 'user_id' not in session:
        logger.warning(f'Попытка редактирования поста без авторизации. Пост ID: {post_id}')
        flash('Необходимо авторизоваться', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        db = get_db()
        repo = PostRepository(db)
        post = repo.get_by_id(post_id)
        
        if post is None:
            logger.warning(f'Попытка редактирования несуществующего поста ID: {post_id}')
            flash('Пост не найден', 'error')
            return redirect(url_for('main.profile'))
        
        if post[3] != session.get('user_id'):
            logger.warning(f'Попытка редактирования чужого поста. Пользователь ID: {session["user_id"]}, '
                         f'Автор поста ID: {post[3]}, Пост ID: {post_id}')
            flash('Недостаточно прав для редактирования', 'error')
            return redirect(url_for('main.profile'))
        
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            
            if not title or not content:
                logger.warning(f'Попытка редактирования с пустыми полями. Пост ID: {post_id}')
                flash('Заголовок и содержимое не могут быть пустыми', 'error')
                return render_template('edit_post.html', post=post)
            
            logger.info(f'Пользователь ID: {session["user_id"]} редактирует пост "{post[1]}" (ID: {post_id})')
            repo.add_edit_post(post_id, title, content)
            logger.info(f'Пост ID: {post_id} успешно отредактирован')
            flash('Пост успешно отредактирован', 'success')
            return redirect(url_for("main.profile"))
        
        return render_template('edit_post.html', post=post)
    
    except Exception as e:
        logger.error(f'Ошибка при редактировании поста ID {post_id}: {str(e)}')
        flash('Произошла ошибка при редактировании поста', 'error')
        return redirect(url_for('main.profile'))


@post_bp.route('/search')
def search():
    """Поиск постов по ключевым словам."""
    try:
        query = request.args.get('q', '').strip()
        db = get_db()
        user_repo = UserRepository(db)
        posts_repo = PostRepository(db)
        
        if query:
            logger.info(f'Поисковый запрос: "{query}"')
            posts = posts_repo.search_posts(query)
            logger.info(f'Найдено {len(posts)} постов по запросу "{query}"')
        else:
            posts = []
            logger.debug('Пустой поисковый запрос')
        
        return render_template('index.html',
                             posts=posts,
                             users=user_repo.get_all_users(),
                             user_name=session.get('user_name'),
                             search_query=query)
    
    except Exception as e:
        logger.error(f'Ошибка при поиске: {str(e)}')
        flash('Произошла ошибка при поиске', 'error')
        return redirect(url_for('main.index'))


@post_bp.route('/category/<int:category_id>')
def category_posts(category_id):
    """Отображает посты по категории с пагинацией."""
    try:
        db = get_db()
        post_repo = PostRepository(db)
        category_repo = CategoriesRepository(db)
        
        category = category_repo.get_all_data_categories_by_id(category_id)
        if not category:
            logger.warning(f'Запрос несуществующей категории ID: {category_id}')
            flash('Категория не найдена', 'error')
            return redirect(url_for('main.index'))
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        
        posts = post_repo.get_posts_by_category_paginated(category_id, page, per_page)
        total = post_repo.count_posts_by_category(category_id)
        total_pages = (total + per_page - 1) // per_page
        
        logger.info(f'Просмотр категории ID: {category_id} ("{category[1]}"), страница {page}/{total_pages}')
        
        return render_template('category.html',
                             posts=posts,
                             category=category,
                             user_name=session.get('user_name'),
                             category_id=category_id,
                             page=page,
                             total_pages=total_pages,
                             per_page=per_page)
    
    except Exception as e:
        logger.error(f'Ошибка при загрузке категории ID {category_id}: {str(e)}')
        flash('Произошла ошибка при загрузке категории', 'error')
        return redirect(url_for('main.index'))