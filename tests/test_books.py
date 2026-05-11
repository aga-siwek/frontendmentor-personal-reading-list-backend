from unittest.mock import patch

MOCK_BOOK_DETAILS = {
    "title": "Harry Potter and the Philosopher's Stone",
    "author": "J.K. Rowling",
    "cover": {"small": None, "medium": None, "large": None},
    "description": "A young wizard's story",
    "categories": ["Fiction"],
    "number_of_pages": 223,
    "publish_date": "1997",
    "publisher": "Bloomsbury",
    "source_api_id": "/works/OL82563W",
}


# --- Search ---

def test_search_success(client, auth_headers):
    with patch("src.clients.book_api_client.search_books") as mock_search:
        mock_search.return_value = [{"title": "Harry Potter", "isbn": "9780747562184"}]
        response = client.get("/books/search/?q=harry+potter", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_search_no_query(client, auth_headers):
    response = client.get("/books/search/", headers=auth_headers)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_search_no_token(client):
    response = client.get("/books/search/?q=harry+potter")
    assert response.status_code == 401


# --- Book details ---

def test_get_book_from_db(client, auth_headers, sample_book):
    response = client.get(f"/books/{sample_book}/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["isbn"] == sample_book
    assert data["user_book"] is None


def test_get_book_fetches_from_api(client, auth_headers):
    with patch("src.clients.book_api_client.get_book_details") as mock_details:
        mock_details.return_value = MOCK_BOOK_DETAILS
        response = client.get("/books/9780439203531/", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["title"] == MOCK_BOOK_DETAILS["title"]


def test_get_book_not_found(client, auth_headers):
    with patch("src.clients.book_api_client.get_book_details") as mock_details:
        mock_details.return_value = {"title": None}
        response = client.get("/books/9780000000000/", headers=auth_headers)
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_get_book_shows_user_book(client, auth_headers, sample_user_book):
    response = client.get(f"/books/{sample_user_book}/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["user_book"] is not None
    assert data["user_book"]["status"] == "want_to_read"


# --- Add book ---

def test_add_book_success(client, auth_headers, sample_book):
    response = client.post(f"/books/{sample_book}/", json={"status": "want_to_read"}, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()["isbn"] == sample_book


def test_add_book_not_in_db(client, auth_headers):
    response = client.post("/books/9780000000000/", json={"status": "want_to_read"}, headers=auth_headers)
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_add_book_duplicate(client, auth_headers, sample_user_book):
    response = client.post(f"/books/{sample_user_book}/", json={"status": "want_to_read"}, headers=auth_headers)
    assert response.status_code == 409
    assert "error" in response.get_json()


def test_add_book_invalid_status(client, auth_headers, sample_book):
    response = client.post(f"/books/{sample_book}/", json={"status": "invalid"}, headers=auth_headers)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_add_book_finished_sets_last_updated(client, auth_headers, sample_book):
    response = client.post(f"/books/{sample_book}/", json={"status": "finished"}, headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 201
    assert data["last_updated"] is not None


def test_add_book_finished_sets_current_page(client, auth_headers, sample_book):
    response = client.post(f"/books/{sample_book}/", json={"status": "finished"}, headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 201
    assert data["current_page"] == 223


# --- Update book ---

def test_update_status_to_finished(client, auth_headers, sample_user_book):
    response = client.patch(f"/books/{sample_user_book}/", json={"status": "finished"}, headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["status"] == "finished"
    assert data["current_page"] == 223
    assert data["last_updated"] is not None


def test_update_invalid_status(client, auth_headers, sample_user_book):
    response = client.patch(f"/books/{sample_user_book}/", json={"status": "invalid"}, headers=auth_headers)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_update_current_page_capped(client, auth_headers, sample_user_book):
    response = client.patch(f"/books/{sample_user_book}/", json={"current_page": 9999}, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["current_page"] == 223


def test_update_book_not_on_list(client, auth_headers, sample_book):
    response = client.patch(f"/books/{sample_book}/", json={"status": "finished"}, headers=auth_headers)
    assert response.status_code == 404
    assert "error" in response.get_json()


# --- Reading progress ---

def test_add_progress_success(client, auth_headers, sample_user_book):
    response = client.post(f"/books/{sample_user_book}/progress/", json={"current_page": 50}, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()["current_page"] == 50


def test_add_progress_caps_at_total(client, auth_headers, sample_user_book):
    response = client.post(f"/books/{sample_user_book}/progress/", json={"current_page": 9999}, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()["current_page"] == 223


def test_add_progress_sets_finished(client, auth_headers, sample_user_book):
    client.post(f"/books/{sample_user_book}/progress/", json={"current_page": 223}, headers=auth_headers)
    response = client.get(f"/books/{sample_user_book}/", headers=auth_headers)
    assert response.get_json()["user_book"]["status"] == "finished"


def test_add_progress_sets_reading(client, auth_headers, sample_user_book):
    client.post(f"/books/{sample_user_book}/progress/", json={"current_page": 10}, headers=auth_headers)
    response = client.get(f"/books/{sample_user_book}/", headers=auth_headers)
    assert response.get_json()["user_book"]["status"] == "currently_reading"


def test_add_progress_book_not_on_list(client, auth_headers, sample_book):
    response = client.post(f"/books/{sample_book}/progress/", json={"current_page": 10}, headers=auth_headers)
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_get_progress_success(client, auth_headers, sample_user_book):
    client.post(f"/books/{sample_user_book}/progress/", json={"current_page": 50}, headers=auth_headers)
    client.post(f"/books/{sample_user_book}/progress/", json={"current_page": 100}, headers=auth_headers)
    response = client.get(f"/books/{sample_user_book}/progress/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["current_page"] == 50
    assert data[1]["current_page"] == 100


def test_get_progress_book_not_on_list(client, auth_headers, sample_book):
    response = client.get(f"/books/{sample_book}/progress/", headers=auth_headers)
    assert response.status_code == 404
    assert "error" in response.get_json()


# --- Me books ---

def test_get_me_books_empty(client, auth_headers):
    response = client.get("/books/me/", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_me_books(client, auth_headers, sample_user_book):
    response = client.get("/books/me/", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 1
    assert "user_book" in data[0]
