"""
Конфигурация тестирования для складского приложения
"""

TEST_CONFIG = {
    # Настройки тестовой базы данных
    'database': {
        'name': 'test_warehouse.db',
        'uri': 'sqlite:///test_warehouse.db'
    },

    # Тестовые пользователи
    'users': {
        'admin': {
            'username': 'test_admin',
            'password': 'admin123',
            'email': 'admin@test.com',
            'is_admin': True
        },
        'user': {
            'username': 'test_user',
            'password': 'user123',
            'email': 'user@test.com',
            'is_admin': False
        }
    },

    # Тестовые товары
    'products': [
        {
            'name': 'Ноутбук тестовый',
            'sku': 'TEST-LAP-001',
            'quantity': 10,
            'price': 50000.0,
            'category': 'Электроника'
        },
        {
            'name': 'Футболка тестовая',
            'sku': 'TEST-TSH-001',
            'quantity': 50,
            'price': 1500.0,
            'category': 'Одежда'
        }
    ],

    # Критерии успешности тестов
    'success_criteria': {
        'min_test_coverage': 0.85,  # 85% покрытие тестами
        'max_response_time': 1000,  # 1 секунда на запрос
        'min_success_rate': 0.95  # 95% успешных тестов
    }
}

# Категории тестов
TEST_CATEGORIES = {
    'authentication': [
        'Регистрация пользователей',
        'Авторизация пользователей',
        'Выход из системы',
        'Управление сессиями'
    ],

    'user_functionality': [
        'Поиск товаров',
        'Просмотр товаров',
        'Фильтрация и сортировка',
        'Доступ к API'
    ],

    'admin_functionality': [
        'Управление товарами',
        'Добавление товаров',
        'Редактирование товаров',
        'Удаление товаров',
        'Статистика'
    ],

    'error_handling': [
        'Обработка 404 ошибок',
        'Обработка 500 ошибок',
        'Валидация данных',
        'Граничные случаи'
    ],

    'performance': [
        'Время отклика',
        'Нагрузка на БД',
        'Множественные запросы'
    ]
}