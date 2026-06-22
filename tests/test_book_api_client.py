import requests
from unittest.mock import patch, MagicMock
from src.clients import book_api_client
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

OPEN_LIBRARY_DOC = {
    "title": "Harry Potter",
    "author_name": ["J.K. Rowling"],
    "isbn": ["9780747562184"],
    "cover_i": 12345,
    "first_publish_year": 1997,
}

OPEN_LIBRARY_PAGE_COUNT_DATA = {
    "ISBN:9780747562184": {"number_of_pages": 223},
}

OPEN_LIBRARY_BOOK_DATA = {
    "ISBN:9780747562184": {
        "title": "Harry Potter and the Philosopher's Stone",
        "authors": [{"name": "J.K. Rowling"}],
        "publishers": [{"name": "Bloomsbury"}],
        "number_of_pages": 223,
        "publish_date": "1997",
        "cover": {"small": "https://covers.openlibrary.org/b/id/123-S.jpg", "medium": "https://covers.openlibrary.org/b/id/123-M.jpg", "large": "https://covers.openlibrary.org/b/id/123-L.jpg"},
        "key": "/works/OL82563W",
    }
}

GOOGLE_DESCRIPTION_DATA = {
    "items": [{
        "volumeInfo": {
            "title": "Harry Potter and the Philosopher's Stone",
            "authors": ["J.K. Rowling"],
            "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9780747562184"}],
            "imageLinks": {"thumbnail": "http://books.google.com/cover.jpg"},
            "description": "A young wizard's story",
            "categories": ["Fiction"],
            "pageCount": 223,
            "publishedDate": "1997",
            "publisher": "Bloomsbury",
        }
    }]
}


def _make_mock_response(json_data):
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.raise_for_status.return_value = None
    return mock


def _fake_get_by_url(by_url):
    """SESSION.get replacement that answers based on the request URL.

    Search now makes a batched Open Library call plus parallel Google Books
    calls, so the call order isn't guaranteed - routing by URL instead of by
    call order keeps the tests correct regardless of execution order.
    """
    def fake_get(url, params=None, headers=None, timeout=None):
        if url not in by_url:
            raise AssertionError(f"Unexpected request to {url} with params {params}")
        response = by_url[url]
        if isinstance(response, Exception):
            raise response
        return response
    return fake_get


def setup_function(_):
    book_api_client._search_cache.clear()


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


def test_search_returns_open_library_results():
    by_url = {
        book_api_client.OPEN_LIBRARY_SEARCH_URL: _make_mock_response({"docs": [OPEN_LIBRARY_DOC]}),
        book_api_client.OPEN_LIBRARY_BOOKS_URL: _make_mock_response(OPEN_LIBRARY_PAGE_COUNT_DATA),
        book_api_client.GOOGLE_BOOKS_URL: _make_mock_response({"items": [GOOGLE_BOOK_ITEM]}),
    }
    with patch.object(book_api_client.SESSION, "get", side_effect=_fake_get_by_url(by_url)):
        results = search_books("harry potter")
    assert len(results) == 1
    assert results[0]["title"] == "Harry Potter"
    assert results[0]["isbn"] == "9780747562184"


def test_search_cover_url_uses_https():
    by_url = {
        book_api_client.OPEN_LIBRARY_SEARCH_URL: _make_mock_response({"docs": [OPEN_LIBRARY_DOC]}),
        book_api_client.OPEN_LIBRARY_BOOKS_URL: _make_mock_response(OPEN_LIBRARY_PAGE_COUNT_DATA),
        book_api_client.GOOGLE_BOOKS_URL: _make_mock_response({"items": [GOOGLE_BOOK_ITEM]}),
    }
    with patch.object(book_api_client.SESSION, "get", side_effect=_fake_get_by_url(by_url)):
        results = search_books("harry potter")
    assert results[0]["cover"]["medium"].startswith("https://")


def test_search_skips_editions_without_page_count():
    # No edition has a page count, so Open Library yields no candidates and
    # search falls back to Google Books - which also returns nothing here.
    by_url = {
        book_api_client.OPEN_LIBRARY_SEARCH_URL: _make_mock_response({"docs": [OPEN_LIBRARY_DOC]}),
        book_api_client.OPEN_LIBRARY_BOOKS_URL: _make_mock_response({"ISBN:9780747562184": {"number_of_pages": 0}}),
        book_api_client.GOOGLE_BOOKS_URL: _make_mock_response({"items": []}),
    }
    with patch.object(book_api_client.SESSION, "get", side_effect=_fake_get_by_url(by_url)):
        results = search_books("harry potter")
    assert results == []


