"""
Репозиторий для работы с постами.

Содержит методы для CRUD операций с постами,
фильтрации, поиска, работы с категориями и редактированиями.
"""

import sqlite3

__all__ = ['PostRepository']


class PostRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def add(self, title: str, content: str, author_id: int, category_ids: list | None = None) -> int:
        """Добавляет новый пост и привязывает к категориям."""
        cur = self.db.execute(
            'INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)',
            (title, content, author_id)
        )
        post_id = cur.lastrowid
        self.db.commit()

        if category_ids:
            self.add_categories_to_post(post_id, category_ids)

        return post_id

    def add_categories_to_post(self, post_id: int, category_ids: list) -> None:
        """Привязывает категории к посту."""
        for category_id in category_ids:
            try:
                self.db.execute(
                    'INSERT INTO post_categories (post_id, category_id) VALUES (?, ?)',
                    (post_id, category_id)
                )
            except sqlite3.IntegrityError:
                pass
        self.db.commit()

    def get_all_with_categories(self, page: int = 1, per_page: int = 5) -> list:
        """
        Возвращает все посты с пагинацией и категориями.
        
        Returns:
            list: [(id, title, content, author_id, created_at, author_name, categories), ...]
        """
        offset = (page - 1) * per_page
        cur = self.db.execute('''
            SELECT 
                p.id,
                p.title,
                p.content,
                p.author_id,
                p.created_at,
                u.name as author_name,
                GROUP_CONCAT(c.name, ', ') as categories
            FROM posts p
            JOIN users u ON p.author_id = u.id
            LEFT JOIN post_categories pc ON p.id = pc.post_id
            LEFT JOIN categories c ON pc.category_id = c.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        return cur.fetchall()

    def get_all(self) -> list:
        """Старый метод — для обратной совместимости."""
        cur = self.db.execute('''
            SELECT posts.*, users.name, categories.name as category_name
            FROM posts 
            JOIN users ON posts.author_id = users.id
            LEFT JOIN categories ON posts.category_id = categories.id
            ORDER BY posts.created_at DESC
        ''')
        return cur.fetchall()

    def get_by_id(self, post_id: int) -> tuple | None:
        """
        Возвращает пост по его ID с категориями.
        
        Returns:
            tuple: (id, title, content, author_id, created_at, author_name, categories) или None
        """
        cur = self.db.execute("""
            SELECT 
                p.id,
                p.title,
                p.content,
                p.author_id,
                p.created_at,
                u.name as author_name,
                GROUP_CONCAT(c.name, ', ') as categories
            FROM posts p
            JOIN users u ON p.author_id = u.id
            LEFT JOIN post_categories pc ON p.id = pc.post_id
            LEFT JOIN categories c ON pc.category_id = c.id
            WHERE p.id = ?
            GROUP BY p.id
        """, (post_id,))
        return cur.fetchone()

    def get_by_author_id(self, author_id: int) -> list:
        """
        Возвращает посты по ID автора с категориями.
        
        Returns:
            list: [(id, title, content, author_id, created_at, author_name, categories), ...]
        """
        cur = self.db.execute('''
            SELECT 
                p.id,
                p.title,
                p.content,
                p.author_id,
                p.created_at,
                u.name as author_name,
                GROUP_CONCAT(c.name, ', ') as categories
            FROM posts p
            JOIN users u ON p.author_id = u.id
            LEFT JOIN post_categories pc ON p.id = pc.post_id
            LEFT JOIN categories c ON pc.category_id = c.id
            WHERE p.author_id = ?
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''', (author_id,))
        return cur.fetchall()

    def delete_by_id(self, post_id: int) -> None:
        """Удаляет пост по ID."""
        self.db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        self.db.commit()

    def add_edit_post(self, post_id: int, title: str, content: str, user_id: int) -> None:
        """Обновляет пост и записывает факт редактирования."""
        self.db.execute(
            'UPDATE posts SET title = ?, content = ? WHERE id = ?',
            (title, content, post_id)
        )
        self.db.execute(
            'INSERT INTO post_edits (post_id, edited_by) VALUES (?, ?)',
            (post_id, user_id)
        )
        self.db.commit()

    def get_edit_count(self, post_id: int) -> int:
        """Возвращает количество редактирований поста."""
        cur = self.db.execute(
            "SELECT COUNT(*) FROM post_edits WHERE post_id = ?",
            (post_id,)
        )
        return cur.fetchone()[0]

    def search_posts(self, query: str) -> list:
        """
        Поиск постов по заголовку или содержимому с категориями.
        
        Returns:
            list: [(id, title, content, author_id, created_at, author_name, categories), ...]
        """
        search_pattern = f'%{query}%'
        cur = self.db.execute('''
            SELECT 
                p.id,
                p.title,
                p.content,
                p.author_id,
                p.created_at,
                u.name as author_name,
                GROUP_CONCAT(c.name, ', ') as categories
            FROM posts p
            JOIN users u ON p.author_id = u.id
            LEFT JOIN post_categories pc ON p.id = pc.post_id
            LEFT JOIN categories c ON pc.category_id = c.id
            WHERE p.title LIKE ? OR p.content LIKE ? 
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''', (search_pattern, search_pattern))
        return cur.fetchall()

    def get_posts_by_category(self, category_id: int) -> list:
        """
        Возвращает все посты из указанной категории.
        
        Returns:
            list: [(id, title, content, author_id, created_at, author_name, categories), ...]
        """
        cur = self.db.execute('''
            SELECT 
                p.id,
                p.title,
                p.content,
                p.author_id,
                p.created_at,
                u.name as author_name,
                GROUP_CONCAT(c.name, ', ') as categories
            FROM posts p
            JOIN users u ON p.author_id = u.id
            JOIN post_categories pc ON p.id = pc.post_id
            JOIN categories c ON pc.category_id = c.id
            WHERE pc.category_id = ? 
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''', (category_id,))
        return cur.fetchall()

    def get_categories_for_post(self, post_id: int) -> list:
        """Возвращает все категории для поста."""
        cur = self.db.execute('''
            SELECT c.id, c.name, c.description
            FROM categories c
            JOIN post_categories pc ON c.id = pc.category_id
            WHERE pc.post_id = ?
        ''', (post_id,))
        return cur.fetchall()

    def update_post_categories(self, post_id: int, new_category_ids: list) -> None:
        """Обновляет категории поста (удаляет старые, добавляет новые)."""
        self.db.execute('DELETE FROM post_categories WHERE post_id = ?', (post_id,))
        self.db.commit()
        if new_category_ids:
            self.add_categories_to_post(post_id, new_category_ids)

    def get_filtered_posts(self, filters: dict, page: int = 1, per_page: int = 5) -> list:
        """
        Возвращает посты с применением фильтров.
        
        Args:
            filters: Словарь с параметрами фильтрации
                - category_id: ID категории
                - author_id: ID автора
                - date_from: дата начала (datetime)
                - date_to: дата окончания (datetime)
                - search: поисковый запрос (строка)
            page: Номер страницы
            per_page: Количество постов на странице
        """
        offset = (page - 1) * per_page
        query = """
            SELECT 
                p.id,
                p.title,
                p.content,
                p.author_id,
                p.created_at,
                u.name as author_name,
                GROUP_CONCAT(c.name, ', ') as categories
            FROM posts p
            JOIN users u ON p.author_id = u.id
            LEFT JOIN post_categories pc ON p.id = pc.post_id
            LEFT JOIN categories c ON pc.category_id = c.id
            WHERE 1=1
        """
        params = []

        if 'category_id' in filters:
            query += " AND EXISTS (SELECT 1 FROM post_categories pc2 WHERE pc2.post_id = p.id AND pc2.category_id = ?)"
            params.append(filters['category_id'])

        if 'author_id' in filters:
            query += " AND p.author_id = ?"
            params.append(filters['author_id'])

        if 'date_from' in filters:
            query += " AND p.created_at >= ?"
            params.append(filters['date_from'])

        if 'date_to' in filters:
            query += " AND p.created_at <= ?"
            params.append(filters['date_to'])

        if 'search' in filters:
            query += " AND (p.title LIKE ? OR p.content LIKE ?)"
            search_pattern = f"%{filters['search']}%"
            params.extend([search_pattern, search_pattern])

        query += f"""
            GROUP BY p.id, p.title, p.content, p.author_id, p.created_at, u.name
            ORDER BY p.created_at DESC
            LIMIT {per_page} OFFSET {offset}
        """

        cur = self.db.execute(query, params)
        return cur.fetchall()

    def get_posts_by_category_paginated(self, category_id: int, page: int = 1, per_page: int = 5) -> list:
        """Возвращает посты категории с пагинацией."""
        offset = (page - 1) * per_page
        cur = self.db.execute("""
            SELECT 
                p.id,
                p.title,
                p.content,
                p.author_id,
                p.created_at,
                u.name as author_name
            FROM posts p
            JOIN users u ON p.author_id = u.id
            JOIN post_categories pc ON p.id = pc.post_id
            WHERE pc.category_id = ?
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        """, (category_id, per_page, offset))
        return cur.fetchall()

    def count_posts(self) -> int:
        """Возвращает общее количество постов."""
        cur = self.db.execute("SELECT COUNT(*) FROM posts")
        return cur.fetchone()[0]

    def count_posts_by_category(self, category_id: int) -> int:
        """Возвращает общее количество постов в категории."""
        cur = self.db.execute(
            "SELECT COUNT(*) FROM post_categories WHERE category_id = ?",
            (category_id,)
        )
        return cur.fetchone()[0]

    def get_posts_by_day(self, days: int = 7) -> list:
        """Возвращает количество постов по дням."""
        cur = self.db.execute("""
            SELECT DATE(created_at) as day, COUNT(*) as count
            FROM posts
            WHERE created_at >= DATE('now', ?)
            GROUP BY DATE(created_at)
            ORDER BY day DESC
        """, (f'-{days} days',))
        return cur.fetchall()