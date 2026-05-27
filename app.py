from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from config import Config
import logging

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Модели базы данных
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_librarian = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    # Явно указываем связи для избежания неоднозначности
    reservations = db.relationship('Reservation', foreign_keys='Reservation.user_id', backref='reader', lazy=True)

    issued_reservations = db.relationship('Reservation', foreign_keys='Reservation.librarian_issued_id', backref='issuer', lazy=True)

    returned_reservations = db.relationship('Reservation', foreign_keys='Reservation.librarian_returned_id', backref='returner', lazy=True)

    fines = db.relationship('Fine', backref='user_obj', lazy=True)

    def get_registration_date_formatted(self):
        if self.registration_date:
            return self.registration_date.strftime('%d.%m.%Y')
        return 'Не указано'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        return f"{self.last_name} {self.first_name}"

class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))

    def get_full_name(self):
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

class Publisher(db.Model):
    __tablename__ = 'publishers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(17))
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    publication_year = db.Column(db.Integer)
    total_copies = db.Column(db.Integer, default=0)
    available_copies = db.Column(db.Integer, default=0)
    cover_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    genres = db.relationship('Genre', secondary='book_genres', backref='books')
    authors = db.relationship('Author', secondary='book_authors', backref='books')
    publishers = db.relationship('Publisher', secondary='book_publishers', backref='books')
"""    reservations = db.relationship('Reservation', backref='book_obj', lazy=True)
"""
class BookGenre(db.Model):
    __tablename__ = 'book_genres'
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'), primary_key=True)

class BookAuthor(db.Model):
    __tablename__ = 'book_authors'
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), primary_key=True)

class BookPublisher(db.Model):
    __tablename__ = 'book_publishers'
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), primary_key=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'), primary_key=True)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    issued_at = db.Column(db.DateTime)
    due_date = db.Column(db.Date)
    returned_at = db.Column(db.DateTime)
    librarian_issued_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    librarian_returned_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    book_obj = db.relationship('Book', backref='book_reservations_rel', lazy=True)

    user_rel = db.relationship('User',
                               foreign_keys=[user_id],
                               backref='user_reservations_rel',
                               lazy=True)

    issued_by_rel = db.relationship('User',
                                    foreign_keys=[librarian_issued_id],
                                    backref='issued_by_reservations_rel',
                                    lazy=True)

    returned_by_rel = db.relationship('User',
                                      foreign_keys=[librarian_returned_id],
                                      backref='returned_by_reservations_rel',
                                      lazy=True)

    fines_rel = db.relationship('Fine', backref='fine_reservation_rel', lazy=True)
    @property
    def is_overdue(self):
        if self.due_date and self.status == 'issued':
            return date.today() > self.due_date
        return False

    @property
    def days_overdue(self):
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0

class Fine(db.Model):
    __tablename__ = 'fines'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршруты
