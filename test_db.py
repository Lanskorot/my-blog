from werkzeug.security import generate_password_hash

import sqlite3
from datetime import datetime, timedelta
import random

# def fill_test_data():
#     conn = sqlite3.connect('users.db')
    
#     # Очищаем таблицы (с учетом внешних ключей)
#     conn.execute('DELETE FROM post_categories')
#     conn.execute('DELETE FROM posts')
#     conn.execute('DELETE FROM categories')
#     conn.execute('DELETE FROM users')
    
#     # Сброс автоинкремента
#     conn.execute('DELETE FROM sqlite_sequence')
    
#     # Добавляем пользователей
#     users = [
#         ('Андрей', 'lanskorot1@gmail.com', generate_password_hash('123456789')),
#         ('Елена', 'elena@mail.com', generate_password_hash('pass456')),
#         ('Михаил', 'mikhail@mail.com', generate_password_hash('qwerty789')),
#         ('Ольга', 'olga@mail.com', generate_password_hash('olga2024')),
#         ('Дмитрий', 'dmitry@mail.com', generate_password_hash('dima12345')),
#         ('Анна', 'anna@example.com',  generate_password_hash('password123')),
#         ('Петр', 'petr@example.com',  generate_password_hash('password456')),
#         ('Мария', 'maria@example.com',  generate_password_hash('password789')),
#         ('Иван', 'ivan@example.com',  generate_password_hash('password321')),
#         ('Елена', 'elena@example.com',  generate_password_hash('password654')),
#         ('Сергей', 'sergey@example.com',  generate_password_hash('password987')),
#         ('Ольга', 'olga@example.com',  generate_password_hash('password111')),
#         ('Алексей', 'alexey@example.com',  generate_password_hash('password222')),
#         ('Наталья', 'natalya@example.com',  generate_password_hash('password333')),
#         ('Дмитрий', 'dmitry@example.com',  generate_password_hash('password444')),
#     ]
#     conn.executemany('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', users)
    
#     # Добавляем категории
#     categories = [
#         ('Технологии', 'Посты о технологиях, IT и гаджетах'),
#         ('Путешествия', 'Посты о путешествиях, странах и приключениях'),
#         ('Кулинария', 'Рецепты, кулинарные советы и гастрономия'),
#         ('Спорт', 'Новости спорта, тренировки и здоровый образ жизни'),
#         ('Наука', 'Научные открытия, исследования и факты'),
#         ('Искусство', 'Живопись, музыка, театр и творчество'),
#         ('Книги', 'Обзоры книг, литература и писатели'),
#         ('Фильмы', 'Кино, сериалы и кинематограф'),
#         ('Здоровье', 'Советы по здоровью, медицина и психология'),
#         ('Образование', 'Обучение, курсы и саморазвитие'),
#         ('Бизнес', 'Предпринимательство, стартапы и финансы'),
#         ('Фотография', 'Фотосъемка, обработка и советы фотографам'),
#     ]
#     conn.executemany('INSERT INTO categories (name, description) VALUES (?, ?)', categories)
    
#     # Получаем ID
#     user_ids = [row[0] for row in conn.execute('SELECT id FROM users').fetchall()]
#     category_ids = [row[0] for row in conn.execute('SELECT id FROM categories').fetchall()]
    
#     # Посты с привязкой к категориям
#     posts_data = [
#         # Технологии
#         ('Введение в Python', 'Python — это мощный язык программирования, который используется в веб-разработке, науке о данных, искусственном интеллекте и многих других областях. Он отличается простотой синтаксиса и огромным сообществом.', user_ids[0], [category_ids[0], category_ids[4]]),
#         ('Новый смартфон 2024: полный обзор', 'Представляем вашему вниманию новый флагманский смартфон 2024 года. Улучшенная камера, мощный процессор и стильный дизайн. Сравнение с конкурентами.', user_ids[3], [category_ids[0], category_ids[11]]),
#         ('Как работает искусственный интеллект', 'Искусственный интеллект меняет наш мир. Нейросети, машинное обучение, глубокое обучение - простыми словами о сложном. Примеры использования в повседневной жизни.', user_ids[7], [category_ids[0], category_ids[4], category_ids[9]]),
#         ('Облачные технологии: будущее уже здесь', 'Что такое облачные вычисления? Преимущества использования облачных сервисов для бизнеса и обычных пользователей. Топ-5 облачных платформ.', user_ids[9], [category_ids[0], category_ids[10]]),
        
