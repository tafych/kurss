from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
import time
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'warehouse-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///warehouse_new.db'  # НОВОЕ ИМЯ ФАЙЛА
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Модели
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    detailed_specs = db.Column(db.Text, default='')
    sku = db.Column(db.String(50), unique=True)
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views_count = db.Column(db.Integer, default=0)


# Декораторы
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Для доступа необходимо войти в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Для доступа необходимо войти в систему', 'warning')
            return redirect(url_for('login'))
        # Используем новую версию запроса без .get()
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            flash('Требуются права администратора', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


def create_database():
    """Создает новую базу данных гарантированно"""
    print("=" * 60)
    print("Создание новой базы данных...")

    # Удаляем старые файлы если существуют
    for db_file in ['warehouse.db', 'warehouse_new.db']:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"✓ Удален старый файл: {db_file}")
                time.sleep(0.5)  # Даем время системе
            except Exception as e:
                print(f"✗ Не удалось удалить {db_file}: {e}")

    # Создаем все таблицы
    try:
        with app.app_context():
            db.create_all()
            print("✓ Таблицы созданы успешно")

            # Добавляем тестовые данные
            add_test_data()
            print("✓ Тестовые данные добавлены")

    except Exception as e:
        print(f"✗ Ошибка при создании БД: {e}")
        return False

    return True


