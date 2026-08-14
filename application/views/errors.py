"""
Обработчики ошибок для приложения.

Содержит обработчики для всех HTTP ошибок (404, 403, 401, 405, 400, 500)
и универсальный обработчик исключений.
"""

from traceback import format_exc

from flask import Blueprint, current_app, render_template, request

errors_bp = Blueprint('errors', __name__, template_folder='../templates/errors')


@errors_bp.app_errorhandler(404)
def page_not_found(e):
    """Обработчик 404 ошибки (страница не найдена)."""
    current_app.logger.warning(
        f'404 ошибка: {request.path} - '
        f'Referrer: {request.referrer} - '
        f'IP: {request.remote_addr}'
    )
    return render_template('404.html'), 404


@errors_bp.app_errorhandler(403)
def forbidden_error(e):
    """Обработчик 403 ошибки (доступ запрещён)."""
    current_app.logger.warning(
        f'403 ошибка: {request.path} - '
        f'IP: {request.remote_addr} - '
        f'User-Agent: {request.user_agent}'
    )
    return render_template(
        'error.html',
        error_code=403,
        error_message='Доступ запрещён. У вас недостаточно прав.'
    ), 403


@errors_bp.app_errorhandler(401)
def unauthorized_error(e):
    """Обработчик 401 ошибки (необходима авторизация)."""
    current_app.logger.warning(
        f'401 ошибка: {request.path} - '
        f'IP: {request.remote_addr}'
    )
    return render_template(
        'error.html',
        error_code=401,
        error_message='Необходима авторизация. Пожалуйста, войдите в систему.'
    ), 401


@errors_bp.app_errorhandler(405)
def method_not_allowed(e):
    """Обработчик 405 ошибки (метод не поддерживается)."""
    current_app.logger.warning(
        f'405 ошибка: {request.method} {request.path} - '
        f'IP: {request.remote_addr}'
    )
    return render_template(
        'error.html',
        error_code=405,
        error_message='Метод не поддерживается для этого URL'
    ), 405


@errors_bp.app_errorhandler(400)
def bad_request(e):
    """Обработчик 400 ошибки (неверный запрос)."""
    current_app.logger.warning(
        f'400 ошибка: {request.path} - '
        f'IP: {request.remote_addr} - '
        f'Data: {request.get_data(as_text=True)[:200]}'
    )
    return render_template(
        'error.html',
        error_code=400,
        error_message='Неверный запрос. Проверьте отправляемые данные.'
    ), 400


@errors_bp.app_errorhandler(413)
def payload_too_large(e):
    """Обработчик 413 ошибки (слишком большой файл)."""
    current_app.logger.warning(
        f'413 ошибка: {request.path} - '
        f'IP: {request.remote_addr}'
    )
    return render_template(
        'error.html',
        error_code=413,
        error_message='Слишком большой файл. Максимальный размер 10MB.'
    ), 413


@errors_bp.app_errorhandler(429)
def too_many_requests(e):
    """Обработчик 429 ошибки (слишком много запросов)."""
    current_app.logger.warning(
        f'429 ошибка: {request.path} - '
        f'IP: {request.remote_addr}'
    )
    return render_template(
        'error.html',
        error_code=429,
        error_message='Слишком много запросов. Подождите немного.'
    ), 429


@errors_bp.app_errorhandler(500)
def internal_server_error(e):
    """Обработчик 500 ошибки (внутренняя ошибка сервера)."""
    current_app.logger.error(
        f'500 ошибка: {str(e)}\n'
        f'URL: {request.url}\n'
        f'Method: {request.method}\n'
        f'IP: {request.remote_addr}\n'
        f'{format_exc()}'
    )
    return render_template('500.html'), 500


@errors_bp.app_errorhandler(Exception)
def handle_all_errors(e):
    """Универсальный обработчик всех исключений."""
    if current_app.debug:
        # В режиме отладки показываем подробную информацию
        error_traceback = format_exc()
        return render_template(
            'debug_error.html',
            error_type=type(e).__name__,
            error_message=str(e),
            error_traceback=error_traceback
        ), 500
    else:
        # В продакшене логируем и показываем красивую страницу
        current_app.logger.error(
            f'Необработанное исключение: {str(e)}\n'
            f'URL: {request.url}\n'
            f'Method: {request.method}\n'
            f'IP: {request.remote_addr}\n'
            f'User-Agent: {request.user_agent}\n'
            f'{format_exc()}'
        )
        return render_template('500.html'), 500