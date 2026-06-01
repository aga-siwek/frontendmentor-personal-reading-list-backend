import os
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_BOOKS_URL = "https://openlibrary.org/api/books"
OPEN_LIBRARY_COVERS_URL = "https://covers.openlibrary.org/b/id"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

OPEN_LIBRARY_HEADERS = {"User-Agent": "PersonalReadingList/1.0 (personal project)"}
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY")


def _https(url):
    if url and url.startswith("http://"):
        return "https://" + url[7:]
    return url


def _fetch_google_for_isbn(isbn: str) -> Optional[dict]:
    try:
        params = {"q": f"isbn:{isbn}", "maxResults": 1}
        if GOOGLE_BOOKS_API_KEY:
            params["key"] = GOOGLE_BOOKS_API_KEY
        response = requests.get(GOOGLE_BOOKS_URL, params=params, timeout=5)
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return {}
        vi = items[0]["volumeInfo"]
        if not vi.get("pageCount", 0):
            return None
        thumbnail = _https(vi.get("imageLinks", {}).get("thumbnail"))
        return {
            "isbn": isbn,
            "title": vi.get("title"),
            "cover": {"small": None, "medium": thumbnail, "large": None},
        }
    except requests.RequestException:
        return {}


def _is_isbn(query: str) -> bool:
    stripped = query.replace("-", "").replace(" ", "")
    return stripped.isdigit() and len(stripped) in (10, 13)


def search_books(query: str, limit: int = 8) -> list:
    results = _search_open_library(query, limit)
    if results:
        return results
    return _search_google_books(query, limit)


