"""
Конфигурация приложения.

Загружает настройки из переменных окружения (.env файл).
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# === ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ ===
REQUIRED_VARS = ['MAIL_USERNAME', 'MAIL_PASSWORD']
missing_vars = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(
        f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}"
    )

# === БАЗА ДАННЫХ ===
DATABASE = os.getenv('DATABASE_URL', 'users.db')

# === REDIS ===
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# === ОКРУЖЕНИЕ ===
ENV = os.getenv('ENV', 'development')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# === НАСТРОЙКИ ПРИЛОЖЕНИЯ ===
config = {
    'ENV': ENV,
    'DEBUG': DEBUG,
    'SECRET_KEY': os.getenv('SECRET_KEY', os.urandom(20).hex()),
    
    # === НАСТРОЙКИ ПОЧТЫ ===
    'MAIL_SERVER': os.getenv('MAIL_SERVER', 'smtp.yandex.ru'),
    'MAIL_PORT': int(os.getenv('MAIL_PORT', 465)),
    'MAIL_USE_SSL': os.getenv('MAIL_USE_SSL', 'True').lower() == 'true',
    'MAIL_USE_TLS': os.getenv('MAIL_USE_TLS', 'False').lower() == 'true',
    'MAIL_USERNAME': os.getenv('MAIL_USERNAME'),
    'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD'),
    'MAIL_DEFAULT_SENDER': os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME')),
}

# === НАСТРОЙКИ ДЛЯ РАЗНЫХ ОКРУЖЕНИЙ ===
if ENV == 'production':
    # В продакшене можно добавить дополнительные проверки
    assert DEBUG is False, "DEBUG должен быть False в production!"