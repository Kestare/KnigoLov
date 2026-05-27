"""
Файл заполнения базы данных тестовыми данными
Запуск: python populate_db.py
"""

from app import app, db
from app import User, Book, Author, Genre, Publisher, Reservation, Fine, BookGenre, BookAuthor, BookPublisher
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta

def populate_database():
    """Заполнение базы данных тестовыми данными"""

    with app.app_context():
        print("Очищаем существующие данные...")

        # Правильный порядок удаления (сначала зависимые таблицы)
        db.session.query(Fine).delete()
        db.session.query(Reservation).delete()
        db.session.query(BookGenre).delete()
        db.session.query(BookAuthor).delete()
        db.session.query(BookPublisher).delete()
        db.session.query(Book).delete()
        db.session.query(Author).delete()
        db.session.query(Genre).delete()
        db.session.query(Publisher).delete()
        db.session.query(User).delete()

        db.session.commit()
        print("Данные очищены.")

        # ===== 1. СОЗДАЁМ ЖАНРЫ =====
        genres = ['Роман', 'Детектив', 'Фантастика', 'Фэнтези', 'Поэзия', 'Драма', 'Приключения', 'Ужасы']
        genre_objects = {}
        for name in genres:
            genre = Genre(name=name)
            db.session.add(genre)
            genre_objects[name] = genre
        print(f"Добавлено {len(genres)} жанров")

        # ===== 2. СОЗДАЁМ ИЗДАТЕЛЬСТВА =====
        publishers = ['Эксмо', 'АСТ', 'Питер', 'Манн, Иванов и Фербер', 'Альпина Паблишер']
        publisher_objects = {}
        for name in publishers:
            publisher = Publisher(name=name)
            db.session.add(publisher)
            publisher_objects[name] = publisher
        print(f"Добавлено {len(publishers)} издательств")

        # ===== 3. СОЗДАЁМ АВТОРОВ =====
        authors_data = [
            ('Толстой', 'Лев', 'Николаевич'),
            ('Достоевский', 'Федор', 'Михайлович'),
            ('Пушкин', 'Александр', 'Сергеевич'),
            ('Гоголь', 'Николай', 'Васильевич'),
            ('Чехов', 'Антон', 'Павлович'),
            ('Булгаков', 'Михаил', 'Афанасьевич'),
            ('Тургенев', 'Иван', 'Сергеевич'),
            ('Есенин', 'Сергей', 'Александрович'),
        ]
        author_objects = {}
        for last_name, first_name, middle_name in authors_data:
            author = Author(last_name=last_name, first_name=first_name, middle_name=middle_name)
            db.session.add(author)
            author_objects[f"{last_name} {first_name}"] = author
        print(f"Добавлено {len(authors_data)} авторов")

        # ===== 4. СОЗДАЁМ ПОЛЬЗОВАТЕЛЕЙ =====
        # Библиотекарь
        admin = User(
            email='admin@library.ru',
            last_name='Иванов',
            first_name='Алексей',
            phone='+79991234567',
            is_librarian=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Обычные пользователи
        users_data = [
            ('Петров', 'Иван', 'ivan@mail.ru', '+79992345678', 'user123'),
            ('Сидорова', 'Мария', 'maria@mail.ru', '+79993456789', 'user123'),
            ('Кузнецов', 'Дмитрий', 'dima@mail.ru', '+79994567890', 'user123'),
        ]

        user_objects = {}
        for last_name, first_name, email, phone, password in users_data:
            user = User(
                email=email,
                last_name=last_name,
                first_name=first_name,
                phone=phone,
                is_librarian=False
            )
            user.set_password(password)
            db.session.add(user)
            user_objects[f"{last_name} {first_name}"] = user

        db.session.flush()
        print(f"Добавлено {len(users_data) + 1} пользователей")

        # ===== 5. СОЗДАЁМ КНИГИ (15 штук) =====
        books_data = [
            {'title': 'Война и мир', 'author': 'Толстой Лев', 'genre': 'Роман', 'publisher': 'АСТ', 'year': 1869, 'isbn': '978-5-17-090630-3', 'copies': 5},
            {'title': 'Анна Каренина', 'author': 'Толстой Лев', 'genre': 'Роман', 'publisher': 'Эксмо', 'year': 1877, 'isbn': '978-5-17-090196-4', 'copies': 4},
            {'title': 'Преступление и наказание', 'author': 'Достоевский Федор', 'genre': 'Роман', 'publisher': 'Эксмо', 'year': 1866, 'isbn': '978-5-04-106345-4', 'copies': 4},
            {'title': 'Идиот', 'author': 'Достоевский Федор', 'genre': 'Роман', 'publisher': 'АСТ', 'year': 1869, 'isbn': '978-5-17-090620-4', 'copies': 3},
            {'title': 'Евгений Онегин', 'author': 'Пушкин Александр', 'genre': 'Поэзия', 'publisher': 'Питер', 'year': 1833, 'isbn': '978-5-17-090200-8', 'copies': 6},
            {'title': 'Капитанская дочка', 'author': 'Пушкин Александр', 'genre': 'Роман', 'publisher': 'Эксмо', 'year': 1836, 'isbn': '978-5-17-090210-7', 'copies': 3},
            {'title': 'Мёртвые души', 'author': 'Гоголь Николай', 'genre': 'Роман', 'publisher': 'АСТ', 'year': 1842, 'isbn': '978-5-17-090220-6', 'copies': 4},
            {'title': 'Ревизор', 'author': 'Гоголь Николай', 'genre': 'Драма', 'publisher': 'Питер', 'year': 1836, 'isbn': '978-5-17-090230-5', 'copies': 3},
            {'title': 'Вишнёвый сад', 'author': 'Чехов Антон', 'genre': 'Драма', 'publisher': 'Эксмо', 'year': 1904, 'isbn': '978-5-17-090240-4', 'copies': 4},
            {'title': 'Чайка', 'author': 'Чехов Антон', 'genre': 'Драма', 'publisher': 'АСТ', 'year': 1896, 'isbn': '978-5-17-090250-3', 'copies': 3},
            {'title': 'Мастер и Маргарита', 'author': 'Булгаков Михаил', 'genre': 'Фантастика', 'publisher': 'Питер', 'year': 1967, 'isbn': '978-5-17-090260-2', 'copies': 6},
            {'title': 'Собачье сердце', 'author': 'Булгаков Михаил', 'genre': 'Фантастика', 'publisher': 'Эксмо', 'year': 1925, 'isbn': '978-5-17-090270-1', 'copies': 4},
            {'title': 'Отцы и дети', 'author': 'Тургенев Иван', 'genre': 'Роман', 'publisher': 'АСТ', 'year': 1862, 'isbn': '978-5-17-090280-0', 'copies': 4},
            {'title': 'Муму', 'author': 'Тургенев Иван', 'genre': 'Драма', 'publisher': 'Питер', 'year': 1854, 'isbn': '978-5-17-090290-9', 'copies': 5},
            {'title': 'Стихотворения', 'author': 'Есенин Сергей', 'genre': 'Поэзия', 'publisher': 'Эксмо', 'year': 1920, 'isbn': '978-5-17-090300-6', 'copies': 7},
        ]

        for data in books_data:
            book = Book(
                title=data['title'],
                isbn=data['isbn'],
                description=f'Классическое произведение {data["title"]}',
                publication_year=data['year'],
                total_copies=data['copies'],
                available_copies=data['copies'],
                created_at=datetime.utcnow()
            )
            db.session.add(book)
            db.session.flush()

            # Добавляем автора
            if data['author'] in author_objects:
                book.authors.append(author_objects[data['author']])

            # Добавляем жанр
            if data['genre'] in genre_objects:
                book.genres.append(genre_objects[data['genre']])

            # Добавляем издательство
            if data['publisher'] in publisher_objects:
                book.publishers.append(publisher_objects[data['publisher']])

        db.session.flush()
        print(f"Добавлено {len(books_data)} книг")

        # ===== 6. СОЗДАЁМ БРОНИРОВАНИЯ =====
        ivan = user_objects.get('Петров Иван')
        book_master = Book.query.filter_by(title='Мастер и Маргарита').first()

        if ivan and book_master:
            reservation = Reservation(
                book_id=book_master.id,
                user_id=ivan.id,
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(reservation)
            book_master.available_copies -= 1
            print("Добавлено активное бронирование для Ивана Петрова")

        # ===== 7. СОЗДАЁМ ШТРАФ (для демонстрации) =====
        book_war = Book.query.filter_by(title='Война и мир').first()
        if ivan and book_war:
            old_reservation = Reservation(
                book_id=book_war.id,
                user_id=ivan.id,
                status='issued',
                issued_at=datetime.utcnow() - timedelta(days=15),
                due_date=date.today() - timedelta(days=5),
                created_at=datetime.utcnow() - timedelta(days=20)
            )
            db.session.add(old_reservation)
            db.session.flush()
            book_war.available_copies -= 1

            fine = Fine(
                user_id=ivan.id,
                reservation_id=old_reservation.id,
                amount=50.00,
                reason='Просрочка возврата на 5 дней',
                status='active',
                created_at=datetime.utcnow() - timedelta(days=5)
            )
            db.session.add(fine)
            print("Добавлен штраф для Ивана Петрова (50 руб.)")

        # ===== 8. СОХРАНЯЕМ ВСЁ =====
        try:
            db.session.commit()
            print("\n✅ База данных успешно заполнена тестовыми данными!")
            print(f"📚 Книг: {Book.query.count()}")
            print(f"👥 Пользователей: {User.query.count()}")
            print(f"🎭 Жанров: {Genre.query.count()}")
            print(f"✍️ Авторов: {Author.query.count()}")
            print(f"🏢 Издательств: {Publisher.query.count()}")
            print(f"📋 Бронирований: {Reservation.query.count()}")
            print(f"💰 Штрафов: {Fine.query.count()}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при заполнении: {e}")


if __name__ == '__main__':
    print("=" * 50)
    print("ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ ТЕСТОВЫМИ ДАННЫМИ")
    print("=" * 50)
    populate_database()