def _search_open_library(query: str, limit: int) -> list:
    try:
        if _is_isbn(query):
            details = get_book_details(query.replace("-", "").replace(" ", ""))
            return [details] if details.get("title") else []
        response = requests.get(OPEN_LIBRARY_SEARCH_URL, params={
            "q": query,
            "limit": limit * 2,
            "fields": "title,author_name,isbn,cover_i,first_publish_year",
        }, headers=OPEN_LIBRARY_HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []
    docs = response.json().get("docs", [])

    seen_isbns = set()
    candidates = []
    for doc in docs:
        isbns = doc.get("isbn", [])
        english_isbns = [i for i in isbns if len(i) == 13 and i.startswith(("9780", "9781"))][:2]
        fallback_isbn = next((i for i in isbns if len(i) == 13), isbns[0] if isbns else None)
        ordered_isbns = english_isbns[:5] or ([fallback_isbn] if fallback_isbn else [])
        new_isbns = [i for i in ordered_isbns if i not in seen_isbns]
        if not new_isbns:
            continue
        cover_i = doc.get("cover_i")
        candidates.append({
            "title": doc.get("title"),
            "author": doc.get("author_name", [None])[0],
            "isbns": new_isbns,
            "cover": _build_covers(cover_i),
            "first_publish_year": doc.get("first_publish_year"),
        })

    def _pick_valid(candidate: dict) -> Optional[dict]:
        for isbn in candidate["isbns"]:
            google = _fetch_google_for_isbn(isbn)
            if google is not None:
                result = {**candidate, "isbn": isbn}
                if google.get("title"):
                    result["title"] = google["title"]
                if google.get("cover", {}).get("medium"):
                    result["cover"] = google["cover"]
                return result
        return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        validated = list(executor.map(_pick_valid, candidates))

    results = []
    seen_isbns = set()
    for item in validated:
        if item and item["isbn"] not in seen_isbns:
            seen_isbns.add(item["isbn"])
            results.append({k: v for k, v in item.items() if k != "isbns"})

    results.sort(key=lambda x: x["first_publish_year"] or 0, reverse=True)
    return results[:limit]


def _search_google_books(query: str, limit: int) -> list:
    try:
        q = f"isbn:{query}" if _is_isbn(query) else query
        params = {"q": q, "maxResults": 40, "printType": "books"}
        if GOOGLE_BOOKS_API_KEY:
            params["key"] = GOOGLE_BOOKS_API_KEY
        response = requests.get(GOOGLE_BOOKS_URL, params=params, timeout=10)
        response.raise_for_status()
        items = response.json().get("items", [])

        seen_isbns = set()
        results = []
        for item in items:
            volume_info = item.get("volumeInfo", {})
            identifiers = volume_info.get("industryIdentifiers", [])
            isbn = next((i["identifier"] for i in identifiers if i["type"] == "ISBN_13"), None)
            if not isbn:
                isbn = next((i["identifier"] for i in identifiers if i["type"] == "ISBN_10"), None)
            if not isbn or isbn in seen_isbns:
                continue
            seen_isbns.add(isbn)
            image_links = volume_info.get("imageLinks", {})
            published_date = volume_info.get("publishedDate", "")
            year = int(published_date[:4]) if published_date and published_date[:4].isdigit() else None
            results.append({
                "title": volume_info.get("title"),
                "author": volume_info.get("authors", [None])[0],
                "isbn": isbn,
                "cover": {
                    "small": _https(image_links.get("smallThumbnail")),
                    "medium": _https(image_links.get("thumbnail")),
                    "large": _https(image_links.get("large")),
                },
                "first_publish_year": year,
            })

        results.sort(key=lambda x: x["first_publish_year"] or 0, reverse=True)
        return results[:limit]
    except requests.RequestException:
        return []


def get_book_details(isbn: str) -> dict:
    google_data = _fetch_google_book_details(isbn)
    ol_data = _fetch_ol_book_details(isbn)
    base = ol_data if ol_data.get("title") else google_data
    if not base.get("cover", {}).get("medium") and google_data.get("cover", {}).get("medium"):
        base["cover"] = google_data["cover"]
    if google_data.get("description"):
        base["description"] = google_data["description"]
    if google_data.get("categories"):
        base["categories"] = google_data["categories"]
    return base


def _fetch_google_book_details(isbn: str) -> dict:
    try:
        params = {"q": f"isbn:{isbn}"}
        if GOOGLE_BOOKS_API_KEY:
            params["key"] = GOOGLE_BOOKS_API_KEY
        response = requests.get(GOOGLE_BOOKS_URL, params=params, timeout=5)
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return {}
        vi = items[0].get("volumeInfo", {})
        identifiers = vi.get("industryIdentifiers", [])
        isbn13 = next((i["identifier"] for i in identifiers if i["type"] == "ISBN_13"), isbn)
        authors = vi.get("authors", [])
        image_links = vi.get("imageLinks", {})
        return {
            "isbn": isbn13,
            "title": vi.get("title"),
            "author": authors[0] if authors else None,
            "cover": {
                "small": _https(image_links.get("smallThumbnail")),
                "medium": _https(image_links.get("thumbnail")),
                "large": _https(image_links.get("large")),
            },
            "description": vi.get("description"),
            "categories": vi.get("categories", []),
            "number_of_pages": vi.get("pageCount"),
            "publish_date": vi.get("publishedDate"),
            "publisher": vi.get("publisher"),
            "source_api_id": None,
        }
    except requests.RequestException:
        return {}


def _fetch_ol_book_details(isbn: str) -> dict:
    bibkey = f"ISBN:{isbn}"
    try:
        response = requests.get(OPEN_LIBRARY_BOOKS_URL, params={
            "bibkeys": bibkey,
            "jscmd": "data",
            "format": "json",
        }, headers=OPEN_LIBRARY_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json().get(bibkey, {})
    except requests.RequestException:
        data = {}

    authors = data.get("authors", [])
    publishers = data.get("publishers", [])
    cover = data.get("cover", {}).get("medium")
    subjects = [s["name"] for s in data.get("subjects", []) if s.get("name", "").isascii()][:5]
    return {
        "isbn": isbn,
        "title": data.get("title"),
        "author": authors[0]["name"] if authors else None,
        "cover": {"small": None, "medium": cover, "large": None},
        "description": None,
        "categories": subjects,
        "number_of_pages": data.get("number_of_pages"),
        "publish_date": data.get("publish_date"),
        "publisher": publishers[0]["name"] if publishers else None,
        "source_api_id": data.get("key"),
    }


def _build_covers(cover_i: Optional[int]) -> dict:
    if not cover_i:
        return {"small": None, "medium": None, "large": None}
    return {
        "small": f"{OPEN_LIBRARY_COVERS_URL}/{cover_i}-S.jpg",
        "medium": f"{OPEN_LIBRARY_COVERS_URL}/{cover_i}-M.jpg",
        "large": f"{OPEN_LIBRARY_COVERS_URL}/{cover_i}-L.jpg",
    }