def test_search_falls_back_to_google_books():
    with patch.object(book_api_client.SESSION, "get") as mock_get:
        mock_get.side_effect = [
            requests.RequestException("OL down"),
            _make_mock_response({"items": [GOOGLE_BOOK_ITEM]}),
        ]
        results = search_books("harry potter")
    assert len(results) == 1
    assert results[0]["isbn"] == "9780747562184"


def test_search_isbn_query_uses_isbn_prefix():
    by_url = {
        book_api_client.GOOGLE_BOOKS_URL: _make_mock_response(GOOGLE_DESCRIPTION_DATA),
        book_api_client.OPEN_LIBRARY_BOOKS_URL: _make_mock_response(OPEN_LIBRARY_BOOK_DATA),
    }
    with patch.object(book_api_client.SESSION, "get", side_effect=_fake_get_by_url(by_url)) as mock_get:
        search_books("9780747562184")
    google_calls = [c for c in mock_get.call_args_list if c.args[0] == book_api_client.GOOGLE_BOOKS_URL]
    assert google_calls[0].kwargs["params"]["q"] == "isbn:9780747562184"


def test_get_book_details_combines_sources():
    by_url = {
        book_api_client.GOOGLE_BOOKS_URL: _make_mock_response(GOOGLE_DESCRIPTION_DATA),
        book_api_client.OPEN_LIBRARY_BOOKS_URL: _make_mock_response(OPEN_LIBRARY_BOOK_DATA),
    }
    with patch.object(book_api_client.SESSION, "get", side_effect=_fake_get_by_url(by_url)):
        result = get_book_details("9780747562184")
    assert result["title"] == "Harry Potter and the Philosopher's Stone"  # from OL
    assert result["description"] == "A young wizard's story"              # from Google
    assert result["categories"] == ["Fiction"]                            # from Google
    assert result["number_of_pages"] == 223                               # from OL
    assert result["publisher"] == "Bloomsbury"                            # from OL


def test_get_book_details_cover_uses_https():
    by_url = {
        book_api_client.GOOGLE_BOOKS_URL: _make_mock_response(GOOGLE_DESCRIPTION_DATA),
        book_api_client.OPEN_LIBRARY_BOOKS_URL: _make_mock_response(OPEN_LIBRARY_BOOK_DATA),
    }
    with patch.object(book_api_client.SESSION, "get", side_effect=_fake_get_by_url(by_url)):
        result = get_book_details("9780747562184")
    assert result["cover"]["medium"].startswith("https://")


def test_get_book_details_google_fails_gracefully():
    by_url = {
        book_api_client.GOOGLE_BOOKS_URL: requests.RequestException("Google down"),
        book_api_client.OPEN_LIBRARY_BOOKS_URL: _make_mock_response(OPEN_LIBRARY_BOOK_DATA),
    }
    with patch.object(book_api_client.SESSION, "get", side_effect=_fake_get_by_url(by_url)):
        result = get_book_details("9780747562184")
    assert result["title"] == "Harry Potter and the Philosopher's Stone"
    assert result["description"] is None
    assert result["categories"] == []


def test_get_book_details_open_library_not_found():
    by_url = {
        book_api_client.GOOGLE_BOOKS_URL: _make_mock_response(GOOGLE_DESCRIPTION_DATA),
        book_api_client.OPEN_LIBRARY_BOOKS_URL: _make_mock_response({}),
    }
    with patch.object(book_api_client.SESSION, "get", side_effect=_fake_get_by_url(by_url)):
        result = get_book_details("9780000000000")
    assert result["title"] == "Harry Potter and the Philosopher's Stone"


def test_search_uses_cache_for_repeated_query():
    by_url = {
        book_api_client.OPEN_LIBRARY_SEARCH_URL: _make_mock_response({"docs": [OPEN_LIBRARY_DOC]}),
        book_api_client.OPEN_LIBRARY_BOOKS_URL: _make_mock_response(OPEN_LIBRARY_PAGE_COUNT_DATA),
        book_api_client.GOOGLE_BOOKS_URL: _make_mock_response({"items": [GOOGLE_BOOK_ITEM]}),
    }
    with patch.object(book_api_client.SESSION, "get", side_effect=_fake_get_by_url(by_url)) as mock_get:
        first = search_books("harry potter")
        call_count_after_first = mock_get.call_count
        second = search_books("harry potter")
    assert first == second
    assert mock_get.call_count == call_count_after_first
