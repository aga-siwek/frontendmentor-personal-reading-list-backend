def test_get_shelves_empty(client, auth_headers):
    response = client.get("/shelves/me/", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_shelves(client, auth_headers, sample_shelf):
    response = client.get("/shelves/me/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["name"] == "My Shelf"


def test_create_shelf(client, auth_headers):
    response = client.post("/shelves/me/", json={"name": "To Read"}, headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 201
    assert data["name"] == "To Read"
    assert "id" in data


def test_create_shelf_no_name(client, auth_headers):
    response = client.post("/shelves/me/", json={}, headers=auth_headers)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_shelf_no_token(client):
    response = client.post("/shelves/me/", json={"name": "To Read"})
    assert response.status_code == 401


def test_get_shelf_by_id(client, auth_headers, sample_shelf):
    response = client.get(f"/shelves/{sample_shelf}/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["id"] == sample_shelf
    assert "books" in data


def test_get_shelf_not_found(client, auth_headers):
    response = client.get("/shelves/9999/", headers=auth_headers)
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_update_shelf_name(client, auth_headers, sample_shelf):
    response = client.patch(f"/shelves/{sample_shelf}/", json={"name": "Updated"}, headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["name"] == "Updated"


def test_set_default_shelf_clears_previous(client, auth_headers):
    r1 = client.post("/shelves/me/", json={"name": "Shelf A", "is_default": True}, headers=auth_headers)
    shelf1_id = r1.get_json()["id"]
    client.post("/shelves/me/", json={"name": "Shelf B", "is_default": True}, headers=auth_headers)

    response = client.get("/shelves/me/", headers=auth_headers)
    shelves = response.get_json()
    default_shelves = [s for s in shelves if s["is_default"]]
    assert len(default_shelves) == 1
    assert default_shelves[0]["id"] != shelf1_id


def test_delete_shelf(client, auth_headers, sample_shelf):
    response = client.delete(f"/shelves/{sample_shelf}/", headers=auth_headers)
    assert response.status_code == 200
    assert client.get(f"/shelves/{sample_shelf}/", headers=auth_headers).status_code == 404


def test_delete_default_shelf(client, auth_headers):
    response = client.post("/shelves/me/", json={"name": "Default", "is_default": True}, headers=auth_headers)
    shelf_id = response.get_json()["id"]
    response = client.delete(f"/shelves/{shelf_id}/", headers=auth_headers)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_add_book_to_shelf(client, auth_headers, sample_shelf, sample_book):
    response = client.post(f"/shelves/{sample_shelf}/books/{sample_book}/", headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()["isbn"] == sample_book


def test_add_book_to_shelf_duplicate(client, auth_headers, sample_shelf, sample_book):
    client.post(f"/shelves/{sample_shelf}/books/{sample_book}/", headers=auth_headers)
    response = client.post(f"/shelves/{sample_shelf}/books/{sample_book}/", headers=auth_headers)
    assert response.status_code == 409
    assert "error" in response.get_json()


def test_add_book_not_in_db_to_shelf(client, auth_headers, sample_shelf):
    response = client.post(f"/shelves/{sample_shelf}/books/9780000000000/", headers=auth_headers)
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_remove_book_from_shelf(client, auth_headers, sample_shelf, sample_book):
    client.post(f"/shelves/{sample_shelf}/books/{sample_book}/", headers=auth_headers)
    response = client.delete(f"/shelves/{sample_shelf}/books/{sample_book}/", headers=auth_headers)
    assert response.status_code == 200


def test_remove_book_not_on_shelf(client, auth_headers, sample_shelf, sample_book):
    response = client.delete(f"/shelves/{sample_shelf}/books/{sample_book}/", headers=auth_headers)
    assert response.status_code == 404
    assert "error" in response.get_json()
