"""
Репозиторий для работы с уведомлениями.

Содержит методы для логирования, получения и подсчёта уведомлений.
"""

import sqlite3

__all__ = ['NotificationRepository']


class NotificationRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def log_notification(self, user_id: int, action: str, details: str) -> None:
        """Создаёт новое уведомление для пользователя."""
        self.db.execute(
            'INSERT INTO notification(user_id, action, details) VALUES(?, ?, ?)',
            (user_id, action, details)
        )
        self.db.commit()

    def get_notification_by_user(self, user_id: int) -> list:
        """
        Возвращает последние 3 уведомления для пользователя.
        
        Returns:
            list: [(id, user_id, action, details, created_at), ...]
        """
        cur = self.db.execute(
            'SELECT * FROM notification WHERE user_id = ? ORDER BY created_at DESC LIMIT 3',
            (user_id,)
        )
        return cur.fetchall()

    def get_full_info(self) -> list:
        """
        Возвращает все уведомления с информацией о пользователях.
        
        Returns:
            list: [(id, user_id, action, details, created_at, users.name), ...]
        """
        cur = self.db.execute('SELECT * FROM notification')
        return cur.fetchall()

    def count_notification(self) -> int:
        """Возвращает общее количество уведомлений."""
        cur = self.db.execute("SELECT COUNT(*) FROM notification")
        return cur.fetchone()[0]

    def last_5_notification(self) -> list:
        """
        Возвращает последние 5 уведомлений с именами пользователей.
        
        Returns:
            list: [(id, user_id, action, details, created_at, users.name), ...]
        """
        cur = self.db.execute("""
            SELECT notification.*, users.name
            FROM notification
            JOIN users ON notification.user_id = users.id
            ORDER BY created_at DESC
            LIMIT 5
        """)
        return cur.fetchall()