#         # Путешествия
#         ('Мое путешествие в горы', 'Прошлым летом я отправился в горы Алтая. Восхождение на вершину, ночевка в палатке и невероятные закаты. Советы для начинающих туристов.', user_ids[1], [category_ids[1], category_ids[3]]),
#         ('Топ-10 мест для отдыха в Европе', 'Париж, Рим, Барселона, Амстердам и другие прекрасные города Европы. Лучшее время для посещения, достопримечательности и местная кухня.', user_ids[4], [category_ids[1], category_ids[2]]),
#         ('Путешествие по Золотому кольцу', 'Маршрут по древним русским городам: Сергиев Посад, Переславль-Залесский, Ростов Великий, Ярославль, Кострома. История и архитектура.', user_ids[6], [category_ids[1], category_ids[7]]),
#         ('Как сэкономить на путешествиях', 'Практические советы: дешевые авиабилеты, бюджетное жилье, еда в путешествиях. Лайфхаки от бывалого путешественника.', user_ids[8], [category_ids[1], category_ids[10]]),
        
#         # Кулинария
#         ('Рецепт пасты карбонара', 'Вкуснейшая паста с беконом, сыром пармезан и яйцом. Настоящий итальянский рецепт с секретами приготовления. Пошаговая инструкция.', user_ids[2], [category_ids[2], category_ids[8]]),
#         ('Идеальный завтрак: яичница по-французски', 'Нежная и воздушная яичница с сыром и зеленью. Секрет заключается в правильной технике приготовления и свежих ингредиентах.', user_ids[5], [category_ids[2]]),
#         ('Печенье с шоколадной крошкой', 'Хрустящие снаружи и мягкие внутри печенья с кусочками шоколада. Лучший рецепт для семейного чаепития.', user_ids[0], [category_ids[2], category_ids[6]]),
#         ('Салат Цезарь с курицей', 'Классический рецепт салата Цезарь с хрустящим салатом, курицей, пармезаном и соусом. Идеальное блюдо для обеда.', user_ids[3], [category_ids[2], category_ids[8]]),
        
#         # Спорт
#         ('Функциональные тренировки для начинающих', 'Программа тренировок для тех, кто только начинает заниматься спортом. Упражнения с собственным весом и гантелями.', user_ids[4], [category_ids[3], category_ids[8]]),
#         ('Йога: путь к гармонии', 'Влияние йоги на физическое и психическое здоровье. Основные асаны для начинающих. Медитация и дыхательные практики.', user_ids[6], [category_ids[3], category_ids[8], category_ids[9]]),
#         ('Правильное питание для спортсменов', 'Что есть до и после тренировки. Баланс белков, жиров и углеводов. Как питание помогает достичь спортивных целей.', user_ids[7], [category_ids[3], category_ids[2], category_ids[8]]),
#         ('Бег для здоровья: с чего начать', 'Программа подготовки к бегу. Техника бега, дыхание, экипировка. Как избежать травм и получать удовольствие.', user_ids[9], [category_ids[3]]),
        
#         # Наука
#         ('Квантовая физика для чайников', 'Что такое квантовая механика? Простые объяснения сложных концепций. Квантовые компьютеры и их будущее.', user_ids[2], [category_ids[4], category_ids[0]]),
#         ('Космос: последние открытия', 'Новые данные о Марсе, черных дырах и экзопланетах. Телескопы будущего и поиск внеземной жизни.', user_ids[5], [category_ids[4], category_ids[1]]),
#         ('Генетика и CRISPR', 'Как работает технология редактирования генов. Этические вопросы и перспективы использования в медицине.', user_ids[8], [category_ids[4], category_ids[8], category_ids[9]]),
#         ('История Земли: от динозавров до людей', 'Эволюция жизни на планете: динозавры, ледниковые периоды, появление человека и развитие цивилизации.', user_ids[1], [category_ids[4], category_ids[6]]),
        
#         # Искусство и книги
#         ('Ван Гог: жизнь и творчество', 'Трагическая жизнь великого художника, его самые известные картины и влияние на современное искусство.', user_ids[0], [category_ids[5], category_ids[6]]),
#         ('Современная литература: главные книги года', 'Обзор самых значимых книг 2024 года: романы, нон-фикшн и фантастика. Личный список рекомендаций.', user_ids[3], [category_ids[6], category_ids[9]]),
#         ('Музыкальный вкус и психология', 'Как музыка влияет на наше настроение и поведение. Почему мы выбираем определенные жанры.', user_ids[7], [category_ids[5], category_ids[8], category_ids[9]]),
#         ('Фотография: искусство видеть', 'Как развить свой фотографический вкус. Композиция, свет и цвет в фотографии. Советы для начинающих.', user_ids[5], [category_ids[5], category_ids[11]]),
        
