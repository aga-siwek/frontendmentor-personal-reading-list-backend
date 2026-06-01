import requests
from unittest.mock import patch, MagicMock
from src.clients.book_api_client import search_books, get_book_details, _is_isbn

GOOGLE_BOOK_ITEM = {
    "volumeInfo": {
        "title": "Harry Potter",
        "authors": ["J.K. Rowling"],
        "language": "en",
        "publishedDate": "1997",
        "pageCount": 223,
        "imageLinks": {"smallThumbnail": "http://books.google.com/small.jpg", "thumbnail": "http://books.google.com/medium.jpg"},
        "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9780747562184"}],
    }
}

GOOGLE_BOOK_DETAILS = {
    "items": [{
        "volumeInfo": {
            "title": "Harry Potter and the Philosopher's Stone",
            "authors": ["J.K. Rowling"],
            "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9780747562184"}],
            "imageLinks": {"smallThumbnail": "small.jpg", "thumbnail": "medium.jpg"},
            "description": "A young wizard's story",
            "categories": ["Fiction"],
            "pageCount": 223,
            "publishedDate": "1997-06-26",
            "publisher": "Bloomsbury",
        }
    }]
}


def _make_mock_response(json_data):
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.raise_for_status.return_value = None
    return mock


def test_is_isbn_13_digits():
    assert _is_isbn("9780747562184") == True


def test_is_isbn_10_digits():
    assert _is_isbn("0747562180") == True


def test_is_isbn_with_dashes():
    assert _is_isbn("978-0747562184") == True


def test_is_isbn_text():
    assert _is_isbn("harry potter") == False


def test_is_isbn_wrong_length():
    assert _is_isbn("12345") == False


def test_search_returns_results():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response({"items": [GOOGLE_BOOK_ITEM]})
        results = search_books("harry potter")
    assert len(results) == 1
    assert results[0]["title"] == "Harry Potter"
    assert results[0]["isbn"] == "9780747562184"
    assert results[0]["author"] == "J.K. Rowling"
    assert results[0]["first_publish_year"] == 1997
    assert results[0]["cover"]["medium"] == "https://books.google.com/medium.jpg"


def test_search_prefers_results_with_cover_and_pages():
    item_no_cover = {
        "volumeInfo": {
            "title": "Harry Potter (old edition)",
            "authors": ["J.K. Rowling"],
            "publishedDate": "2020",
            "pageCount": 0,
            "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9780000000001"}],
        }
    }
    item_with_cover = {
        "volumeInfo": {
            "title": "Harry Potter (new edition)",
            "authors": ["J.K. Rowling"],
            "publishedDate": "2010",
            "pageCount": 223,
            "imageLinks": {"thumbnail": "http://books.google.com/cover.jpg"},
            "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9780000000002"}],
        }
    }
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response({"items": [item_no_cover, item_with_cover]})
        results = search_books("harry potter")
    assert results[0]["isbn"] == "9780000000002"


def test_search_isbn_uses_isbn_prefix():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response({"items": [GOOGLE_BOOK_ITEM]})
        search_books("9780747562184")
    call_params = mock_get.call_args[1]["params"]
    assert call_params["q"] == "isbn:9780747562184"


def test_search_returns_empty_on_api_error():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Google down")
        results = search_books("harry potter")
    assert results == []


def test_search_includes_non_english_results():
    non_english_item = {
        "volumeInfo": {
            "title": "Harry Potter i Kamień Filozoficzny",
            "authors": ["J.K. Rowling"],
            "language": "pl",
            "publishedDate": "2000",
            "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9788380082625"}],
        }
    }
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response({"items": [non_english_item]})
        results = search_books("harry potter")
    assert len(results) == 1
    assert results[0]["isbn"] == "9788380082625"


def test_get_book_details_returns_full_data():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response(GOOGLE_BOOK_DETAILS)
        result = get_book_details("9780747562184")
    assert result["title"] == "Harry Potter and the Philosopher's Stone"
    assert result["author"] == "J.K. Rowling"
    assert result["description"] == "A young wizard's story"
    assert result["categories"] == ["Fiction"]
    assert result["number_of_pages"] == 223
    assert result["publisher"] == "Bloomsbury"
    assert result["isbn"] == "9780747562184"


def test_get_book_details_not_found():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response({"items": []})
        result = get_book_details("9780000000000")
    assert result == {}


def test_get_book_details_returns_empty_on_api_error():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Google down")
        result = get_book_details("9780747562184")
    assert result == {}
