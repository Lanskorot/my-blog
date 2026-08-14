"""
Сервис для отправки email-уведомлений.

Содержит функции для отправки писем о новых постах,
подтверждении регистрации и уведомлениях администратора.
"""

import os
from typing import Optional

from flask import current_app, url_for
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

mail = Mail()


def init_mail(app):
    """Инициализация Flask-Mail с приложением."""
    mail.init_app(app)


def send_new_post_email(email: str, title: str = 'Новый пост') -> None:
    """
    Отправляет письмо о создании нового поста.
    
    Args:
        email: Email получателя
        title: Заголовок поста
    """
    if not email:
        current_app.logger.warning("❌ Email не указан для отправки письма о новом посте")
        return
    
    try:
        with current_app.app_context():
            msg = Message(
                subject='📝 Новый пост в блоге',
                recipients=[email]
            )
            msg.html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ padding: 20px; background: #f8fafc; }}
                    .footer {{ text-align: center; color: #94a3b8; font-size: 0.8rem; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>📝 Новый пост</h2>
                    </div>
                    <div class="content">
                        <p>Здравствуйте!</p>
                        <p>В блоге появился новый пост: <strong>"{title}"</strong></p>
                        <p>Перейдите на сайт, чтобы прочитать его.</p>
                        <p style="text-align: center; margin-top: 20px;">
                            <a href="{url_for('main.index', _external=True)}" style="display: inline-block; padding: 10px 20px; background: #2563eb; color: white; text-decoration: none; border-radius: 5px;">
                                Перейти на сайт
                            </a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>С уважением,<br>Команда блога</p>
                    </div>
                </div>
            </body>
            </html>
            """
            mail.send(msg)
            current_app.logger.info(f"✅ Письмо о новом посте отправлено на {email}")
    except Exception as e:
        current_app.logger.error(f"❌ Ошибка отправки письма о новом посте на {email}: {e}")


def send_welcome_email(email: str, name: str, token: str) -> None:
    """
    Отправляет письмо со ссылкой подтверждения регистрации.
    
    Args:
        email: Email получателя
        name: Имя пользователя
        token: Токен подтверждения
    """
    if not email:
        current_app.logger.warning("❌ Email не указан для отправки письма подтверждения")
        return
    
    try:
        with current_app.app_context():
            confirm_url = url_for('auth.confirm_registration', token=token, _external=True)
            msg = Message(
                subject='✅ Подтверждение регистрации в блоге',
                recipients=[email]
            )
            msg.html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #22c55e; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ padding: 20px; background: #f8fafc; }}
                    .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 5px; }}
                    .footer {{ text-align: center; color: #94a3b8; font-size: 0.8rem; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>👋 Добро пожаловать в блог!</h2>
                    </div>
                    <div class="content">
                        <p>Привет, <strong>{name}</strong>!</p>
                        <p>Спасибо за регистрацию в нашем блоге.</p>
                        <p>Для подтверждения регистрации нажмите на кнопку ниже:</p>
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{confirm_url}" class="button">✅ Подтвердить регистрацию</a>
                        </p>
                        <p>Или перейдите по ссылке:</p>
                        <p><a href="{confirm_url}">{confirm_url}</a></p>
                        <p>Ссылка действительна в течение 24 часов.</p>
                    </div>
                    <div class="footer">
                        <p>С уважением,<br>Команда блога</p>
                    </div>
                </div>
            </body>
            </html>
            """
            mail.send(msg)
            current_app.logger.info(f"✅ Письмо подтверждения отправлено на {email}")
    except Exception as e:
        current_app.logger.error(f"❌ Ошибка отправки письма подтверждения на {email}: {e}")


def new_user(new_user_email: str, new_user_name: str, new_user_id: int) -> None:
    """
    Отправляет уведомление администратору о новом пользователе.
    
    Args:
        new_user_email: Email нового пользователя
        new_user_name: Имя нового пользователя
        new_user_id: ID нового пользователя
    """
    admin_email = os.getenv("ADMIN_MAIL")
    
    if not admin_email:
        current_app.logger.warning("❌ ADMIN_MAIL не указан в переменных окружения")
        return
    
    if not new_user_email:
        current_app.logger.warning("❌ Email нового пользователя не указан")
        return
    
    try:
        with current_app.app_context():
            msg = Message(
                subject='👤 Новый пользователь в блоге',
                recipients=[admin_email]
            )
            msg.html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #eab308; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ padding: 20px; background: #f8fafc; }}
                    .footer {{ text-align: center; color: #94a3b8; font-size: 0.8rem; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>👤 Новый пользователь</h2>
                    </div>
                    <div class="content">
                        <p>В блоге зарегистрировался новый пользователь:</p>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Имя:</strong> {new_user_name}</li>
                            <li><strong>Email:</strong> {new_user_email}</li>
                            <li><strong>ID:</strong> {new_user_id}</li>
                        </ul>
                        <p style="text-align: center; margin-top: 20px;">
                            <a href="{url_for('admin.admin_dashboard', _external=True)}" style="display: inline-block; padding: 10px 20px; background: #2563eb; color: white; text-decoration: none; border-radius: 5px;">
                                Перейти в админ-панель
                            </a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>С уважением,<br>Ваш блог</p>
                    </div>
                </div>
            </body>
            </html>
            """
            mail.send(msg)
            current_app.logger.info(f"✅ Уведомление администратору отправлено на {admin_email}")
    except Exception as e:
        current_app.logger.error(f"❌ Ошибка отправки уведомления администратору: {e}")