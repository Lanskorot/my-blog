"""
Главный модуль приложения.

Создаёт и настраивает Flask-приложение,
регистрирует blueprints и инициализирует сервисы.
"""

import logging
from datetime import datetime

from flask import Flask, request, session
from flask_cors import CORS

from config import DATABASE, config
from application.db import get_db, close_db, init_db
from application.services.mail_service import init_mail
from application.services.redis_service import init_redis, set_user_active
from application.services.logging_service import setup_logging
from application.services.limiter import limiter
from application.models.auth_tokens import LongTokenRepository
from application.models.user import UserRepository

__all__ = ['create_app']

logger = logging.getLogger(__name__)


def datetime_format(value, format='%d.%m.%Y %H:%M'):
    """
    Фильтр для форматирования даты в шаблонах Jinja2.
    
    Args:
        value: Дата (datetime или строка)
        format: Формат вывода
        
    Returns:
        str: Отформатированная дата
    """
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value
    if isinstance(value, datetime):
        return value.strftime(format)
    return value


def create_app():
    """
    Создаёт и настраивает Flask-приложение.
    
    Returns:
        Flask: Настроенное приложение
    """
    # ============================================
    # СОЗДАНИЕ ПРИЛОЖЕНИЯ
    # ============================================
    app = Flask(__name__)
    app.config['DATABASE'] = DATABASE
    app.config.from_mapping(config)
    
    # ============================================
    # НАСТРОЙКА CORS
    # ============================================
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # ============================================
    # ИНИЦИАЛИЗАЦИЯ СЕРВИСОВ
    # ============================================
    init_mail(app)
    init_redis(app)
    setup_logging(app)
    limiter.init_app(app)
    
    # ============================================
    # НАСТРОЙКА БАЗЫ ДАННЫХ
    # ============================================
    app.teardown_appcontext(close_db)
    app.jinja_env.filters['datetime'] = datetime_format
    
    with app.app_context():
        init_db()
    
    # ============================================
    # ПРОВЕРКА АУТЕНТИФИКАЦИИ (перед каждым запросом)
    # ============================================
    @app.before_request
    def check_auth():
        """Проверяет авторизацию пользователя перед каждым запросом."""
        # Пропускаем статические файлы
        if request.endpoint and request.endpoint.startswith('static'):
            return
        
        try:
            # Если пользователь уже в сессии
            if 'user_id' in session:
                db = get_db()
                db.execute(
                    'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                    (session['user_id'],)
                )
                db.commit()
                set_user_active(session['user_id'], expire_seconds=300)
            
            # Проверка токена из куки
            token = request.cookies.get('auth_token')
            if token:
                db = get_db()
                auth_repo = LongTokenRepository(db)
                user_id = auth_repo.validate_auth_token(token)
                
                if user_id:
                    user_repo = UserRepository(db)
                    user = user_repo.get_by_id(user_id)
                    if user:
                        session['user_id'] = user[0]
                        session['email'] = user[2]
                        session['name'] = user[1]
                        return
                    else:
                        auth_repo.delete_auth_token(token)
                session.clear()
                
        except Exception as e:
            app.logger.error(f"Ошибка в check_auth: {e}")
            session.clear()
    
    # ============================================
    # РЕГИСТРАЦИЯ BLUEPRINTS
    # ============================================
    from application.views.main import main_bp
    from application.views.auth import auth_bp
    from application.views.post import post_bp
    from application.views.admin import admin_bp
    from application.views.api import api_bp
    from application.views.errors import errors_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(post_bp, url_prefix='/post')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(errors_bp)
    
    return app