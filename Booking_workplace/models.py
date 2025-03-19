from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Инициализация базы данных
# db будет использоваться для создания всех таблиц

db = SQLAlchemy()

# Модель пользователя
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор пользователя
    login = db.Column(db.String(80), unique=True, nullable=False)  # Логин (уникальный)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email (уникальный)
    pass_hash = db.Column(db.String(256), nullable=False)  # Хеш пароля
    is_admin = db.Column(db.Boolean, default=False)  # Флаг, является ли пользователь администратором
    status = db.Column(db.String(20), default="active")  # Статус пользователя (active / blocked)
    create_dt = db.Column(db.DateTime, default=lambda: datetime.utcnow().replace(microsecond=int(datetime.utcnow().microsecond / 10000) * 10000))  

    # Связь с бронированиями (если пользователь удалён → удаляются его брони)
    bookings = db.relationship("Booking", back_populates="user", cascade="all, delete")

    def set_password(self, password):
        """Создаёт хеш пароля"""
        self.pass_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет пароль"""
        return check_password_hash(self.pass_hash, password)

    def __repr__(self):
        return f"<User {self.login}>"

# Модель локации
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор локации
    seat_count = db.Column(db.Integer, nullable=False)  # Количество рабочих мест в локации
    name_location = db.Column(db.String(60), nullable=False)  # Адрес локации
    address = db.Column(db.String(255), nullable=False)  # Адрес локации
    create_dt = db.Column(db.DateTime, default=lambda: datetime.utcnow().replace(microsecond=int(datetime.utcnow().microsecond / 10000) * 10000))  
    status = db.Column(db.String(20), default="active")  # Статус локации (active / inactive)

    # Связь с местами (если удаляем локацию → удаляем все её места)
    seats = db.relationship("Seat", back_populates="location", cascade="all, delete")

    def __repr__(self):
        return f"<Location {self.address}>"

# Модель рабочего места
class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор рабочего места
    location_id = db.Column(db.Integer, db.ForeignKey("location.id", ondelete="CASCADE"), nullable=False)  # Связь с локацией

    # Связь с локацией
    location = db.relationship("Location", back_populates="seats")

    # Связь с бронированиями (если место удаляется → удаляются его брони)
    bookings = db.relationship("Booking", back_populates="seat", cascade="all, delete")

    def __repr__(self):
        return f"<Seat {self.id} in Location {self.location_id}>"

# Модель бронирования
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор бронирования
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)  # ID пользователя, сделавшего бронь
    seat_id = db.Column(db.Integer, db.ForeignKey("seat.id", ondelete="CASCADE"), nullable=False)  # ID рабочего места
    booking_date = db.Column(db.Date, nullable=False)  # Дата бронирования
    status = db.Column(db.Integer, default=1, nullable=False)
    create_dt = db.Column(db.DateTime, default=lambda: datetime.utcnow().replace(microsecond=int(datetime.utcnow().microsecond / 10000) * 10000))  

    # Связи
    user = db.relationship("User", back_populates="bookings")  # Связь с пользователем
    seat = db.relationship("Seat", back_populates="bookings")  # Связь с рабочим местом

    def __repr__(self):
        return f"<Booking {self.id} - User {self.user_id} Seat {self.seat_id} Date {self.booking_date}>"
