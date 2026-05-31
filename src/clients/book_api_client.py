import os
import requests

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY")


def _is_isbn(query: str) -> bool:
    stripped = query.replace("-", "").replace(" ", "")
    return stripped.isdigit() and len(stripped) in (10, 13)


def _google_params(extra: dict) -> dict:
    params = {**extra}
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY
    return params


def search_books(query: str, limit: int = 8) -> list:
    q = f"isbn:{query.replace('-', '').replace(' ', '')}" if _is_isbn(query) else query
    try:
        response = requests.get(
            GOOGLE_BOOKS_URL,
            params=_google_params({"q": q, "maxResults": 40, "printType": "books", "langRestrict": "en"}),
            timeout=10,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
    except requests.RequestException:
        return []

    seen_isbns = set()
    results = []
    for item in items:
        vi = item.get("volumeInfo", {})
        if not vi.get("language", "").startswith("en"):
            continue
        identifiers = vi.get("industryIdentifiers", [])
        isbn = next((i["identifier"] for i in identifiers if i["type"] == "ISBN_13"), None)
        if not isbn:
            isbn = next((i["identifier"] for i in identifiers if i["type"] == "ISBN_10"), None)
        if not isbn or isbn in seen_isbns:
            continue
        seen_isbns.add(isbn)
        image_links = vi.get("imageLinks", {})
        published_date = vi.get("publishedDate", "")
        year = int(published_date[:4]) if published_date and published_date[:4].isdigit() else None
        results.append({
            "title": vi.get("title"),
            "author": vi.get("authors", [None])[0],
            "isbn": isbn,
            "cover": {
                "small": image_links.get("smallThumbnail"),
                "medium": image_links.get("thumbnail"),
                "large": image_links.get("large"),
            },
            "first_publish_year": year,
        })

    results.sort(key=lambda x: x["first_publish_year"] or 0, reverse=True)
    return results[:limit]


def get_book_details(isbn: str) -> dict:
    try:
        response = requests.get(
            GOOGLE_BOOKS_URL,
            params=_google_params({"q": f"isbn:{isbn}"}),
            timeout=5,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return {}
        vi = items[0].get("volumeInfo", {})
    except requests.RequestException:
        return {}

    identifiers = vi.get("industryIdentifiers", [])
    isbn13 = next((i["identifier"] for i in identifiers if i["type"] == "ISBN_13"), isbn)
    authors = vi.get("authors", [])
    image_links = vi.get("imageLinks", {})
    return {
        "isbn": isbn13,
        "title": vi.get("title"),
        "author": authors[0] if authors else None,
        "cover": {
            "small": image_links.get("smallThumbnail"),
            "medium": image_links.get("thumbnail"),
            "large": image_links.get("large"),
        },
        "description": vi.get("description"),
        "categories": vi.get("categories", []),
        "number_of_pages": vi.get("pageCount"),
        "publish_date": vi.get("publishedDate"),
        "publisher": vi.get("publisher"),
        "source_api_id": None,
    }
