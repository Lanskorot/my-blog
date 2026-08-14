"""
Модуль с маршрутами для аутентификации.

Содержит обработчики для регистрации, входа, подтверждения email,
выхода из системы и управления сессиями.
"""

import os
import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from marshmallow import ValidationError
from werkzeug.security import check_password_hash, generate_password_hash

from application.db import get_db
from application.models.auth_tokens import LongTokenRepository
from application.models.notification import NotificationRepository
from application.models.pending_user import PendingUserRepository
from application.models.user import UserRepository
from application.schemas.user import UserLoginSchema, UserRegistrationSchema
from application.services.mail_service import new_user, send_welcome_email
from application.services.redis_service import remove_user_activity

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register/', methods=['GET', 'POST'])
def register():
    """
    Обрабатывает регистрацию нового пользователя.
    
    GET: Показывает форму регистрации.
    POST: Обрабатывает отправку формы и создаёт пользователя.
    """
    if request.method == 'POST':
        schema = UserRegistrationSchema()
        try:
            validated_data = schema.load(request.form)
        except ValidationError as err:
            logger.warning(f'Ошибка валидации регистрации: {err.messages}')
            return render_template('register.html', errors=err.messages, form_data=request.form)
        
        name = validated_data['name']
        email = validated_data['email']
        password = generate_password_hash(validated_data['password'])
        
        try:
            repo = UserRepository(get_db())
            user = repo.get_by_email(email)
            
            if user is None:
                token = os.urandom(20).hex()
                user_repo = PendingUserRepository(get_db())
                user_repo.add(name, email, token, password)
                send_welcome_email(email, name, token)
                
                logger.info(f'Новый пользователь зарегистрирован (ожидает подтверждения): {email}')
                flash('Подтвердите регистрацию на почте', 'success')
                return render_template('register.html')
            else:
                logger.warning(f'Попытка повторной регистрации: {email}')
                return render_template(
                    'register.html',
                    errors={'email': ['Пользователь с таким email уже существует']},
                    form_data=request.form
                )
        
        except Exception as e:
            logger.error(f'Ошибка при регистрации пользователя {email}: {str(e)}')
            flash('Произошла ошибка при регистрации. Попробуйте позже.', 'error')
            return render_template('register.html', form_data=request.form)
    
    return render_template('register.html')


@auth_bp.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Обрабатывает вход пользователя в систему.
    
    GET: Показывает форму входа.
    POST: Обрабатывает отправку формы и авторизует пользователя.
    """
    user_id = session.get('user_id')
    if user_id:
        logger.info(f'Пользователь уже авторизован: {session.get("email")}')
        return redirect(url_for('main.profile'))
    
    if request.method == 'POST':
        schema = UserLoginSchema()
        try:
            validated_data = schema.load(request.form)
        except ValidationError as err:
            logger.warning(f'Ошибка валидации входа: {err.messages}')
            return render_template('login.html', errors=err.messages, form_data=request.form)
        
        email = validated_data['email']
        password = validated_data['password']
        remember = validated_data['remember']
        
        try:
            db = get_db()
            notification_repo = NotificationRepository(db)
            repo = UserRepository(db)
            auth_repo = LongTokenRepository(db)
            user = repo.get_by_email(email)
            
            if user is None:
                logger.warning(f'Попытка входа с несуществующим email: {email}')
                return render_template('login.html', message='**Пользователь не найден**')
            
            if check_password_hash(user[3], password):
                # Успешный вход
                session['user_id'] = user[0]
                session['email'] = user[2]
                session['name'] = user[1]
                
                notification_repo.log_notification(user[0], 'Вход', f'Вы вошли на сайт')
                repo.update_last_login(user[0])
                
                logger.info(f'Пользователь вошёл: {email} (ID: {user[0]})')
                
                if remember:
                    token = auth_repo.create_auth_token(user[0], remember=True)
                    max_age = 30 * 24 * 60 * 60  # 30 дней
                else:
                    token = auth_repo.create_auth_token(user[0])
                    max_age = 60 * 60  # 1 час
                
                response = redirect(url_for('main.profile'))
                response.set_cookie('auth_token', token, max_age=max_age, httponly=True)
                
                return response
            else:
                logger.warning(f'Неверный пароль для пользователя: {email}')
                return render_template('login.html', message='**Неверный пароль**')
        
        except Exception as e:
            logger.error(f'Ошибка при входе пользователя {email}: {str(e)}')
            flash('Произошла ошибка при входе. Попробуйте позже.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


@auth_bp.route('/confirm/<token>')
def confirm_registration(token):
    """Подтверждение регистрации по токену из email."""
    try:
        db = get_db()
        notification_repo = NotificationRepository(db)
        pending_repo = PendingUserRepository(db)
        pending_user = pending_repo.get_by_token(token)
        
        if pending_user:
            name, email, password = pending_user
            user_repo = UserRepository(db)
            user_id = user_repo.add(name, email, password)
            
            session['user_id'] = user_id
            session['email'] = email
            session['name'] = name
            
            new_user(email, name, user_id)
            notification_repo.log_notification(
                user_id,
                'Пользователь успешно добавлен',
                f'Приветственное письмо отправлено на {email}'
            )
            pending_repo.delete_by_token(token)
            
            logger.info(f'Регистрация подтверждена: {email} (ID: {user_id})')
            flash('Регистрация успешно подтверждена!', 'success')
            return redirect(url_for('main.profile'))
        else:
            logger.warning(f'Попытка подтверждения с недействительным токеном: {token[:10]}...')
            flash('Ссылка недействительна или истекла.', 'danger')
            return redirect(url_for('auth.login'))
    
    except Exception as e:
        logger.error(f'Ошибка при подтверждении регистрации (токен: {token[:10]}...): {str(e)}')
        flash('Произошла ошибка при подтверждении регистрации.', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Выход из системы.
    
    GET: Выход текущего пользователя.
    POST: Администратор завершает сессию другого пользователя.
    """
    token_to_delete = request.form.get('user_token') or request.args.get('user_token')
    
    try:
        if token_to_delete:
            # Режим администратора - завершение сессии другого пользователя
            auth_repo = LongTokenRepository(get_db())
            token_data = auth_repo.get_token_by_value(token_to_delete)
            
            if token_data:
                user_id = token_data['user_id']
                remove_user_activity(user_id)
                auth_repo.delete_auth_token(token_to_delete)
                logger.info(f'Администратор завершил сессию пользователя ID: {user_id}')
                flash('Сессия пользователя завершена', 'success')
            else:
                logger.warning(f'Попытка удаления несуществующего токена: {token_to_delete[:10]}...')
                flash('Токен не найден', 'warning')
            
            return redirect(url_for('admin.stats'))
        
        else:
            # Обычный выход текущего пользователя
            user_id = session.get('user_id')
            user_email = session.get('email')
            
            if user_id:
                remove_user_activity(user_id)
                logger.info(f'Пользователь вышел: {user_email} (ID: {user_id})')
            
            token = request.cookies.get('auth_token')
            auth_repo = LongTokenRepository(get_db())
            if token:
                auth_repo.delete_auth_token(token)
            
            session.clear()
            response = redirect(url_for("main.index"))
            response.set_cookie('auth_token', '', expires=0)
            return response
    
    except Exception as e:
        logger.error(f'Ошибка при выходе из системы: {str(e)}')
        flash('Произошла ошибка при выходе из системы.', 'error')
        return redirect(url_for('main.index'))