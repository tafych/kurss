# test_app.py
import pytest
import tempfile
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from app.py
from app import app, db, User, Category, Product


class TestConfig:
    """Test configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'


@pytest.fixture
def test_app():
    """Create test application"""
    # Save original configuration
    original_config = app.config.copy()

    # Configure app for tests
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    # Create all tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    # Restore original configuration
    app.config.clear()
    app.config.update(original_config)


@pytest.fixture
def client(test_app):
    """Test client"""
    return test_app.test_client()


@pytest.fixture
def init_database(test_app):
    """Initialize test database"""
    with test_app.app_context():
        # Clear all tables
        db.session.query(User).delete()
        db.session.query(Category).delete()
        db.session.query(Product).delete()
        db.session.commit()

        # Create test data
        # Users
        admin_user = User(
            username='admin_test',
            email='admin_test@example.com',
            password_hash='hashed_password_admin',
            is_admin=True
        )

        regular_user = User(
            username='user_test',
            email='user_test@example.com',
            password_hash='hashed_password_user',
            is_admin=False
        )

        # Categories
        category1 = Category(
            name='Electronics_test',
            description='Test electronics category'
        )

        category2 = Category(
            name='Books_test',
            description='Test books category'
        )

        # Products
        product1 = Product(
            name='Laptop_test',
            description='Test laptop',
            detailed_specs='Test specifications',
            sku='TEST001',
            quantity=5,
            price=50000.0,
            category=category1,
            views_count=0
        )

        product2 = Product(
            name='Book_test',
            description='Test book',
            detailed_specs='Test description',
            sku='TEST002',
            quantity=10,
            price=1500.0,
            category=category2,
            views_count=0
        )

        db.session.add_all([admin_user, regular_user, category1, category2, product1, product2])
        db.session.commit()

        yield db


class TestBasicRoutes:
    """Tests for basic routes"""

    def test_home_page(self, client):
        """Test home page"""
        response = client.get('/')
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'

    def test_login_page_get(self, client):
        """Test login page (GET request)"""
        response = client.get('/login')
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'

    def test_register_page_get(self, client):
        """Test register page (GET request)"""
        response = client.get('/register')
        assert response.status_code == 200
        assert response.content_type == 'text/html; charset=utf-8'


class TestAuthentication:
    """Authentication tests"""

    def test_user_registration(self, client, test_app):
        """Test new user registration"""
        with test_app.app_context():
            # Check that user doesn't exist yet
            existing_user = User.query.filter_by(username='new_test_user').first()
            assert existing_user is None

            # Register new user
            response = client.post('/register', data={
                'username': 'new_test_user',
                'email': 'new_test@example.com',
                'password': 'TestPassword123'
            }, follow_redirects=True)

            assert response.status_code == 200

            # Check that user was created
            new_user = User.query.filter_by(username='new_test_user').first()
            assert new_user is not None
            assert new_user.email == 'new_test@example.com'
            assert new_user.is_admin is False

    def test_duplicate_username_registration(self, client, test_app, init_database):
        """Test registration with existing username"""
        with test_app.app_context():
            response = client.post('/register', data={
                'username': 'admin_test',  # Already exists
                'email': 'new_email@example.com',
                'password': 'password123'
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_login_success(self, client, test_app, init_database):
        """Test successful login"""
        with test_app.app_context():
            # Create user with real password
            from werkzeug.security import generate_password_hash
            test_user = User(
                username='login_test_user',
                email='login_test@example.com',
                password_hash=generate_password_hash('testpassword'),
                is_admin=False
            )
            db.session.add(test_user)
            db.session.commit()

            # Try to login
            response = client.post('/login', data={
                'username': 'login_test_user',
                'password': 'testpassword'
            }, follow_redirects=True)

            assert response.status_code == 200
            # Check that redirect to /search happened
            assert response.request.path == '/search'

    def test_login_failure(self, client):
        """Test failed login"""
        response = client.post('/login', data={
            'username': 'nonexistent_user',
            'password': 'wrongpassword'
        })

        assert response.status_code == 200

    def test_logout(self, client, test_app):
        """Test logout"""
        with test_app.app_context():
            # First login
            with client.session_transaction() as session:
                session['user_id'] = 1
                session['username'] = 'testuser'
                session['is_admin'] = False

            # Check that session is set
            with client.session_transaction() as session:
                assert 'user_id' in session

            # Logout
            response = client.get('/logout', follow_redirects=True)
            assert response.status_code == 200

            # Check that session is cleared
            with client.session_transaction() as session:
                assert 'user_id' not in session


class TestSearchFunctionality:
    """Search functionality tests"""

    def test_search_page_requires_login(self, client):
        """Test that search page requires authentication"""
        response = client.get('/search', follow_redirects=True)
        assert response.status_code == 200

    def test_search_with_authenticated_user(self, client, test_app, init_database):
        """Test search with authenticated user"""
        with test_app.app_context():
            # Login
            with client.session_transaction() as session:
                session['user_id'] = 2  # regular_user
                session['username'] = 'user_test'
                session['is_admin'] = False

            response = client.get('/search')
            assert response.status_code == 200

            # Search specific product
            response = client.get('/search?q=laptop')
            assert response.status_code == 200

    def test_product_detail_page(self, client, test_app, init_database):
        """Test product detail page"""
        with test_app.app_context():
            # Login
            with client.session_transaction() as session:
                session['user_id'] = 2
                session['username'] = 'user_test'
                session['is_admin'] = False

            # Get first product
            product = Product.query.first()
            assert product is not None

            # View product page
            initial_views = product.views_count
            response = client.get(f'/product/{product.id}')
            assert response.status_code == 200

            # Check that view counter increased
            db.session.refresh(product)
            assert product.views_count == initial_views + 1


class TestAdminFunctionality:
    """Admin functionality tests"""

    def test_admin_page_requires_admin(self, client, test_app, init_database):
        """Test that admin page requires admin rights"""
        with test_app.app_context():
            # Login as regular user
            with client.session_transaction() as session:
                session['user_id'] = 2  # regular_user (not admin)
                session['username'] = 'user_test'
                session['is_admin'] = False

            response = client.get('/admin', follow_redirects=True)
            assert response.status_code == 200

    def test_admin_page_access_granted(self, client, test_app, init_database):
        """Test admin page access with admin rights"""
        with test_app.app_context():
            # Login as admin
            with client.session_transaction() as session:
                session['user_id'] = 1  # admin_user
                session['username'] = 'admin_test'
                session['is_admin'] = True

            response = client.get('/admin')
            assert response.status_code == 200

    def test_add_product_page(self, client, test_app, init_database):
        """Test add product page"""
        with test_app.app_context():
            # Login as admin
            with client.session_transaction() as session:
                session['user_id'] = 1
                session['username'] = 'admin_test'
                session['is_admin'] = True

            response = client.get('/admin/product/add')
            assert response.status_code == 200

    def test_add_new_product(self, client, test_app, init_database):
        """Test adding new product"""
        with test_app.app_context():
            # Login as admin
            with client.session_transaction() as session:
                session['user_id'] = 1
                session['username'] = 'admin_test'
                session['is_admin'] = True

            # Add new product
            response = client.post('/admin/product/add', data={
                'name': 'New test product',
                'description': 'Test product description',
                'detailed_specs': 'Product specifications',
                'sku': 'UNIQUE_SKU_001',
                'quantity': 100,
                'price': 9999.99,
                'category_id': 1
            }, follow_redirects=True)

            assert response.status_code == 200

            # Check that product was created
            product = Product.query.filter_by(sku='UNIQUE_SKU_001').first()
            assert product is not None
            assert product.name == 'New test product'
            assert product.quantity == 100

    def test_edit_product(self, client, test_app, init_database):
        """Test product editing"""
        with test_app.app_context():
            # Login as admin
            with client.session_transaction() as session:
                session['user_id'] = 1
                session['username'] = 'admin_test'
                session['is_admin'] = True

            # Get existing product
            product = Product.query.first()
            original_name = product.name

            # Edit product
            response = client.post(f'/admin/product/edit/{product.id}', data={
                'name': 'Modified product name',
                'description': product.description,
                'detailed_specs': product.detailed_specs,
                'sku': product.sku,
                'quantity': product.quantity + 10,
                'price': product.price,
                'category_id': product.category_id
            }, follow_redirects=True)

            assert response.status_code == 200

            # Check changes
            db.session.refresh(product)
            assert product.name == 'Modified product name'
            assert product.quantity == 15  # Was 5, now 15

    def test_delete_product(self, client, test_app, init_database):
        """Test product deletion"""
        with test_app.app_context():
            # Login as admin
            with client.session_transaction() as session:
                session['user_id'] = 1
                session['username'] = 'admin_test'
                session['is_admin'] = True

            # Create product for deletion
            product = Product(
                name='Product to delete',
                description='Description',
                sku='DELETE_ME',
                quantity=1,
                price=100.0,
                category_id=1
            )
            db.session.add(product)
            db.session.commit()

            product_id = product.id

            # Delete product
            response = client.get(f'/admin/product/delete/{product_id}', follow_redirects=True)
            assert response.status_code == 200

            # Check that product was deleted
            deleted_product = Product.query.get(product_id)
            assert deleted_product is None


class TestAPIEndpoints:
    """API endpoints tests"""

    def test_api_products_requires_login(self, client):
        """Test that API requires authentication"""
        response = client.get('/api/products')
        assert response.status_code in [401, 403, 302]

    def test_api_products_authenticated(self, client, test_app, init_database):
        """Test API products with authenticated user"""
        with test_app.app_context():
            # Login
            with client.session_transaction() as session:
                session['user_id'] = 2
                session['username'] = 'user_test'
                session['is_admin'] = False

            response = client.get('/api/products')
            assert response.status_code == 200
            assert response.content_type == 'application/json'

            data = json.loads(response.get_data(as_text=True))
            assert isinstance(data, list)
            assert len(data) > 0
            assert 'name' in data[0]
            assert 'sku' in data[0]


class TestErrorHandling:
    """Error handling tests"""

    def test_404_error(self, client):
        """Test 404 error"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404

    def test_product_not_found(self, client, test_app):
        """Test non-existent product"""
        with test_app.app_context():
            # Login
            with client.session_transaction() as session:
                session['user_id'] = 1
                session['username'] = 'test'
                session['is_admin'] = False

            response = client.get('/product/999999', follow_redirects=True)
            assert response.status_code == 200


