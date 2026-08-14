"""
Главные маршруты приложения.

Содержит обработчики для главной страницы, профиля,
страницы пользователя и информации о пользователях.
"""

import logging
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from application.db import get_db
from application.models.categories import CategoriesRepository
from application.models.notification import NotificationRepository
from application.models.posts import PostRepository
from application.models.user import UserRepository

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

# Константы
PER_PAGE = 5


@main_bp.route('/')
def index():
    """
    Главная страница с постами и фильтрацией.
    
    Поддерживает фильтрацию по категории, автору, дате и поисковому запросу.
    """
    try:
        db = get_db()
        repo = PostRepository(db)
        user_repo = UserRepository(db)
        category_repo = CategoriesRepository(db)
        
        # Получаем параметры пагинации
        page = request.args.get('page', 1, type=int)
        per_page = PER_PAGE
        
        # Получаем параметры фильтрации из GET-запроса
        category_id = request.args.get('category', type=int)
        author_id = request.args.get('author', type=int)
        date_filter = request.args.get('date')  # 'today', 'week', 'month'
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search_query = request.args.get('q', '').strip()
        
        # Логируем запрос с фильтрами
        logger.info(
            f'Запрос главной страницы. Фильтры: категория={category_id}, '
            f'автор={author_id}, дата={date_filter}, поиск="{search_query}", страница={page}'
        )
        
        # Собираем параметры для фильтрации
        filters = {}
        
        # Фильтр по категории
        if category_id:
            filters['category_id'] = category_id
        
        # Фильтр по автору
        if author_id:
            filters['author_id'] = author_id
        
        # Фильтр по дате
        if date_filter == 'today':
            filters['date_from'] = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            filters['date_to'] = datetime.now().replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            logger.debug(f'Фильтр: сегодня с {filters["date_from"]} по {filters["date_to"]}')
            
        elif date_filter == 'week':
            week_ago = datetime.now() - timedelta(days=7)
            filters['date_from'] = week_ago.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            filters['date_to'] = datetime.now().replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            logger.debug(f'Фильтр: за неделю с {filters["date_from"]} по {filters["date_to"]}')
            
        elif date_filter == 'month':
            month_ago = datetime.now() - timedelta(days=30)
            filters['date_from'] = month_ago.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            filters['date_to'] = datetime.now().replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            logger.debug(f'Фильтр: за месяц с {filters["date_from"]} по {filters["date_to"]}')
            
        elif date_from and date_to:
            # Пользовательский диапазон дат
            try:
                filters['date_from'] = datetime.strptime(date_from, '%Y-%m-%d')
                filters['date_to'] = datetime.strptime(date_to, '%Y-%m-%d').replace(
                    hour=23, minute=59, second=59
                )
                logger.debug(
                    f'Фильтр: пользовательский диапазон с {filters["date_from"]} '
                    f'по {filters["date_to"]}'
                )
            except ValueError as e:
                logger.warning(
                    f'Неверный формат даты: date_from={date_from}, date_to={date_to}, ошибка: {e}'
                )
        
        # Поисковый запрос
        if search_query:
            filters['search'] = search_query
        
        # Получаем посты с фильтрацией
        if filters:
            logger.info(f'Применяем фильтры: {filters}')
            posts = repo.get_filtered_posts(filters, page, per_page)
        else:
            posts = repo.get_all_with_categories(page, per_page)
            logger.debug(f'Загружены все посты без фильтров, страница {page}')
        
        # Получаем все категории для сайдбара
        categories = category_repo.get_all_categories()
        # Получаем всех авторов для сайдбара
        authors = user_repo.get_all_users()
        # Получаем количество постов по категориям
        cat_count = category_repo.count_post_by_category()
        
        # Информация о пользователе
        user_name = None
        last_login = None
        admin = False
        
        if 'user_id' in session:
            user_name = session.get('name')
            user_data = user_repo.get_by_id(session.get('user_id'))
            if user_data:
                last_login = user_data[4]  # предполагаем, что последний вход на 4-й позиции
                admin = user_repo.is_admin(session['user_id'])
                logger.debug(f'Пользователь авторизован: {user_name} (ID: {session["user_id"]})')
        
        # Пагинация
        total_posts = repo.count_posts()
        total_pages = (total_posts + per_page - 1) // per_page
        
        logger.info(
            f'Загружено {len(posts)} постов из {total_posts}, страница {page}/{total_pages}'
        )
        
        return render_template(
            'index.html',
            posts=posts,
            users=user_repo.get_all_users(),
            user_name=user_name,
            last_login=last_login,
            cat_count=cat_count,
            categories=categories,
            authors=authors,
            selected_category=category_id,
            selected_author=author_id,
            date_filter=date_filter,
            date_from=date_from,
            date_to=date_to,
            search_query=search_query,
            current_page=page,
            total_pages=total_pages,
            per_page=per_page,
            admin=admin
        )
    
    except Exception as e:
        logger.error(f'Ошибка при загрузке главной страницы: {str(e)}')
        flash('Произошла ошибка при загрузке страницы', 'error')
        return render_template(
            'index.html',
            posts=[],
            users=[],
            user_name=None,
            categories=[],
            authors=[],
            current_page=1,
            total_pages=1
        )


