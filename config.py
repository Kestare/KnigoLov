import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost/new_bd'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки библиотеки
    MAX_BOOKS_PER_USER = 5
    RESERVATION_DAYS = 14
    FINE_PER_DAY = 10.00