"""
Модуль: config
Путь к файлу: /d:/Projects/Booking_workplace/config.py

Этот модуль предоставляет настройки конфигурации приложения. Он выполняет следующие основные задачи:
1. Определяет BASE_DIR проекта на основе расположения текущего файла.
2. Формирует пути для основных ресурсов:
    - DB_PATH: Путь к базе данных SQLite (app.db).
    - SECRET_KEY_PATH: Путь к файлу, содержащему секретный ключ.
3. Если файл с секретным ключом не существует, генерируется 32-байтовый шестнадцатеричный секретный ключ с использованием модуля 'secrets' и записывается в файл. Затем ключ считывается из файла.
4. Определяет класс Config, который включает:
    - SECRET_KEY: Секретный ключ для криптографических операций.
    - ADMIN_EMAIL: Электронная почта администратора. Может быть переопределена переменной окружения 'ADMIN_EMAIL' (по умолчанию 'Test@gmail.com').
    - SQLALCHEMY_DATABASE_URI: Строка подключения к базе данных SQLite.
    - SQLALCHEMY_TRACK_MODIFICATIONS: Флаг, отключающий отслеживание изменений в SQLAlchemy.

Использование:
    Импортируйте класс Config из этого модуля для настройки параметров вашего приложения.
"""

import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_NAME = "app.db"  # Имя БД
DB_PATH = os.path.join(BASE_DIR, DB_NAME)  # Путь к БД
SECRET_KEY_PATH = os.path.join(BASE_DIR, ".secret_key")  # Файл с ключом

# Генерация и сохранение SECRET_KEY
if not os.path.exists(SECRET_KEY_PATH):
    with open(SECRET_KEY_PATH, "w") as f:
        f.write(secrets.token_hex(32))  # Генерация 32-байтового ключа

# Читаем ключ из файла
with open(SECRET_KEY_PATH, "r") as f:
    SECRET_KEY = f.read().strip()

class Config:
    SECRET_KEY = SECRET_KEY
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'example@gmail.com')  
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
