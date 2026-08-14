import redis
from flask import current_app
import json
from datetime import datetime

from application.models.posts import PostRepository
from application.db import get_db

# Глобальный клиент (будет инициализирован при старте)
redis_client = None

class DateTimeEncoder(json.JSONEncoder):
    """Кастомный JSON encoder для datetime объектов"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Превращает datetime в строку "2024-08-04T14:30:00"
        return super().default(obj)

def init_redis(app):
    """Инициализация Redis клиента с конфигурацией из app."""
    global redis_client
    redis_client = redis.Redis(
        host=app.config.get('REDIS_HOST', 'localhost'),
        port=app.config.get('REDIS_PORT', 6379),
        db=app.config.get('REDIS_DB', 0),
        decode_responses=True  # чтобы получать строки вместо байтов
    )
    # Проверяем соединение
    try:
        redis_client.ping()
        print("✅ Redis подключён")
    except redis.ConnectionError:
        print("⚠️ Redis недоступен, работаем без кэширования")
        redis_client = None

def set_user_active(user_id: int, expire_seconds: int = 300):
    """Отмечает пользователя как активного на expire_seconds секунд."""
    if redis_client is None:
        return
    key = f"active_user:{user_id}"
    redis_client.setex(key, expire_seconds, "1")  # сохраняем отметку

def get_active_users_count() -> int:
    """Возвращает количество активных пользователей."""
    if redis_client is None:
        return 0
    # Ищем все ключи по шаблону active_user:*
    keys = redis_client.keys("active_user:*")
    return len(keys)

def get_active_user_ids() -> list:
    """Возвращает список ID активных пользователей."""
    if redis_client is None:
        return []
    keys = redis_client.keys("active_user:*")
    # Извлекаем ID из ключа (active_user:123)
    return [int(key.split(':')[1]) for key in keys]

def remove_user_activity(user_id: int):
    """Удаляет отметку активности пользователя (при выходе)."""
    if redis_client is None:
        return
    redis_client.delete(f"active_user:{user_id}")
    
    
    
def get_cached_posts(page, per_page):
    if redis_client is None:
        db = get_db()
        repo = PostRepository(db)
        return repo.get_all_with_categories(page, per_page)
    
    cache_key = f'posts_page_{page}_per_{per_page}'
    
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            print('✅ Данные из кеша')
            posts_dicts = json.loads(cached_data)
            # Конвертируем обратно в кортежи
            return [tuple(post.values()) for post in posts_dicts]
    except Exception as e:
        print(f"⚠️ Ошибка чтения кеша: {e}")
    
    db = get_db()
    repo = PostRepository(db)
    posts = repo.get_all_with_categories(page, per_page)
    
    try:
        # Конвертируем кортежи в словари для JSON
        posts_dicts = []
        for post in posts:
            posts_dicts.append({
                'id': post[0],
                'title': post[1],
                'content': post[2],
                'author_id': post[3],
                'created_at': post[4],
                'author_name': post[5],
                'categories': post[6]
            })
        redis_client.setex(cache_key, 60, json.dumps(posts_dicts, cls=DateTimeEncoder))
        print('💾 Данные сохранены в кеш')
    except Exception as e:
        print(f"⚠️ Ошибка сохранения в кеш: {e}")
    
    return posts

