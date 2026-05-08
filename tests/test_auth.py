from tests.conftest import TEST_EMAIL, TEST_PASSWORD


def test_register_success(client):
    response = client.post("/users/register/", json={
        "user_email": TEST_EMAIL,
        "user_password": TEST_PASSWORD,
    })
    data = response.get_json()
    assert response.status_code == 201
    assert data["user_email"] == TEST_EMAIL
    assert data["is_admin"] == False
    assert "user_id" in data
    assert "user_password" not in data


def test_register_duplicate_email(client):
    client.post("/users/register/", json={
        "user_email": TEST_EMAIL,
        "user_password": TEST_PASSWORD,
    })
    response = client.post("/users/register/", json={
        "user_email": TEST_EMAIL,
        "user_password": TEST_PASSWORD,
    })
    assert response.status_code == 409
    assert "error" in response.get_json()


def test_login_success(client, registered_user):
    response = client.post("/users/login/", json=registered_user)
    data = response.get_json()
    assert response.status_code == 200
    assert "access_token" in data
    assert data["user_email"] == TEST_EMAIL
    assert data["message"] == "Login Success"


def test_login_wrong_password(client, registered_user):
    response = client.post("/users/login/", json={
        "user_email": TEST_EMAIL,
        "user_password": "wrongpassword",
    })
    assert response.status_code == 401
    assert response.get_json()["error"] == "Access Denied: bad login or password"
