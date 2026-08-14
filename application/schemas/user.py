"""
Схемы валидации для пользователей.

Содержит Marshmallow схемы для регистрации и входа пользователей.
"""

from marshmallow import Schema, fields, validate

__all__ = ['UserRegistrationSchema', 'UserLoginSchema']


class UserRegistrationSchema(Schema):
    """Схема валидации для регистрации нового пользователя."""
    
    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={
            'required': 'Имя обязательно',
            'validator_failed': 'Имя должно быть от 2 до 100 символов'
        }
    )
    email = fields.Email(
        required=True,
        error_messages={
            'required': 'Email обязателен',
            'invalid': 'Некорректный email'
        }
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128),
        error_messages={
            'required': 'Пароль обязателен',
            'validator_failed': 'Пароль должен быть от 8 до 128 символов'
        }
    )


class UserLoginSchema(Schema):
    """Схема валидации для входа пользователя."""
    
    email = fields.Email(
        required=True,
        error_messages={
            'required': 'Email обязателен',
            'invalid': 'Некорректный email'
        }
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        error_messages={
            'required': 'Пароль обязателен',
            'validator_failed': 'Пароль должен быть не короче 8 символов'
        }
    )
    remember = fields.Bool(required=False, load_default=False)