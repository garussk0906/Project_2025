"""
Модуль Flask-приложения для бронирования рабочих мест.
Основное предназначение:
- Обеспечить аутентификацию пользователей с помощью Flask-Login.
- Предоставить интерфейс для бронирования рабочих мест (с выбором даты: сегодня/завтра).
- Реализовать административную панель для управления пользователями и локациями, включая создание, удаление, смену статуса и сброс пароля.
- Обеспечить работу с базой данных через SQLite, включая создание бронирований, локаций и мест.
- Определить маршруты для авторизации, выхода из системы, бронирования, отмены бронирований и управления данными.
Другим разработчикам:
Данный модуль служит центральной точкой приложения, объединяющей маршруты и бизнес-логику для работы с бронированиями, а также административное управление пользователями и локациями.
"""

from flask import Flask, render_template, redirect, url_for, request, flash
from config import Config
from models import db, User, Location, Seat, Booking
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta, datetime



app = Flask(__name__)
app.config.from_object(Config)

# Инициализация базы данных
db.init_app(app)

# Инициализация Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from datetime import date, timedelta

@property 
def active_booking_today(self):
    """Возвращает бронирование пользователя на сегодня, если оно есть"""
    return Booking.query.filter_by(user_id=self.id, booking_date=date.today()).first()

@property 
def active_booking_tomorrow(self):
    """Возвращает бронирование пользователя на завтра, если оно есть"""
    return Booking.query.filter_by(user_id=self.id, booking_date=date.today() + timedelta(days=1)).first()

# Привяжите их к модели User
User.active_booking_today = active_booking_today
User.active_booking_tomorrow = active_booking_tomorrow


@app.context_processor
def inject_dates():
    today = date.today()
    return {
        'today_date': today.strftime("%d.%m.%Y"),
        'tomorrow_date': (today + timedelta(days=1)).strftime("%d.%m.%Y")
    }
    
### route
@app.route('/')
def index():
    return redirect(url_for('booking'))

@app.route('/admin_panel')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return redirect(url_for('booking'))
    
    # Получаем список всех пользователей и локаций
    users = User.query.all()  # Запрашиваем всех пользователей из базы данных
    locations = Location.query.all()  # Запрашиваем все локации из базы данных

    return render_template('admin_panel.html', users=users, locations=locations)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже авторизован, перенаправляем его на /booking
    if current_user.is_authenticated:
        return redirect(url_for('booking'))
    
    error = None
    
    if request.method == 'POST':
        login_val = request.form.get('login')
        password = request.form.get('password')
        user = User.query.filter_by(login=login_val).first()
        if user and user.check_password(password):
            # Проверка, активен ли пользователь
            if user.status != "active":
                error = 'Пользователь заблокирован'
            else:
                login_user(user)
                return redirect(url_for('booking'))
        else:
            error = 'Неверный логин или пароль'
    admin_email = app.config.get("ADMIN_EMAIL", "admin@example.com")
    return render_template('login.html', error=error, admin_email=admin_email)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/booking')
@login_required
def booking():
    locations = Location.query.all()
    return render_template('booking.html', locations=locations)


@app.route('/book_seat/<int:seat_id>', methods=['POST'])
@login_required
def book_seat(seat_id):
    booking_date_str = request.form.get("booking_date")
    try:
        booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
    except Exception:
        booking_date = date.today()  # по умолчанию сегодня

    # Проверяем, есть ли у пользователя бронь на выбранную дату
    existing_booking = Booking.query.filter_by(user_id=current_user.id, booking_date=booking_date).first()
    if existing_booking:
        return redirect(url_for('location_page', location_id=Seat.query.get(seat_id).location_id,
                                day=('tomorrow' if booking_date != date.today() else 'today')))

    seat = Seat.query.get_or_404(seat_id)
    # Проверка, не забронировано ли место для этой даты
    if Booking.query.filter_by(seat_id=seat_id, booking_date=booking_date).first():
        return redirect(url_for('location_page', location_id=seat.location_id,
                                day=('tomorrow' if booking_date != date.today() else 'today')))

    # Создаём бронирование
    booking = Booking(user_id=current_user.id, seat_id=seat_id, booking_date=booking_date)
    db.session.add(booking)
    db.session.commit()

    return redirect(url_for('location_page', location_id=seat.location_id,
                            day=('tomorrow' if booking_date != date.today() else 'today')))

