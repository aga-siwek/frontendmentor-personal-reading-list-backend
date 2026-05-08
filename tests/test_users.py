from tests.conftest import TEST_EMAIL


def test_get_me_success(client, auth_headers):
    response = client.get("/users/me/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["user_email"] == TEST_EMAIL
    assert data["is_admin"] == False
    assert "user_id" in data
    assert "user_name" in data
    assert "user_password" not in data


def test_get_me_no_token(client):
    response = client.get("/users/me/")
    assert response.status_code == 401


def test_get_all_users_as_admin(client, admin_headers):
    response = client.get("/users/", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_all_users_as_regular_user(client, auth_headers):
    response = client.get("/users/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 401
    assert "error" in data


def test_get_single_user_as_admin(client, admin_headers):
    register_response = client.post("/users/register/", json={
        "user_email": "another@example.com",
        "user_password": "password123",
    })
    user_id = register_response.get_json()["user_id"]

    response = client.get(f"/users/{user_id}/", headers=admin_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["user_email"] == "another@example.com"
    assert "user_password" not in data


def test_get_single_user_as_regular_user(client, auth_headers):
    response = client.get("/users/1/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 401
    assert "error" in data


def test_get_single_user_not_found(client, admin_headers):
    response = client.get("/users/9999/", headers=admin_headers)
    data = response.get_json()
    assert response.status_code == 404
    assert "error" in data
