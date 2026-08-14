"""
Репозиторий для работы с токенами аутентификации.

Содержит методы для создания, проверки, удаления токенов
и получения информации о них.
"""

import os
import time
from typing import Optional

__all__ = ['LongTokenRepository']


class LongTokenRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def create_auth_token(self, user_id: int, remember: bool = False) -> str:
        """Создаёт токен аутентификации."""
        token = os.urandom(20).hex()
        if remember:
            expires_at = time.time() + 30 * 24 * 60 * 60  # 30 дней
        else:
            expires_at = time.time() + 60 * 60  # 1 час
        self.db.execute(
            'INSERT INTO auth_tokens(user_id, token, expires_at) VALUES (?, ?, ?)',
            (user_id, token, expires_at)
        )
        self.db.commit()
        return token

    def validate_auth_token(self, token: str) -> int | None:
        """Проверяет токен аутентификации и возвращает user_id."""
        cur = self.db.execute(
            'SELECT user_id FROM auth_tokens WHERE token = ? AND expires_at > ?',
            (token, time.time())
        )
        result = cur.fetchone()
        if result:
            return result[0]
        return None

    def delete_auth_token(self, token: str) -> None:
        """Удаляет токен аутентификации."""
        self.db.execute('DELETE FROM auth_tokens WHERE token = ?', (token,))
        self.db.commit()

    def get(self) -> list:
        """
        Возвращает все токены с именами пользователей.
        
        Returns:
            list: [(id, user_id, token, expires_at, name), ...]
        """
        cur = self.db.execute("""
            SELECT auth_tokens.*, users.name
            FROM auth_tokens
            JOIN users ON auth_tokens.user_id = users.id
        """)
        return cur.fetchall()

    def get_token_by_value(self, token: str) -> dict | None:
        """
        Возвращает данные токена по его значению.
        
        Returns:
            dict: {'user_id': int, 'expires_at': float} или None
        """
        cur = self.db.execute(
            "SELECT user_id, expires_at FROM auth_tokens WHERE token = ?",
            (token,)
        )
        row = cur.fetchone()
        if row:
            return {'user_id': row[0], 'expires_at': row[1]}
        return None