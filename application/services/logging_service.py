import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask

def setup_logging(app):
    """Настройка логирования для Flask приложения"""
    
    # Создаём папку для логов, если её нет
    if not os.path.exists('logs'):
        try:
            os.mkdir('logs')
        except OSError:
            pass  # Игнорируем ошибку создания папки
    
    # Настраиваем файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        'logs/blog.log',
        maxBytes=10485760,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    
    # Формат логов
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Добавляем обработчик в приложение
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Логируем запуск
    app.logger.info('📝 Блог запущен')
    
    return app.logger


def get_logger(name):
    """Возвращает логгер с указанным именем"""
    return logging.getLogger(name)