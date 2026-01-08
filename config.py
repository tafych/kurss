import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'mysql+pymysql://username:password@localhost/warehouse_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки OAuth (Google)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    OAUTH_CREDENTIALS = {
        'google': {
            'id': GOOGLE_CLIENT_ID,
            'secret': GOOGLE_CLIENT_SECRET
        }
    }

    # Настройки сессии
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # Настройки для тестирования
    TESTING = False
    WTF_CSRF_ENABLED = True