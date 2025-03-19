import re
from getpass import getpass
from models import db, User
from app import app

def validate_email(email):
    email_regex = r"(^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$)"
    return re.match(email_regex, email, re.IGNORECASE) is not None

def validate_password(password, confirm_password):
    if password != confirm_password:
        print("Пароли не совпадают!")
        return False
    elif len(password) < 8:
        print("Пароль должен содержать минимум 8 символов!")
        return False
    return True

def init_db():
    with app.app_context():
        # Создаем все таблицы, если их ещё нет
        db.create_all()

        admin = User.query.filter_by(login="admin").first()
        if admin:
            print("Администратор уже создан.")
            return

        # Берем email администратора из конфига
        admin_email = app.config.get("ADMIN_EMAIL")
        print(f"Используется email администратора: {admin_email}")

        # Если email указан в конфигурации, проверяем его корректность:
        while not validate_email(admin_email):
            print("Неверный формат email, указанный в конфигурации!")
            admin_email = input("Введите корректный email администратора: ")

        # Запрашиваем пароль и подтверждение пароля
        password = getpass("Введите пароль для администратора: ")
        confirm_password = getpass("Подтвердите пароль для администратора: ")

        while not validate_password(password, confirm_password):
            password = getpass("Введите пароль для администратора: ")
            confirm_password = getpass("Подтвердите пароль для администратора: ")

        # Создаем администратора
        admin_user = User(
            login="admin",
            email=admin_email,
            is_admin=True
        )
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()

        print("Администратор успешно создан!")

if __name__ == "__main__":
    init_db()