class TestSessionManagement:
    """Session management tests"""

    def test_session_creation_on_login(self, client, test_app, init_database):
        """Test that session is created on login"""
        with test_app.app_context():
            # Create test user
            from werkzeug.security import generate_password_hash
            test_user = User(
                username='session_test',
                email='session@example.com',
                password_hash=generate_password_hash('sessionpass'),
                is_admin=False
            )
            db.session.add(test_user)
            db.session.commit()

            # Login
            response = client.post('/login', data={
                'username': 'session_test',
                'password': 'sessionpass'
            }, follow_redirects=True)

            assert response.status_code == 200

            # Check session data
            with client.session_transaction() as session:
                assert 'user_id' in session
                assert 'username' in session
                assert session['username'] == 'session_test'
                assert 'is_admin' in session
                assert session['is_admin'] is False

    def test_session_clear_on_logout(self, client, test_app):
        """Test that session is cleared on logout"""
        with test_app.app_context():
            # Set session data
            with client.session_transaction() as session:
                session['user_id'] = 123
                session['username'] = 'testuser'
                session['is_admin'] = True

            # Logout
            response = client.get('/logout', follow_redirects=True)
            assert response.status_code == 200

            # Verify session is cleared
            with client.session_transaction() as session:
                assert 'user_id' not in session
                assert 'username' not in session
                assert 'is_admin' not in session


