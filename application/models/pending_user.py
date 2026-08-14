"""
Репозиторий для работы с ожидающими регистрациями.

Содержит методы для временного хранения данных пользователей
до подтверждения регистрации по email.
"""

import sqlite3

__all__ = ['PendingUserRepository']


class PendingUserRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def add(self, name: str, email: str, token: str, password: str) -> None:
        """
        Сохраняет данные пользователя для подтверждения регистрации.
        
        Args:
            name: Имя пользователя
            email: Email пользователя
            token: Уникальный токен подтверждения
            password: Хеш пароля
        """
        self.db.execute(
            'INSERT INTO pending_registrations (name, email, confirmation, password) VALUES (?, ?, ?, ?)',
            (name, email, token, password)
        )
        self.db.commit()

    def get_by_token(self, token: str) -> tuple | None:
        """
        Получает данные пользователя по токену подтверждения.
        
        Returns:
            tuple: (name, email, password) или None, если токен не найден
        """
        cur = self.db.execute(
            'SELECT name, email, password FROM pending_registrations WHERE confirmation = ?',
            (token,)
        )
        return cur.fetchone()

    def delete_by_token(self, token: str) -> None:
        """Удаляет запись о пользователе после успешного подтверждения."""
        self.db.execute(
            'DELETE FROM pending_registrations WHERE confirmation = ?',
            (token,)
        )
        self.db.commit()