@app.route('/cancel_booking', methods=['POST'])
@login_required
def cancel_booking():
    booking_id = request.form.get("booking_id")
    booking = Booking.query.get_or_404(booking_id)
    # Определяем день для перенаправления
    day = 'tomorrow' if booking.booking_date != date.today() else 'today'
    
    if booking.user_id != current_user.id:
        location_id = booking.seat.location_id
        return redirect(url_for('location_page', location_id=location_id, day=day))

    location_id = booking.seat.location_id
    db.session.delete(booking)
    db.session.commit()
    
    return redirect(url_for('location_page', location_id=location_id, day=day))

# Создание пользователя
@app.route('/create_user', methods=['POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        return redirect(url_for('booking'))
    
    login_val = request.form.get('login')
    email = request.form.get('email')
    password = request.form.get('password')
    is_admin = True if request.form.get('is_admin') == 'on' else False
    password_hash = generate_password_hash(password)
    new_user = User(login=login_val, email=email, pass_hash=password_hash, is_admin=is_admin)
    db.session.add(new_user)
    db.session.commit()
    
    return redirect(url_for('admin_panel'))

@app.route('/booking/<int:location_id>')
@login_required
def location_page(location_id):
    location = Location.query.get_or_404(location_id)
    seats = location.seats

    # Определяем выбранный день: по умолчанию сегодня
    day = request.args.get('day', 'today')
    if day == 'tomorrow':
        selected_date = date.today() + timedelta(days=1)
    else:
        selected_date = date.today()

    return render_template('location.html',
                           location=location,
                           seats=seats,
                           selected_date=selected_date,
                           day=day)


# Удаление пользователя
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('booking'))

    user_to_delete = User.query.get(user_id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()

    return redirect(url_for('admin_panel'))

# Сброс пароля
@app.route('/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if not current_user.is_admin:
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('booking'))

    user_to_reset = User.query.get(user_id)
    if user_to_reset:
        new_password = '0000'  # Пример временного пароля
        user_to_reset.pass_hash = generate_password_hash(new_password)
        db.session.commit()
        flash(f'Пароль для пользователя {user_to_reset.login} сброшен', 'success')
    else:
        flash('Пользователь не найден', 'danger')

    return redirect(url_for('admin_panel'))


@app.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin:
        flash('У вас нет прав для выполнения этого действия', 'danger')
        return redirect(url_for('booking'))
    
    user = User.query.get_or_404(user_id)
    
    # Переключение статуса
    if user.status == "active":
        user.status = "deactive"
        flash(f"Пользователь {user.login} заблокирован", "success")
    else:
        user.status = "active"
        flash(f"Пользователь {user.login} разблокирован", "success")
    
    db.session.commit()
    return redirect(url_for('admin_panel'))



# Создание локации
@app.route('/create_location', methods=['POST'])
@login_required
def create_location():
    if not current_user.is_admin:
        return redirect(url_for('booking'))

    # Получаем данные из формы
    address = request.form.get('address')
    name_location = request.form.get('name')
    seat_count = request.form.get('seat_count', type=int)

    if not address or seat_count <= 0:
        return redirect(url_for('admin_panel'))

    # Создаем новую локацию
    location = Location(address=address, name_location=name_location, seat_count=seat_count)
    db.session.add(location)
    db.session.flush()  # Сразу получаем ID, но не коммитим

    # Создаем места для этой локации
    seats = [Seat(location_id=location.id) for _ in range(seat_count)]
    db.session.add_all(seats)
    
    db.session.commit()  # Теперь сохраняем все изменения

    return redirect(url_for('admin_panel'))

# Удаление локации
@app.route('/delete_location/<int:location_id>', methods=['POST'])
def delete_location(location_id):
    location = Location.query.get_or_404(location_id)

    # Удаление происходит автоматически благодаря cascade="all, delete"
    db.session.delete(location)
    db.session.commit()

    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    # Импортируем и запускаем init_db перед запуском приложения
    from init_db import init_db
    init_db()
    app.run(debug=True)
