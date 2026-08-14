# Блог на Flask

Веб-приложение для ведения блога с административной панелью и API.

## 🚀 Возможности

- Регистрация и авторизация пользователей
- Создание, редактирование и удаление постов
- Категории для постов
- Административная панель
- REST API с документацией
- Кэширование через Redis
- Отправка email уведомлений
- Логирование действий

## 🛠️ Технологии

- Python 3.12
- Flask 3.1
- SQLite
- Redis
- Docker
- Marshmallow
- Pytest

## 📦 Установка

### Локальная установка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd <project-name>

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows

# Установить зависимости
pip install -r requirements.txt

# Скопировать .env.example в .env и заполнить
cp .env.example .env

# Запустить Redis (если установлен)
redis-server

# Запустить приложение
python run.py