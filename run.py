"""
Точка входа в приложение.

Запускает Flask-приложение с настройками из переменных окружения.
"""

import os
import logging
from application import create_app

app = create_app()

if __name__ == '__main__':
    # Настройки из переменных окружения (с значениями по умолчанию)
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    logging.info(f'🚀 Запуск приложения на {host}:{port} (debug={debug})')
    
    # Запуск приложения
    app.run(host=host, port=port, debug=debug)