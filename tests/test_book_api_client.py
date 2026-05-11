import requests
from unittest.mock import patch, MagicMock
from src.clients.book_api_client import search_books, get_book_details, _is_isbn

GOOGLE_BOOK_ITEM = {
    "volumeInfo": {
        "title": "Harry Potter",
        "authors": ["J.K. Rowling"],
        "language": "en",
        "publishedDate": "1997",
        "imageLinks": {"smallThumbnail": "small.jpg", "thumbnail": "medium.jpg"},
        "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9780747562184"}],
    }
}

OPEN_LIBRARY_DOC = {
    "title": "Harry Potter",
    "author_name": ["J.K. Rowling"],
    "isbn": ["9780747562184"],
    "cover_i": 12345,
    "first_publish_year": 1997,
}

OPEN_LIBRARY_BOOK_DATA = {
    "ISBN:9780747562184": {
        "title": "Harry Potter and the Philosopher's Stone",
        "authors": [{"name": "J.K. Rowling"}],
        "publishers": [{"name": "Bloomsbury"}],
        "number_of_pages": 223,
        "publish_date": "1997",
        "cover": {"small": "small.jpg", "medium": "medium.jpg", "large": "large.jpg"},
        "key": "/works/OL82563W",
    }
}

GOOGLE_DESCRIPTION_DATA = {
    "items": [{
        "volumeInfo": {
            "description": "A young wizard's story",
            "categories": ["Fiction"],
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


def test_search_returns_google_results():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response({"items": [GOOGLE_BOOK_ITEM]})
        results = search_books("harry potter")
    assert len(results) == 1
    assert results[0]["title"] == "Harry Potter"
    assert results[0]["isbn"] == "9780747562184"


def test_search_isbn_uses_isbn_prefix():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response({"items": [GOOGLE_BOOK_ITEM]})
        search_books("9780747562184")
    call_params = mock_get.call_args[1]["params"]
    assert call_params["q"] == "isbn:9780747562184"


def test_search_falls_back_to_open_library():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.side_effect = [
            requests.RequestException("Google down"),
            _make_mock_response({"docs": [OPEN_LIBRARY_DOC]}),
        ]
        results = search_books("harry potter")
    assert len(results) == 1
    assert results[0]["isbn"] == "9780747562184"


def test_get_book_details_combines_sources():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.side_effect = [
            _make_mock_response(OPEN_LIBRARY_BOOK_DATA),
            _make_mock_response(GOOGLE_DESCRIPTION_DATA),
        ]
        result = get_book_details("9780747562184")
    assert result["title"] == "Harry Potter and the Philosopher's Stone"
    assert result["description"] == "A young wizard's story"
    assert result["categories"] == ["Fiction"]
    assert result["number_of_pages"] == 223


def test_get_book_details_google_fails_gracefully():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.side_effect = [
            _make_mock_response(OPEN_LIBRARY_BOOK_DATA),
            requests.RequestException("Google down"),
        ]
        result = get_book_details("9780747562184")
    assert result["title"] == "Harry Potter and the Philosopher's Stone"
    assert result["description"] is None
    assert result["categories"] == []


def test_get_book_details_open_library_not_found():
    with patch("src.clients.book_api_client.requests.get") as mock_get:
        mock_get.side_effect = [
            _make_mock_response({}),
            _make_mock_response(GOOGLE_DESCRIPTION_DATA),
        ]
        result = get_book_details("9780000000000")
    assert result["title"] is None
