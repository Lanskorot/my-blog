"""
Репозиторий для работы с категориями.

Содержит методы для CRUD операций с категориями,
а также для получения статистики по постам в категориях.
"""

import sqlite3

__all__ = ['CategoriesRepository']


class CategoriesRepository:
    def __init__(self, db_connection):
        """Сохраняем подключение к базе данных."""
        self.db = db_connection

    def get_all_categories(self) -> list:
        """
        Возвращает все категории.
        
        Returns:
            list: [(id, name, description), ...] или пустой список
        """
        cur = self.db.execute('SELECT * FROM categories ORDER BY name')
        return cur.fetchall()

    def get_categories_by_id(self, cat_id: int) -> str:
        """
        Возвращает название категории по её ID.
        
        Returns:
            str: Название категории или 'Неизвестно'
        """
        cur = self.db.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
        cat_name = cur.fetchone()
        return cat_name[0] if cat_name else 'Неизвестно'

    def get_all_data_categories_by_id(self, category_id: int) -> tuple | None:
        """
        Возвращает все данные категории по её ID.
        
        Returns:
            tuple: (id, name, description) или None
        """
        cur = self.db.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
        return cur.fetchone()

    def count_post_by_category(self) -> list:
        """
        Возвращает количество постов в каждой категории.
        
        Returns:
            list: [(name, id, count), ...]
        """
        cur = self.db.execute("""
            SELECT 
                c.name, 
                c.id, 
                COUNT(pc.post_id) as count
            FROM categories c
            LEFT JOIN post_categories pc ON c.id = pc.category_id
            GROUP BY c.id
            ORDER BY count DESC
        """)
        return cur.fetchall()

    def count_categories(self) -> int:
        """Возвращает общее количество категорий."""
        cur = self.db.execute("SELECT COUNT(*) FROM categories")
        return cur.fetchone()[0]

    def get_posts_by_category(self) -> list:
        """
        Возвращает распределение постов по категориям.
        
        Returns:
            list: [(name, post_count), ...]
        """
        cur = self.db.execute("""
            SELECT categories.name, COUNT(pc.post_id) as post_count
            FROM categories
            LEFT JOIN post_categories pc ON categories.id = pc.category_id
            GROUP BY categories.id
            ORDER BY post_count DESC
        """)
        return cur.fetchall()