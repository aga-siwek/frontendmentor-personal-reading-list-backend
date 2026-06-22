import os
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_BOOKS_URL = "https://openlibrary.org/api/books"
OPEN_LIBRARY_COVERS_URL = "https://covers.openlibrary.org/b/id"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

OPEN_LIBRARY_HEADERS = {"User-Agent": "PersonalReadingList/1.0 (personal project)"}
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY")

# Reused across requests so repeated calls to the same hosts keep their TCP/TLS
# connection alive instead of renegotiating one per request.
SESSION = requests.Session()

_SEARCH_CACHE_TTL_SECONDS = 600
_search_cache: dict = {}
_search_cache_lock = threading.Lock()


def _https(url):
    if url and url.startswith("http://"):
        return "https://" + url[7:]
    return url


def _is_isbn(query: str) -> bool:
    stripped = query.replace("-", "").replace(" ", "")
    return stripped.isdigit() and len(stripped) in (10, 13)


def search_books(query: str, limit: int = 8) -> list:
    cache_key = (query.strip().lower(), limit)
    now = time.monotonic()
    with _search_cache_lock:
        cached = _search_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

    results = _search_open_library(query, limit)
    if not results:
        results = _search_google_books(query, limit)

    with _search_cache_lock:
        _search_cache[cache_key] = (now + _SEARCH_CACHE_TTL_SECONDS, results)
    return results


def _fetch_page_counts(isbns: list) -> dict:
    """One batched Open Library lookup that replaces per-ISBN Google Books calls
    for filtering out editions with no page count."""
    if not isbns:
        return {}
    bibkeys = ",".join(f"ISBN:{isbn}" for isbn in isbns)
    try:
        response = SESSION.get(OPEN_LIBRARY_BOOKS_URL, params={
            "bibkeys": bibkeys,
            "jscmd": "data",
            "format": "json",
        }, headers=OPEN_LIBRARY_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return {}
    return {isbn: data.get(f"ISBN:{isbn}", {}).get("number_of_pages", 0) for isbn in isbns}


def _fetch_google_for_isbn(isbn: str) -> dict:
    try:
        params = {"q": f"isbn:{isbn}", "maxResults": 1}
        if GOOGLE_BOOKS_API_KEY:
            params["key"] = GOOGLE_BOOKS_API_KEY
        response = SESSION.get(GOOGLE_BOOKS_URL, params=params, timeout=5)
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return {}
        vi = items[0]["volumeInfo"]
        thumbnail = _https(vi.get("imageLinks", {}).get("thumbnail"))
        return {
            "title": vi.get("title"),
            "cover": {"small": None, "medium": thumbnail, "large": None},
        }
    except requests.RequestException:
        return {}


def _search_open_library(query: str, limit: int) -> list:
    try:
        if _is_isbn(query):
            details = get_book_details(query.replace("-", "").replace(" ", ""))
            return [details] if details.get("title") else []
        response = SESSION.get(OPEN_LIBRARY_SEARCH_URL, params={
            "q": query,
            "limit": limit + 6,
            "fields": "title,author_name,isbn,cover_i,first_publish_year",
        }, headers=OPEN_LIBRARY_HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []
    docs = response.json().get("docs", [])

    candidates = []
    for doc in docs:
        isbns = doc.get("isbn", [])
        english_isbns = [i for i in isbns if len(i) == 13 and i.startswith(("9780", "9781"))][:2]
        fallback_isbn = next((i for i in isbns if len(i) == 13), isbns[0] if isbns else None)
        ordered_isbns = english_isbns[:5] or ([fallback_isbn] if fallback_isbn else [])
        if not ordered_isbns:
            continue
        cover_i = doc.get("cover_i")
        candidates.append({
            "title": doc.get("title"),
            "author": doc.get("author_name", [None])[0],
            "isbns": ordered_isbns,
            "cover": _build_covers(cover_i),
            "first_publish_year": doc.get("first_publish_year"),
        })

    if not candidates:
        return []

    # Single batched request instead of asking Google Books, ISBN by ISBN,
    # whether each edition has a page count.
    all_isbns = [isbn for candidate in candidates for isbn in candidate["isbns"]]

    # The page-count check (Open Library) doesn't depend on the cover/title
    # lookup (Google Books), so run them at the same time instead of waiting
    # for one to finish before starting the other. We don't know yet which
    # ISBN each candidate will end up using, so we prefetch Google data for
    # the most likely one (its first, preference-ordered ISBN) - the rare
    # case where that guess turns out invalid falls back to an extra request.
    best_guess_isbns = {candidate["isbns"][0] for candidate in candidates}
    with ThreadPoolExecutor(max_workers=min(len(best_guess_isbns), 8) + 1) as executor:
        page_counts_future = executor.submit(_fetch_page_counts, all_isbns)
        google_futures = {isbn: executor.submit(_fetch_google_for_isbn, isbn) for isbn in best_guess_isbns}
        page_counts = page_counts_future.result()
        google_by_isbn = {isbn: future.result() for isbn, future in google_futures.items()}

    chosen = []
    for candidate in candidates:
        isbn = next((i for i in candidate["isbns"] if page_counts.get(i, 0) > 0), None)
        if isbn:
            chosen.append({**candidate, "isbn": isbn})

    def _enrich_with_google(candidate: dict) -> dict:
        isbn = candidate["isbn"]
        google = google_by_isbn[isbn] if isbn in google_by_isbn else _fetch_google_for_isbn(isbn)
        if google.get("title"):
            candidate["title"] = google["title"]
        if google.get("cover", {}).get("medium"):
            candidate["cover"] = google["cover"]
        return candidate

    with ThreadPoolExecutor(max_workers=8) as executor:
        enriched = list(executor.map(_enrich_with_google, chosen))

    results = []
    seen_isbns = set()
    for item in enriched:
        if item["isbn"] not in seen_isbns:
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
        response = SESSION.get(GOOGLE_BOOKS_URL, params=params, timeout=10)
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
    # Google Books and Open Library are independent lookups, so run them
    # concurrently instead of waiting on one before starting the other.
    with ThreadPoolExecutor(max_workers=2) as executor:
        google_future = executor.submit(_fetch_google_book_details, isbn)
        ol_future = executor.submit(_fetch_ol_book_details, isbn)
        google_data = google_future.result()
        ol_data = ol_future.result()

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
        response = SESSION.get(GOOGLE_BOOKS_URL, params=params, timeout=5)
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
        response = SESSION.get(OPEN_LIBRARY_BOOKS_URL, params={
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
