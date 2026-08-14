"""
Модуль для работы с базой данных SQLite.

Содержит функции для получения соединения с БД,
закрытия соединения и инициализации таблиц.
"""

import sqlite3
from flask import g
from config import DATABASE

__all__ = ['get_db', 'close_db', 'init_db']


def get_db():
    """
    Возвращает соединение с БД для текущего запроса.
    
    Использует глобальный объект g для хранения соединения
    в течение одного запроса.
    
    Returns:
        sqlite3.Connection: Соединение с базой данных
        
    Raises:
        RuntimeError: Если не удалось подключиться к БД
    """
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(DATABASE)
            # Позволяет обращаться к колонкам по имени
            g.db.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise RuntimeError(f"Ошибка подключения к БД: {e}")
    return g.db


def close_db(exception=None):
    """
    Закрывает соединение после завершения запроса.
    
    Args:
        exception: Исключение, если оно возникло (не используется)
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """
    Создаёт таблицы в базе данных, если их нет.
    
    Создаёт все необходимые таблицы и индексы для работы приложения.
    """
    conn = sqlite3.connect(DATABASE)
    
    # ============================================
    # ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
    # ============================================
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    # ============================================
    # ТАБЛИЦА ПОСТОВ
    # ============================================
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            author_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users(id)
        )
    ''')
    
    # ============================================
    # ТАБЛИЦА ОЖИДАЮЩИХ РЕГИСТРАЦИЙ
    # ============================================
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pending_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            confirmation TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # ============================================
    # ТАБЛИЦА УВЕДОМЛЕНИЙ
    # ============================================
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notification(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ============================================
    # ТАБЛИЦА ТОКЕНОВ АУТЕНТИФИКАЦИИ
    # ============================================
    conn.execute('''
        CREATE TABLE IF NOT EXISTS auth_tokens(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # ============================================
    # ТАБЛИЦА КАТЕГОРИЙ
    # ============================================
    conn.execute('''
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')
    
    # ============================================
    # ТАБЛИЦА СВЯЗИ ПОСТОВ И КАТЕГОРИЙ (MANY-TO-MANY)
    # ============================================
    conn.execute('''
        CREATE TABLE IF NOT EXISTS post_categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
            UNIQUE(post_id, category_id)
        )
    ''')
    
    # ============================================
    # ТАБЛИЦА ИСТОРИИ РЕДАКТИРОВАНИЙ ПОСТОВ
    # ============================================
    conn.execute('''
        CREATE TABLE IF NOT EXISTS post_edits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            edited_by INTEGER NOT NULL,
            edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (edited_by) REFERENCES users(id)
        )
    ''')
    
    # ============================================
    # ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ ЗАПРОСОВ
    # ============================================
    conn.execute('CREATE INDEX IF NOT EXISTS idx_token ON auth_tokens(token)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_notif_user_id ON notification(user_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON posts(author_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_post_title ON posts(title)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_post_content ON posts(content)')
    
    conn.commit()
    conn.close()