import pytest
from main import create_app
from src.database import db as _db
from src.models.user import User
from src.bcrypt import bcrypt as _bcrypt


TEST_CONFIG = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "test-secret",
    "SECRET_KEY": "test-secret",
}

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="session")
def app():
    app = create_app(TEST_CONFIG)
    yield app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        _db.drop_all()
        _db.create_all()
    yield


@pytest.fixture
def registered_user(client):
    client.post("/users/register/", json={
        "user_email": TEST_EMAIL,
        "user_password": TEST_PASSWORD,
    })
    return {"user_email": TEST_EMAIL, "user_password": TEST_PASSWORD}


@pytest.fixture
def auth_headers(client, registered_user):
    response = client.post("/users/login/", json=registered_user)
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, app):
    with app.app_context():
        admin = User(
            user_email="admin@example.com",
            user_password=_bcrypt.generate_password_hash("adminpass").decode(),
            is_admin=True,
        )
        _db.session.add(admin)
        _db.session.commit()
    response = client.post("/users/login/", json={
        "user_email": "admin@example.com",
        "user_password": "adminpass",
    })
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