#         # Бизнес и образование
#         ('Как открыть свой бизнес', 'Пошаговое руководство для начинающих предпринимателей. Выбор ниши, бизнес-план, регистрация и первые клиенты.', user_ids[9], [category_ids[10], category_ids[9]]),
#         ('Саморазвитие: топ-5 полезных привычек', 'Книги, курсы, упражнения для личностного роста. Как стать продуктивнее и достигать целей.', user_ids[4], [category_ids[9], category_ids[6]]),
#         ('Финансовая грамотность', 'Как управлять деньгами, инвестировать и создавать пассивный доход. Советы по бюджету и накоплениям.', user_ids[6], [category_ids[10], category_ids[9]]),
#         ('Успешное собеседование', 'Как подготовиться к собеседованию, отвечать на сложные вопросы и произвести хорошее впечатление на работодателя.', user_ids[8], [category_ids[9]]),
        
#         # Фильмы и развлечения
#         ('Лучшие фильмы 2024 года', 'Подборка фильмов, которые стоит посмотреть в этом году. Жанры: драма, фантастика, комедия.', user_ids[1], [category_ids[7], category_ids[5]]),
#         ('Сериалы, которые обсуждают все', 'Топ-5 сериалов года. Что посмотреть в выходные на Netflix и других платформах.', user_ids[3], [category_ids[7], category_ids[0]]),
#     ]
    
#     # Вставляем посты и связи
#     created_posts = []
#     for title, content, author_id, cats in posts_data:
#         # Генерируем случайную дату создания (за последние 30 дней)
#         days_ago = random.randint(0, 30)
#         hours_ago = random.randint(0, 23)
#         created_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
        
#         # Вставляем пост
#         cur = conn.execute(
#             'INSERT INTO posts (title, content, author_id, created_at) VALUES (?, ?, ?, ?)',
#             (title, content, author_id, created_at.isoformat())
#         )
#         post_id = cur.lastrowid
#         created_posts.append(post_id)
        
#         # Связываем с категориями
#         for cat_id in cats:
#             try:
#                 conn.execute(
#                     'INSERT INTO post_categories (post_id, category_id) VALUES (?, ?)',
#                     (post_id, cat_id)
#                 )
#             except sqlite3.IntegrityError:
#                 pass
    
#     conn.commit()
#     conn.close()
    
#     # Выводим статистику
#     print("✅ Тестовые данные успешно добавлены!")
#     print(f"   Пользователей: {len(users)}")
#     print(f"   Категорий: {len(categories)}")
#     print(f"   Постов: {len(posts_data)}")
#     print(f"   Создано постов в базе: {len(created_posts)}")

# def check_data():
#     """Проверка добавленных данных"""
#     conn = sqlite3.connect('users.db')
    
#     # Количество записей
#     users_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
#     categories_count = conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
#     posts_count = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
#     connections_count = conn.execute('SELECT COUNT(*) FROM post_categories').fetchone()[0]
    
#     print("\n📊 Статистика базы данных:")
#     print(f"   Всего пользователей: {users_count}")
#     print(f"   Всего категорий: {categories_count}")
#     print(f"   Всего постов: {posts_count}")
#     print(f"   Связей пост-категория: {connections_count}")
    
#     # Выводим несколько примеров
#     print("\n📝 Примеры постов:")
#     sample_posts = conn.execute('''
#         SELECT 
#             p.title,
#             u.name as author,
#             GROUP_CONCAT(c.name, ', ') as categories
#         FROM posts p
#         JOIN users u ON p.author_id = u.id
#         LEFT JOIN post_categories pc ON p.id = pc.post_id
#         LEFT JOIN categories c ON pc.category_id = c.id
#         GROUP BY p.id
#         ORDER BY p.created_at DESC
#         LIMIT 5
#     ''').fetchall()
    
#     for post in sample_posts:
#         print(f"   📌 {post[0]} (автор: {post[1]}) -> {post[2] or 'без категорий'}")
    
#     # Выводим топ категорий по количеству постов
#     print("\n🏷️ Топ категорий:")
#     top_categories = conn.execute('''
#         SELECT 
#             c.name,
#             COUNT(pc.post_id) as post_count
#         FROM categories c
#         LEFT JOIN post_categories pc ON c.id = pc.category_id
#         GROUP BY c.id
#         ORDER BY post_count DESC
#         LIMIT 5
#     ''').fetchall()
    
#     for cat in top_categories:
#         print(f"   📂 {cat[0]} -> {cat[1]} постов")
    
#     conn.close()

# if __name__ == '__main__':
#     fill_test_data()
#     check_data()

# conn = sqlite3.connect('users.db')

# conn.execute("""
#     ALTER TABLE users
#     ADD COLUMN role TEXT NOT NULL DEFAULT 'user'
# """)

# conn.execute("""
#     UPDATE users
#     SET role = 'admin'
#     WHERE id = 1
# """)