@app.route('/')
def index():
    """Главная страница"""
    if current_user.is_authenticated and current_user.is_librarian:
        return redirect(url_for('admin_panel'))

    new_books = Book.query.order_by(Book.created_at.desc()).limit(8).all()
    popular_books = Book.query.filter(Book.available_copies > 0) \
        .order_by(Book.available_copies.asc()) \
        .limit(8).all()

    return render_template('index.html',
                           new_books=new_books,
                           popular_books=popular_books)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if current_user.is_authenticated:
        if current_user.is_librarian:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.is_active:
                login_user(user, remember=remember)
                logger.info(f"User {email} logged in successfully")
                next_page = request.args.get('next')
                if user.is_librarian:
                    return redirect(next_page or url_for('admin_panel'))
                return redirect(next_page or url_for('index'))
            else:
                flash('Ваш аккаунт деактивирован', 'danger')
        else:
            flash('Неверный email или пароль', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')

        # Проверяем, существует ли пользователь
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('register'))

        # Создаем нового пользователя
        new_user = User(
            email=email,
            last_name=last_name,
            first_name=first_name,
            phone=phone,
            is_librarian=False
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти в систему.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/books')
def books_list():
    """Список всех книг с возможностью фильтрации"""
    query = Book.query

    # Фильтрация по названию
    search = request.args.get('search')
    if search:
        query = query.filter(Book.title.ilike(f'%{search}%'))

    # Фильтрация по автору
    author_id = request.args.get('author_id')
    if author_id:
        query = query.join(Book.authors).filter(Author.id == author_id)

    # Фильтрация по жанру
    genre_id = request.args.get('genre_id')
    if genre_id:
        query = query.join(Book.genres).filter(Genre.id == genre_id)

    # Фильтрация по наличию
    available_only = request.args.get('available_only')
    if available_only:
        query = query.filter(Book.available_copies > 0)

    books = query.order_by(Book.title).all()
    genres = Genre.query.all()
    authors = Author.query.all()

    return render_template('books_list.html',
                           books=books,
                           genres=genres,
                           authors=authors)

@app.route('/books/<int:book_id>')
def book_detail(book_id):
    """Детальная информация о книге"""
    book = Book.query.get_or_404(book_id)
    can_reserve = (current_user.is_authenticated and
                   not current_user.is_librarian and
                   book.available_copies > 0)

    return render_template('books_detail.html',
                           book=book,
                           can_reserve=can_reserve)

@app.route('/books/add', methods=['GET', 'POST'])
@login_required
def book_add():
    """Добавление новой книги (только для библиотекарей)"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    # Получаем данные для формы (всегда)
    authors = Author.query.all()
    genres = Genre.query.all()
    publishers = Publisher.query.all()

    if request.method == 'POST':
        try:
            # ===== 1. СОЗДАЁМ НОВЫХ АВТОРОВ =====
            new_authors_raw = request.form.get('new_authors', '').strip()
            if new_authors_raw:
                # Формат: "Фамилия Имя Отчество" или "Фамилия Имя"
                for author_line in new_authors_raw.split('\n'):
                    author_line = author_line.strip()
                    if not author_line:
                        continue

                    parts = author_line.split()
                    if len(parts) >= 2:
                        last_name = parts[0]
                        first_name = parts[1]
                        middle_name = ' '.join(parts[2:]) if len(parts) > 2 else None

                        existing = Author.query.filter_by(
                            last_name=last_name,
                            first_name=first_name
                        ).first()

                        if not existing:
                            new_author = Author(
                                last_name=last_name,
                                first_name=first_name,
                                middle_name=middle_name
                            )
                            db.session.add(new_author)
                            db.session.flush()

            # ===== 2. СОЗДАЁМ НОВЫЕ ЖАНРЫ =====
            new_genres_raw = request.form.get('new_genres', '').strip()
            new_genre_ids = []
            if new_genres_raw:
                for genre_name in new_genres_raw.split('\n'):
                    genre_name = genre_name.strip()
                    if not genre_name:
                        continue

                    existing = Genre.query.filter_by(name=genre_name).first()
                    if existing:
                        new_genre_ids.append(existing.id)
                    else:
                        new_genre = Genre(name=genre_name)
                        db.session.add(new_genre)
                        db.session.flush()
                        new_genre_ids.append(new_genre.id)

            # ===== 3. СОЗДАЁМ НОВЫЕ ИЗДАТЕЛЬСТВА =====
            new_publishers_raw = request.form.get('new_publishers', '').strip()
            new_publisher_ids = []
            if new_publishers_raw:
                for publisher_name in new_publishers_raw.split('\n'):
                    publisher_name = publisher_name.strip()
                    if not publisher_name:
                        continue

                    existing = Publisher.query.filter_by(name=publisher_name).first()
                    if existing:
                        new_publisher_ids.append(existing.id)
                    else:
                        new_publisher = Publisher(name=publisher_name)
                        db.session.add(new_publisher)
                        db.session.flush()
                        new_publisher_ids.append(new_publisher.id)

            # ===== 4. СОЗДАЁМ КНИГУ =====
            book = Book(
                isbn=request.form.get('isbn'),
                title=request.form.get('title'),
                description=request.form.get('description'),
                publication_year=request.form.get('publication_year'),
                total_copies=int(request.form.get('total_copies', 0)),
                available_copies=int(request.form.get('available_copies', 0)),
                cover_url=request.form.get('cover_url'),
            )
            db.session.add(book)
            db.session.flush()

            # Добавляем выбранных авторов
            author_ids = request.form.getlist('author_ids')
            for author_id in author_ids:
                author = Author.query.get(author_id)
                if author:
                    book.authors.append(author)

            # Добавляем выбранные жанры
            genre_ids = request.form.getlist('genre_ids')
            for genre_id in genre_ids:
                genre = Genre.query.get(genre_id)
                if genre:
                    book.genres.append(genre)

            # Добавляем новые жанры (которые только что создали)
            for genre_id in new_genre_ids:
                genre = Genre.query.get(genre_id)
                if genre:
                    book.genres.append(genre)

            # Добавляем выбранные издательства
            publisher_ids = request.form.getlist('publisher_ids')
            for publisher_id in publisher_ids:
                publisher = Publisher.query.get(publisher_id)
                if publisher:
                    book.publishers.append(publisher)

            # Добавляем новые издательства
            for publisher_id in new_publisher_ids:
                publisher = Publisher.query.get(publisher_id)
                if publisher:
                    book.publishers.append(publisher)

            db.session.commit()
            flash('Книга успешно добавлена', 'success')
            return redirect(url_for('book_detail', book_id=book.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding book: {str(e)}")
            flash('Ошибка при добавлении книги. Проверьте правильность заполнения.', 'danger')

            # Возвращаем обратно с сохранением введённых данных
            return render_template('books_add.html',
                                   authors=authors,
                                   genres=genres,
                                   publishers=publishers,
                                   form_data=request.form,
                                   now=datetime.utcnow())

    # GET запрос - пустая форма
    return render_template('books_add.html',
                           authors=authors,
                           genres=genres,
                           publishers=publishers,
                           form_data=None,
                           now=datetime.utcnow())

@app.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def book_edit(book_id):
    """Редактирование книги (только для библиотекарей)"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    book = Book.query.get_or_404(book_id)

    authors = Author.query.all()
    genres = Genre.query.all()
    publishers = Publisher.query.all()

    if request.method == 'POST':
        try:
            # ===== 1. СОЗДАЁМ НОВЫХ АВТОРОВ =====
            new_authors_raw = request.form.get('new_authors', '').strip()
            if new_authors_raw:
                for author_line in new_authors_raw.split('\n'):
                    author_line = author_line.strip()
                    if not author_line:
                        continue

                    parts = author_line.split()
                    if len(parts) >= 2:
                        last_name = parts[0]
                        first_name = parts[1]
                        middle_name = ' '.join(parts[2:]) if len(parts) > 2 else None

                        existing = Author.query.filter_by(
                            last_name=last_name,
                            first_name=first_name
                        ).first()

                        if not existing:
                            new_author = Author(
                                last_name=last_name,
                                first_name=first_name,
                                middle_name=middle_name
                            )
                            db.session.add(new_author)
                            db.session.flush()

            # ===== 2. СОЗДАЁМ НОВЫЕ ЖАНРЫ =====
            new_genres_raw = request.form.get('new_genres', '').strip()
            new_genre_ids = []
            if new_genres_raw:
                for genre_name in new_genres_raw.split('\n'):
                    genre_name = genre_name.strip()
                    if not genre_name:
                        continue

                    existing = Genre.query.filter_by(name=genre_name).first()
                    if existing:
                        new_genre_ids.append(existing.id)
                    else:
                        new_genre = Genre(name=genre_name)
                        db.session.add(new_genre)
                        db.session.flush()
                        new_genre_ids.append(new_genre.id)

            # ===== 3. СОЗДАЁМ НОВЫЕ ИЗДАТЕЛЬСТВА =====
            new_publishers_raw = request.form.get('new_publishers', '').strip()
            new_publisher_ids = []
            if new_publishers_raw:
                for publisher_name in new_publishers_raw.split('\n'):
                    publisher_name = publisher_name.strip()
                    if not publisher_name:
                        continue

                    existing = Publisher.query.filter_by(name=publisher_name).first()
                    if existing:
                        new_publisher_ids.append(existing.id)
                    else:
                        new_publisher = Publisher(name=publisher_name)
                        db.session.add(new_publisher)
                        db.session.flush()
                        new_publisher_ids.append(new_publisher.id)

            # ===== 4. ОБНОВЛЯЕМ КНИГУ =====
            book.isbn = request.form.get('isbn')
            book.title = request.form.get('title')
            book.description = request.form.get('description')
            book.publication_year = request.form.get('publication_year')
            book.total_copies = int(request.form.get('total_copies', 0))
            book.available_copies = int(request.form.get('available_copies', 0))
            book.cover_url = request.form.get('cover_url')

            # Обновляем авторов
            book.authors = []
            author_ids = request.form.getlist('author_ids')
            for author_id in author_ids:
                author = Author.query.get(author_id)
                if author:
                    book.authors.append(author)

            # Обновляем жанры (выбранные + новые)
            book.genres = []
            genre_ids = request.form.getlist('genre_ids')
            for genre_id in genre_ids:
                genre = Genre.query.get(genre_id)
                if genre:
                    book.genres.append(genre)

            for genre_id in new_genre_ids:
                genre = Genre.query.get(genre_id)
                if genre:
                    book.genres.append(genre)

            # Обновляем издательства (выбранные + новые)
            book.publishers = []
            publisher_ids = request.form.getlist('publisher_ids')
            for publisher_id in publisher_ids:
                publisher = Publisher.query.get(publisher_id)
                if publisher:
                    book.publishers.append(publisher)

            for publisher_id in new_publisher_ids:
                publisher = Publisher.query.get(publisher_id)
                if publisher:
                    book.publishers.append(publisher)

            db.session.commit()
            flash('Книга успешно обновлена', 'success')
            return redirect(url_for('book_detail', book_id=book.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error editing book: {str(e)}")
            flash('Ошибка при обновлении книги', 'danger')

            # Возвращаем обратно с сохранением введённых данных
            return render_template('books_edit.html',
                                   book=book,
                                   authors=authors,
                                   genres=genres,
                                   publishers=publishers,
                                   form_data=request.form,
                                   now=datetime.utcnow())

    # GET запрос - показываем форму с текущими данными
    return render_template('books_edit.html',
                           book=book,
                           authors=authors,
                           genres=genres,
                           publishers=publishers,
                           form_data=None,
                           now=datetime.utcnow())

@app.route('/books/<int:book_id>/delete', methods=['POST'])
@login_required
def book_delete(book_id):
    if not current_user.is_librarian:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403

    book = Book.query.get_or_404(book_id)

    try:
        active_reservations = Reservation.query.filter_by(
            book_id=book_id
        ).filter(
            Reservation.status.in_(['active', 'issued'])
        ).count()

        if active_reservations > 0:
            flash('Нельзя удалить книгу с активными бронированиями', 'danger')
            return redirect(url_for('book_detail', book_id=book_id))

        db.session.delete(book)
        db.session.commit()
        flash('Книга успешно удалена', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting book: {str(e)}")
        flash('Ошибка при удалении книги', 'danger')

    return redirect(url_for('books_list'))

@app.route('/reservations')
@login_required
def reservations_list():
    """Список бронирований пользователя"""
    today = date.today()

    if current_user.is_librarian:
        # Для библиотекаря показываем все бронирования
        status_filter = request.args.get('status')
        if status_filter:
            reservations = Reservation.query.filter_by(status=status_filter) \
                .order_by(Reservation.created_at.desc()).all()
        else:
            reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
    else:
        # Для обычных пользователей только их бронирования
        reservations = Reservation.query.filter_by(user_id=current_user.id) \
            .order_by(Reservation.created_at.desc()).all()

    return render_template('reserv_list.html',
                           reservations=reservations,
                           today=today)

@app.route('/books/<int:book_id>/reserve', methods=['POST'])
@login_required
def reserve_book(book_id):
    """Бронирование книги"""
    if current_user.is_librarian:
        flash('Библиотекари не могут бронировать книги', 'danger')
        return redirect(url_for('book_detail', book_id=book_id))

    book = Book.query.get_or_404(book_id)

    # Проверяем доступность книги
    if book.available_copies <= 0:
        flash('Книга временно недоступна', 'danger')
        return redirect(url_for('book_detail', book_id=book_id))

    # Проверяем, не превышен ли лимит бронирований
    active_reservations = Reservation.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).count()

    if active_reservations >= 5:  # Максимум 5 книг
        flash('Вы не можете забронировать более 5 книг одновременно', 'danger')
        return redirect(url_for('book_detail', book_id=book_id))

    fine_amount = get_user_active_fine_amount(current_user.id)
    if fine_amount > 0:
        flash(f'ВНИМАНИЕ! У вас есть неоплаченный штраф на сумму {fine_amount} ₽. '
              f'При получении книги необходимо будет оплатить штраф.', 'warning')

    # Создаем бронирование
    reservation = Reservation(
        book_id=book_id,
        user_id=current_user.id,
        status='active'
    )

    try:
        book.available_copies -= 1
        db.session.add(reservation)
        db.session.commit()
        flash('Книга успешно забронирована', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reserving book: {str(e)}")
        flash('Ошибка при бронировании книги', 'danger')

    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    """Отмена бронирования (только для читателя, который создал бронь)"""
    reservation = Reservation.query.get_or_404(reservation_id)

    if reservation.user_id != current_user.id:
        flash('Нельзя отменить чужое бронирование', 'danger')
        return redirect(url_for('profile'))

    if reservation.status != 'active':
        flash('Можно отменить только активное бронирование', 'danger')
        return redirect(url_for('profile'))

    try:
        reservation.status = 'cancelled'

        book = Book.query.get(reservation.book_id)
        if book:
            book.available_copies += 1

        db.session.commit()
        flash('Бронирование успешно отменено', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling reservation: {str(e)}")
        flash('Ошибка при отмене бронирования', 'danger')

    return redirect(url_for('profile'))

@app.route('/reservations/<int:reservation_id>/issue', methods=['POST'])
@login_required
def issue_book(reservation_id):
    """Оформление выдачи книги (только для библиотекарей)"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    reservation = Reservation.query.get_or_404(reservation_id)

    if reservation.status != 'active':
        flash('Нельзя оформить выдачу для этого бронирования', 'danger')
        return redirect(url_for('reservations_list'))


    fine_amount = get_user_active_fine_amount(reservation.user_id)
    if fine_amount > 0:
        flash(f'НЕЛЬЗЯ ВЫДАТЬ КНИГУ! У читателя {reservation.user_rel.last_name}'
              f' {reservation.user_rel.first_name} есть неоплаченный штраф на сумму {fine_amount} '
              f'₽. Сначала оплатите штраф.', 'danger')
        return redirect(url_for('reservations_list'))
    try:
        reservation.status = 'issued'
        reservation.issued_at = datetime.utcnow()
        reservation.due_date = date.today() + timedelta(days=14)
        reservation.librarian_issued_id = current_user.id

        db.session.commit()
        flash('Выдача книги оформлена', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error issuing book: {str(e)}")
        flash('Ошибка при оформлении выдачи', 'danger')

    return redirect(url_for('reservations_list'))

@app.route('/reservations/<int:reservation_id>/return', methods=['POST'])
@login_required
def return_book(reservation_id):
    """Оформление возврата книги (только для библиотекарей)"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    reservation = Reservation.query.get_or_404(reservation_id)
    book = Book.query.get(reservation.book_id)

    if reservation.status != 'issued':
        flash('Нельзя оформить возврат для этого бронирования', 'danger')
        return redirect(url_for('reservations_list'))

    try:
        reservation.status = 'closed'
        reservation.returned_at = datetime.utcnow()
        reservation.librarian_returned_id = current_user.id

        # Возвращаем книгу в фонд
        if book:
            book.available_copies += 1

        # Проверяем просрочку и начисляем штраф если нужно
        if reservation.due_date and reservation.due_date < date.today():
            overdue_days = (date.today() - reservation.due_date).days
            fine_amount = overdue_days * 10.00  # 10 рублей в день

            existing_fine = Fine.query.filter_by(
                reservation_id=reservation.id,
                status='active'
            ).first()

            if existing_fine:
                existing_fine.amount = fine_amount
                existing_fine.reason = f'Просрочка возврата на {overdue_days} дней'
            else:
                fine = Fine(
                    user_id=reservation.user_id,
                    reservation_id=reservation.id,
                    amount=fine_amount,
                    reason=f'Просрочка возврата на {overdue_days} дней'
                )
                db.session.add(fine)

        db.session.commit()
        flash('Возврат книги оформлен', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error returning book: {str(e)}")
        flash('Ошибка при оформлении возврата', 'danger')

    return redirect(url_for('reservations_list'))

@app.route('/profile')
@login_required
def profile():
    """Личный кабинет пользователя"""
    today = date.today()

    # Получаем активные бронирования
    active_reservations = Reservation.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()

    # Получаем текущие выданные книги
    issued_reservations = Reservation.query.filter_by(
        user_id=current_user.id,
        status='issued'
    ).all()

    # Получаем активные штрафы
    active_fines = Fine.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()

    # Получаем историю
    history_reservations = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.status == 'closed'
    ).order_by(Reservation.returned_at.desc()).limit(10).all()

    return render_template('profile.html',
                           active_reservations=active_reservations,
                           issued_reservations=issued_reservations,
                           active_fines=active_fines,
                           history_reservations=history_reservations,
                           today=today)

@app.route('/admin')
@login_required
def admin_panel():
    """Панель администратора"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    today = date.today()

    # Статистика
    total_books = Book.query.count()
    total_users = User.query.filter_by(is_librarian=False).count()
    active_reservations = Reservation.query.filter_by(status='active').count()
    overdue_reservations = Reservation.query.filter(
        Reservation.status == 'issued',
        Reservation.due_date < today
    ).count()

    unpaid_fines = Fine.query.filter_by(status='active').all()

    overdue_books = Reservation.query.filter(
        Reservation.status == 'issued',
        Reservation.due_date < today
    ).order_by(Reservation.due_date.asc()).all()

    # Последние бронирования
    recent_reservations = Reservation.query.order_by(
        Reservation.created_at.desc()
    ).limit(10).all()

    return render_template('admin.html',
                           total_books=total_books,
                           total_users=total_users,
                           active_reservations=active_reservations,
                           overdue_reservations=overdue_reservations,
                           recent_reservations=recent_reservations,
                           unpaid_fines=unpaid_fines,
                           overdue_books=overdue_books,
                           today=today,
                           has_fine_at_reservation_time=has_fine_at_reservation_time)


def get_user_active_fine_amount(user_id):
    """Возвращает сумму активных штрафов пользователя"""
    fines = Fine.query.filter_by(user_id=user_id, status='active').all()
    total = sum(float(fine.amount) for fine in fines)
    return total


@app.route('/api/books/search')
def api_books_search():
    """API для поиска книг"""
    query = request.args.get('q', '')

    if not query or len(query) < 2:
        return jsonify([])

    books = Book.query.filter(
        Book.title.ilike(f'%{query}%') |
        Book.isbn.ilike(f'%{query}%')
    ).limit(10).all()

    result = []
    for book in books:
        authors_names = []
        for author in book.authors[:2]:  # Берем первых двух авторов
            authors_names.append(f'{author.last_name} {author.first_name[0]}.')

        result.append({
            'id': book.id,
            'title': book.title,
            'authors': ', '.join(authors_names),
            'available_copies': book.available_copies
        })

    return jsonify(result)

def check_overdue_reservations():
    """Проверка просроченных бронирований (запускать по расписанию)"""
    overdue_reservations = Reservation.query.filter(
        Reservation.status == 'issued',
        Reservation.due_date < date.today()
    ).all()

    for reservation in overdue_reservations:
        overdue_days = (date.today() - reservation.due_date).days
        fine_amount = overdue_days * 10.00

        # Проверяем, не был ли уже начислен штраф
        existing_fine = Fine.query.filter_by(
            reservation_id=reservation.id,
            status='active'
        ).first()

        if existing_fine:
            # Обновляем существующий штраф
            existing_fine.amount = fine_amount
            existing_fine.reason = f'Просрочка возврата на {overdue_days} дней'
        else:
            # Создаём новый штраф
            fine = Fine(
                user_id=reservation.user_id,
                reservation_id=reservation.id,
                amount=fine_amount,
                reason=f'Просрочка возврата на {overdue_days} дней'
            )
            db.session.add(fine)

    try:
        db.session.commit()
        logger.info(f"Checked overdue reservations: {len(overdue_reservations)} found")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error checking overdue reservations: {str(e)}")

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Функция для инициализации данных
def init_data():
    """Инициализация начальных данных"""
    with app.app_context():
        # Проверяем, есть ли уже данные
        if User.query.count() > 0:
            print("База данных уже содержит данные.")
            return

        print("Инициализация начальных данных...")

        # Создаем жанры
        genres = ['Роман', 'Детектив', 'Фантастика', 'Фэнтези', 'Поэзия']
        for name in genres:
            genre = Genre(name=name)
            db.session.add(genre)

        # Создаем издательства
        publishers = ['Эксмо', 'АСТ', 'Питер']
        for name in publishers:
            publisher = Publisher(name=name)
            db.session.add(publisher)

        # Создаем авторов
        authors = [
            ('Толстой', 'Лев', 'Николаевич'),
            ('Достоевский', 'Федор', 'Михайлович'),
            ('Пушкин', 'Александр', 'Сергеевич'),
        ]
        for last_name, first_name, middle_name in authors:
            author = Author(last_name=last_name, first_name=first_name, middle_name=middle_name)
            db.session.add(author)

        # Создаем администратора
        admin = User(
            email='admin@library.ru',
            last_name='Иванов',
            first_name='Алексей',
            phone='+79991234567',
            is_librarian=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Создаем обычного пользователя
        user = User(
            email='user@mail.ru',
            last_name='Петров',
            first_name='Иван',
            phone='+79992345678',
            is_librarian=False
        )
        user.set_password('user123')
        db.session.add(user)

        db.session.commit()
        print("Начальные данные созданы успешно!")

@app.route('/force-500')
def force_500():
    # Просто вызываем исключение
    raise Exception("Это тестовая ошибка 500")

# ========== УПРАВЛЕНИЕ ШТРАФАМИ (ДЛЯ БИБЛИОТЕКАРЯ) ==========

@app.route('/admin/fines')
@login_required
def admin_fines():
    """Страница управления штрафами (только библиотекарь)"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    search_query = request.args.get('search', '').strip()

    # Базовый запрос - только активные штрафы
    query = Fine.query.filter_by(status='active')

    # Поиск по фамилии
    if search_query:
        query = query.join(User).filter(
            User.last_name.ilike(f'%{search_query}%') |
            User.first_name.ilike(f'%{search_query}%')
        )

    fines = query.order_by(Fine.created_at.desc()).all()

    return render_template('admin_fines.html',
                           fines=fines,
                           search_query=search_query)


@app.route('/admin/fines/<int:fine_id>/pay', methods=['POST'])
@login_required
def pay_fine(fine_id):
    """Отметить штраф как оплаченный (только для библиотекаря)"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('index'))

    fine = Fine.query.get_or_404(fine_id)

    if fine.status == 'paid':
        flash('Штраф уже оплачен', 'warning')
        return redirect(url_for('admin_fines'))

    try:
        fine.status = 'paid'
        fine.paid_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Fine {fine_id} paid by librarian {current_user.id}")
        flash(f'Штраф {fine.amount} ₽ отмечен как оплаченный', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error paying fine: {str(e)}")
        flash('Ошибка при оплате штрафа', 'danger')

    return redirect(url_for('admin_fines'))

# ========== ДОБАВЛЕНИЕ АВТОРА, ЖАНРА, ИЗДАТЕЛЬСТВА ==========

@app.route('/author/add/ajax', methods=['POST'])
@login_required
def add_author_ajax():
    """Добавление нового автора (возвращается на ту же страницу)"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('book_add'))

    last_name = request.form.get('last_name', '').strip()
    first_name = request.form.get('first_name', '').strip()
    middle_name = request.form.get('middle_name', '').strip()

    if last_name and first_name:
        existing = Author.query.filter_by(last_name=last_name, first_name=first_name).first()
        if not existing:
            author = Author(last_name=last_name, first_name=first_name, middle_name=middle_name or None)
            db.session.add(author)
            db.session.commit()
            flash(f'Автор {last_name} {first_name} добавлен', 'success')

    return redirect(url_for('book_add'))


@app.route('/genre/add/ajax', methods=['POST'])
@login_required
def add_genre_ajax():
    """Добавление нового жанра"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('book_add'))

    name = request.form.get('name', '').strip()

    if name:
        existing = Genre.query.filter_by(name=name).first()
        if not existing:
            genre = Genre(name=name)
            db.session.add(genre)
            db.session.commit()
            flash(f'Жанр "{name}" добавлен', 'success')

    return redirect(url_for('book_add'))


@app.route('/publisher/add/ajax', methods=['POST'])
@login_required
def add_publisher_ajax():
    """Добавление нового издательства"""
    if not current_user.is_librarian:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('book_add'))

    name = request.form.get('name', '').strip()

    if name:
        existing = Publisher.query.filter_by(name=name).first()
        if not existing:
            publisher = Publisher(name=name)
            db.session.add(publisher)
            db.session.commit()
            flash(f'Издательство "{name}" добавлено', 'success')

    return redirect(url_for('book_add'))

def has_fine_at_reservation_time(reservation):
    """Проверяет, был ли у пользователя активный штраф на момент создания бронирования"""
    # Находим все активные штрафы, созданные ДО или В момент бронирования
    active_fines_at_time = Fine.query.filter(
        Fine.user_id == reservation.user_id,
        Fine.status == 'active',
        Fine.created_at <= reservation.created_at
    ).count()

    return active_fines_at_time > 0

from apscheduler.schedulers.background import BackgroundScheduler
import os

def run_check_overdue():
    """Обёртка для вызова с контекстом"""
    with app.app_context():
        check_overdue_reservations()

scheduler = BackgroundScheduler()

# Защита от двойного запуска в debug режиме
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler.add_job(func=run_check_overdue, trigger="interval", days=1)
    scheduler.start()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()      # ← СОЗДАЕТ ТАБЛИЦЫ (если их нет)
        init_data()
        check_overdue_reservations()# ← ЗАПОЛНЯЕТ ДАННЫМИ (если пусто)
    """# Инициализируем данные при первом запуске
    init_data()"""

    app.run(debug=True)###
    ###app.run(host='0.0.0.0', port=5000, debug=True)###