class TestDatabaseModels:
    """Database models tests"""

    def test_user_model(self, test_app):
        """Test User model"""
        with test_app.app_context():
            user = User(
                username='model_test',
                email='model@example.com',
                password_hash='test_hash',
                is_admin=True
            )
            db.session.add(user)
            db.session.commit()

            retrieved_user = User.query.filter_by(username='model_test').first()
            assert retrieved_user is not None
            assert retrieved_user.email == 'model@example.com'
            assert retrieved_user.is_admin is True

    def test_category_model(self, test_app):
        """Test Category model"""
        with test_app.app_context():
            category = Category(
                name='Test Category',
                description='Test Description'
            )
            db.session.add(category)
            db.session.commit()

            retrieved_category = Category.query.filter_by(name='Test Category').first()
            assert retrieved_category is not None
            assert retrieved_category.description == 'Test Description'

    def test_product_model(self, test_app):
        """Test Product model"""
        with test_app.app_context():
            # First create a category
            category = Category(name='Model Test Category')
            db.session.add(category)
            db.session.commit()

            product = Product(
                name='Model Test Product',
                description='Model Test Description',
                sku='MODEL_TEST_001',
                quantity=50,
                price=1000.0,
                category_id=category.id
            )
            db.session.add(product)
            db.session.commit()

            retrieved_product = Product.query.filter_by(sku='MODEL_TEST_001').first()
            assert retrieved_product is not None
            assert retrieved_product.name == 'Model Test Product'
            assert retrieved_product.quantity == 50
            assert retrieved_product.price == 1000.0
            assert retrieved_product.category_id == category.id


if __name__ == '__main__':
    # Run tests
    pytest.main(['-v', '--tb=short', 'test_app.py'])