@main_bp.route('/profile')
def profile():
    """Отображает профиль пользователя."""
    try:
        db = get_db()
        repo = PostRepository(db)
        user_repo = UserRepository(db)
        notification_repo = NotificationRepository(db)
        
        user_id = session.get('user_id')
        if not user_id:
            logger.warning('Попытка доступа к профилю без авторизации')
            flash('Необходимо авторизоваться', 'warning')
            return redirect(url_for('auth.login'))
        
        logger.info(f'Загрузка профиля пользователя ID: {user_id}')
        
        user = user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f'Пользователь ID {user_id} не найден в БД')
            session.pop('user_id', None)
            flash('Пользователь не найден', 'error')
            return redirect(url_for('auth.login'))
        
        posts = repo.get_by_author_id(user_id)
        notifications = notification_repo.get_notification_by_user(user_id)
        
        logger.info(
            f'Загружено {len(posts)} постов и {len(notifications)} уведомлений '
            f'для пользователя {user[1]}'
        )
        
        return render_template('profile.html', posts=posts, notifications=notifications)
    
    except Exception as e:
        logger.error(f'Ошибка при загрузке профиля: {str(e)}')
        flash('Произошла ошибка при загрузке профиля', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/user/<int:user_id>')
def user_page(user_id):
    """Отображает страницу пользователя с его постами."""
    try:
        db = get_db()
        repo = PostRepository(db)
        user_repo = UserRepository(db)
        
        logger.info(f'Загрузка страницы пользователя ID: {user_id}')
        
        user = user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f'Пользователь ID {user_id} не найден')
            flash('Пользователь не найден', 'error')
            return redirect(url_for('main.index'))
        
        posts = repo.get_by_author_id(user_id)
        logger.info(f'Загружено {len(posts)} постов пользователя {user[1]} (ID: {user_id})')
        
        return render_template('user_page.html', user=user, posts=posts)
    
    except Exception as e:
        logger.error(f'Ошибка при загрузке страницы пользователя ID {user_id}: {str(e)}')
        flash('Произошла ошибка при загрузке страницы пользователя', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/users-info')
def users_info():
    """Отображает информацию о пользователях."""
    try:
        repo = UserRepository(get_db())
        users = repo.users_count()
        logger.info(
            f'Загружена информация о пользователях: {len(users) if users else 0} записей'
        )
        return render_template("users_info.html", users=users)
    
    except Exception as e:
        logger.error(f'Ошибка при загрузке информации о пользователях: {str(e)}')
        flash('Произошла ошибка при загрузке информации', 'error')
        return redirect(url_for('main.index'))