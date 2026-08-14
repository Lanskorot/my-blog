"""
Схемы валидации для постов.

Содержит Marshmallow схему для создания и редактирования постов.
"""

from marshmallow import Schema, fields, validate, pre_load

__all__ = ['PostRegistrationSchema']


class PostRegistrationSchema(Schema):
    """Схема валидации для создания нового поста."""
    
    title = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100, error="Название должно быть от 2 до 100 символов"),
        error_messages={'required': 'Название поста обязательно'}
    )
    content = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=5000, error="Содержимое должно быть от 2 до 5000 символов"),
        error_messages={'required': 'Содержимое поста обязательно'}
    )
    
    categories = fields.List(
        fields.Int(),
        required=True,
        validate=validate.Length(min=1, error="Выберите хотя бы одну категорию"),
        error_messages={'required': 'Выберите хотя бы одну категорию'}
    )
    
    @pre_load
    def prepare_categories(self, data, **kwargs):
        """
        Преобразует данные категорий перед загрузкой.
        
        Если пришла строка (один выбор) - превращаем в список.
        Если пришёл список - оставляем как есть.
        """
        if 'categories' in data:
            # Если это строка (выбрана одна категория)
            if isinstance(data['categories'], str):
                if data['categories']:  # если не пустая строка
                    data['categories'] = [data['categories']]
                else:
                    data['categories'] = []  # если пустая строка
            # Если это список - оставляем как есть
            elif isinstance(data['categories'], list):
                # Фильтруем пустые значения
                data['categories'] = [v for v in data['categories'] if v]
        
        return data