def add_test_data():
    """Добавляет тестовые данные в БД"""
    # Проверяем, есть ли уже пользователи
    if User.query.first():
        return

    # Создаем пользователей
    admin = User(
        username='admin',
        email='admin@warehouse.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )

    user = User(
        username='user',
        email='user@warehouse.com',
        password_hash=generate_password_hash('user123'),
        is_admin=False
    )

    db.session.add(admin)
    db.session.add(user)

    # Создаем категории
    categories = [
        Category(name='Электроника', description='Электронные устройства'),
        Category(name='Одежда', description='Одежда и аксессуары'),
        Category(name='Книги', description='Книги и учебники'),
        Category(name='Мебель', description='Мебель для дома и офиса'),
        Category(name='Продукты', description='Продукты питания')
    ]

    for cat in categories:
        db.session.add(cat)

    db.session.commit()

    # Создаем товары
    products = [
        Product(
            name='Ноутбук Lenovo IdeaPad',
            description='15.6" ноутбук для работы и учебы',
            detailed_specs='Процессор: Intel Core i5\nПамять: 8 ГБ\nSSD: 512 ГБ\nЭкран: 15.6"\nВес: 1.7 кг',
            sku='LAP001',
            quantity=10,
            price=54999.99,
            category_id=1
        ),
        Product(
            name='Смартфон Samsung',
            description='Смартфон с отличной камерой',
            detailed_specs='Экран: 6.1"\nПамять: 128 ГБ\nКамера: 50 Мп\nАккумулятор: 4000 мАч',
            sku='PHN001',
            quantity=15,
            price=39999.99,
            category_id=1
        ),
        Product(
            name='Футболка мужская',
            description='Хлопковая футболка черного цвета',
            detailed_specs='Материал: 100% хлопок\nРазмеры: S-XXL\nЦвет: черный',
            sku='TSH001',
            quantity=50,
            price=1499.99,
            category_id=2
        ),
        Product(
            name='Книга "Python для начинающих"',
            description='Учебник по программированию на Python',
            detailed_specs='Автор: Иван Иванов\nСтраниц: 400\nИздательство: ООО "Издательство"\nГод: 2023',
            sku='BOK001',
            quantity=25,
            price=1299.99,
            category_id=3
        )
    ]

    for prod in products:
        db.session.add(prod)

    db.session.commit()


# Маршруты
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Проверка существования пользователя
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email уже используется', 'danger')
            return redirect(url_for('register'))

        # Создаем пользователя
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=False
        )

        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Войдите в систему.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Ищем пользователя
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('search'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    category_id = request.args.get('category', '')
    sort_by = request.args.get('sort', 'views_count')

    # Базовый запрос
    products_query = Product.query

    # Фильтрация
    if query:
        products_query = products_query.filter(
            Product.name.contains(query) |
            Product.description.contains(query) |
            Product.sku.contains(query)
        )

    if category_id:
        products_query = products_query.filter_by(category_id=category_id)

    # Сортировка
    if sort_by == 'name':
        products_query = products_query.order_by(Product.name)
    elif sort_by == 'price_asc':
        products_query = products_query.order_by(Product.price)
    elif sort_by == 'price_desc':
        products_query = products_query.order_by(Product.price.desc())
    elif sort_by == 'date':
        products_query = products_query.order_by(Product.created_at.desc())
    else:  # views_count
        products_query = products_query.order_by(Product.views_count.desc())

    products = products_query.all()
    categories = Category.query.all()

    return render_template('search.html',
                           products=products,
                           categories=categories,
                           query=query,
                           category_id=category_id,
                           sort_by=sort_by)


@app.route('/product/<int:product_id>')
@login_required
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash('Товар не найден', 'danger')
        return redirect(url_for('search'))

    # Увеличиваем счетчик просмотров
    product.views_count += 1
    db.session.commit()

    return render_template('product_detail.html', product=product)


@app.route('/admin')
@admin_required
def admin():
    products = Product.query.all()
    categories = Category.query.all()

    # Статистика
    stats = {
        'total_products': len(products),
        'total_quantity': sum(p.quantity for p in products),
        'total_value': sum(p.price * p.quantity for p in products),
        'total_views': sum(p.views_count for p in products)
    }

    return render_template('admin.html',
                           products=products,
                           categories=categories,
                           stats=stats)


@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            detailed_specs = request.form.get('detailed_specs', '')
            sku = request.form['sku']
            quantity = int(request.form['quantity'])
            price = float(request.form['price'])
            category_id = request.form.get('category_id')

            # Проверка SKU
            if Product.query.filter_by(sku=sku).first():
                flash('Артикул должен быть уникальным', 'danger')
                return redirect(url_for('add_product'))

            product = Product(
                name=name,
                description=description,
                detailed_specs=detailed_specs,
                sku=sku,
                quantity=quantity,
                price=price,
                category_id=category_id if category_id else None
            )

            db.session.add(product)
            db.session.commit()

            flash('Товар успешно добавлен', 'success')
            return redirect(url_for('admin'))

        except Exception as e:
            flash(f'Ошибка: {str(e)}', 'danger')

    categories = Category.query.all()
    return render_template('add_product.html', categories=categories)


@app.route('/admin/product/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    product = db.session.get(Product, id)
    if not product:
        flash('Товар не найден', 'danger')
        return redirect(url_for('admin'))

    if request.method == 'POST':
        try:
            product.name = request.form['name']
            product.description = request.form['description']
            product.detailed_specs = request.form.get('detailed_specs', '')
            product.sku = request.form['sku']
            product.quantity = int(request.form['quantity'])
            product.price = float(request.form['price'])
            product.category_id = request.form.get('category_id')

            db.session.commit()
            flash('Товар обновлен', 'success')
            return redirect(url_for('admin'))

        except Exception as e:
            flash(f'Ошибка: {str(e)}', 'danger')

    categories = Category.query.all()
    return render_template('edit_product.html', product=product, categories=categories)


@app.route('/admin/product/delete/<int:id>')
@admin_required
def delete_product(id):
    product = db.session.get(Product, id)
    if not product:
        flash('Товар не найден', 'danger')
        return redirect(url_for('admin'))

    name = product.name
    db.session.delete(product)
    db.session.commit()

    flash(f'Товар "{name}" удален', 'success')
    return redirect(url_for('admin'))


# API
@app.route('/api/products')
@login_required
def api_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'quantity': p.quantity,
        'price': p.price,
        'category': p.category.name if p.category else 'Без категории'
    } for p in products])


# Обработчики ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


# Контекстный процессор
@app.context_processor
def inject_user():
    return {
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'is_admin': session.get('is_admin', False),
            'is_authenticated': 'user_id' in session
        }
    }


if __name__ == '__main__':
    # Гарантированно создаем новую БД
    success = create_database()

    if success:
        print("=" * 60)
        print("✅ ПРИЛОЖЕНИЕ ГОТОВО К РАБОТЕ!")
        print("=" * 60)
        print("🌐 Адрес: http://localhost:5000")
        print("👤 Администратор: admin / admin123")
        print("👤 Пользователь: user / user123")
        print("=" * 60)

        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("=" * 60)
        print("❌ НЕ УДАЛОСЬ СОЗДАТЬ БАЗУ ДАННЫХ")
        print("=" * 60)