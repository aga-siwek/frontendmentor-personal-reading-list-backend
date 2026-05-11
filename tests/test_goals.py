def test_get_goals_empty(client, auth_headers):
    response = client.get("/goals/me/", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_goal(client, auth_headers):
    response = client.post("/goals/me/", json={"year": 2026, "goal": 24}, headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 201
    assert data["year"] == 2026
    assert data["goal"] == 24
    assert "books_finished" in data


def test_create_goal_no_token(client):
    response = client.post("/goals/me/", json={"year": 2026, "goal": 24})
    assert response.status_code == 401


def test_create_duplicate_goal(client, auth_headers):
    client.post("/goals/me/", json={"year": 2026, "goal": 24}, headers=auth_headers)
    response = client.post("/goals/me/", json={"year": 2026, "goal": 12}, headers=auth_headers)
    assert response.status_code == 409
    assert "error" in response.get_json()


def test_get_goal_by_year(client, auth_headers):
    client.post("/goals/me/", json={"year": 2026, "goal": 24}, headers=auth_headers)
    response = client.get("/goals/me/2026/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["year"] == 2026
    assert data["goal"] == 24


def test_get_goal_not_found(client, auth_headers):
    response = client.get("/goals/me/2099/", headers=auth_headers)
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_update_goal(client, auth_headers):
    client.post("/goals/me/", json={"year": 2026, "goal": 24}, headers=auth_headers)
    response = client.patch("/goals/me/2026/", json={"goal": 30}, headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["goal"] == 30


def test_delete_goal(client, auth_headers):
    client.post("/goals/me/", json={"year": 2026, "goal": 24}, headers=auth_headers)
    response = client.delete("/goals/me/2026/", headers=auth_headers)
    assert response.status_code == 200
    assert client.get("/goals/me/2026/", headers=auth_headers).status_code == 404


def test_books_finished_counts_correctly(client, auth_headers, sample_user_book):
    client.post("/goals/me/", json={"year": 2026, "goal": 24}, headers=auth_headers)
    client.patch(f"/books/{sample_user_book}/", json={"status": "finished"}, headers=auth_headers)
    response = client.get("/goals/me/2026/", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["books_finished"] == 1
