"""
Конфигурация pytest для проекта.

Добавляет корневую папку проекта в PYTHONPATH для корректного импорта модулей.
Может содержать общие фикстуры для всех тестов.
"""

import sys
import os

# Добавляем корневую папку проекта в PYTHONPATH
# Это позволяет импортировать модули из application/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

