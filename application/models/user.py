"""
Репозиторий для работы с пользователями.

Содержит методы для CRUD операций с пользователями,
проверки прав и получения статистики.
"""

import sqlite3

__all__ = ['UserRepository']


class UserRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def add(self, name: str, email: str, password: str) -> int:
        """Добавляет нового пользователя в базу данных и возвращает его ID."""
        try:
            cur = self.db.execute(
                'INSERT INTO users (name, email, password) VALUES (?,?,?)',
                (name, email, password)
            )
            self.db.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError('Пользователь с таким email уже существует')

    def get_by_id(self, user_id: int) -> tuple:
        """
        Возвращает пользователя по его ID.
        
        Returns:
            tuple: (id, name, email, password, last_login, role) или None
        """
        cur = self.db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cur.fetchone()

    def get_by_email(self, email: str) -> tuple:
        """
        Возвращает пользователя по его email.
        
        Returns:
            tuple: (id, name, email, password, last_login, role) или None
        """
        cur = self.db.execute('SELECT * FROM users WHERE email = ?', (email,))
        return cur.fetchone()

    def get_all_users(self) -> list:
        """Возвращает всех пользователей."""
        cur = self.db.execute('SELECT * FROM users')
        return cur.fetchall()

    def users_count(self) -> list:
        """
        Возвращает количество постов по пользователю.
        
        Returns:
            list: [(users.name, post_count), ...]
        """
        cur = self.db.execute('''
            SELECT users.name, COUNT(posts.id) as post_count
            FROM posts
            JOIN users ON posts.author_id = users.id
            GROUP BY users.name
        ''')
        return cur.fetchall()

    def update_last_login(self, user_id: int) -> None:
        """Обновляет время последнего входа пользователя."""
        self.db.execute(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            (user_id,)
        )
        self.db.commit()

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором."""
        if not user_id:
            return False
        cur = self.db.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()
        return result and result[0] == 'admin'

    def get_current_user_role(self, user_id: int) -> str | None:
        """Возвращает текущую роль пользователя."""
        if not user_id:
            return None
        cur = self.db.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        result = cur.fetchone()
        return result[0] if result else None

    def count_users(self) -> int:
        """Возвращает общее количество пользователей."""
        cur = self.db.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]

    def get_paginated_users(self, per_page: int, offset: int) -> list:
        """Возвращает список пользователей с пагинацией."""
        cur = self.db.execute("""
            SELECT id, name, email, role
            FROM users
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        return cur.fetchall()

    def delete_user_by_id(self, user_id: int) -> None:
        """Удаляет пользователя по ID."""
        self.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.db.commit()

    def update_user(self, user_id: int, name: str | None = None,
                    email: str | None = None, role: str | None = None) -> bool:
        """
        Обновляет данные пользователя.
        
        Args:
            user_id: ID пользователя
            name: Новое имя (опционально)
            email: Новый email (опционально)
            role: Новая роль (опционально)
            
        Returns:
            bool: True если обновление выполнено, иначе False
        """
        updates = []
        params = []
        if name:
            updates.append('name = ?')
            params.append(name)
        if email:
            updates.append('email = ?')
            params.append(email)
        if role:
            updates.append('role = ?')
            params.append(role)
        if not updates:
            return False
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        self.db.execute(query, params)
        self.db.commit()
        return True

    def get_active_users(self, days: int = 30, limit: int = 5) -> list:
        """
        Возвращает самых активных пользователей за последние N дней.
        
        Args:
            days: Количество дней
            limit: Максимальное количество пользователей
            
        Returns:
            list: [(users.name, post_count), ...]
        """
        cur = self.db.execute("""
            SELECT users.name, COUNT(posts.id) as post_count
            FROM users
            LEFT JOIN posts ON users.id = posts.author_id
            WHERE posts.created_at >= DATE('now', ?) OR posts.created_at IS NULL
            GROUP BY users.id
            ORDER BY post_count DESC
            LIMIT ?
        """, (f'-{days} days', limit))
        return cur.fetchall()