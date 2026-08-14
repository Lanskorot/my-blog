"""
Настройка лимитов запросов для API.

Использует Flask-Limiter для ограничения количества запросов
и защиты от злоупотреблений.
"""

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Настройка хранилища (для продакшена использовать Redis)
storage_uri = os.getenv('LIMITER_STORAGE', 'memory://')

# Создаём экземпляр Limiter (без app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=storage_uri,
)