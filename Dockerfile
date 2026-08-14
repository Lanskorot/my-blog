# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаём папку для логов и даём права
RUN mkdir -p logs && chown -R 1000:1000 /app

# Создаём пользователя для запуска приложения
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Открываем порт
EXPOSE 5000

# Запускаем приложение через Gunicorn
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "application:create_app()"]