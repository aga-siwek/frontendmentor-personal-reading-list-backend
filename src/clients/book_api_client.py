import requests
from typing import Optional

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_BOOKS_URL = "https://openlibrary.org/api/books"
OPEN_LIBRARY_COVERS_URL = "https://covers.openlibrary.org/b/id"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


def search_books_by_title(title: str, limit: int = 8) -> list:
    try:
        response = requests.get(GOOGLE_BOOKS_URL, params={
            "q": f"intitle:{title}",
            "maxResults": 40,
            "printType": "books",
            "langRestrict": "en",
        }, timeout=10)
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
            if volume_info.get("language") != "en":
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
                    "small": image_links.get("smallThumbnail"),
                    "medium": image_links.get("thumbnail"),
                    "large": image_links.get("large"),
                },
                "first_publish_year": year,
            })

        results.sort(key=lambda x: x["first_publish_year"] or 0, reverse=True)
        return results[:limit]
    except requests.RequestException:
        return _search_open_library(title, limit)


def _search_open_library(title: str, limit: int) -> list:
    response = requests.get(OPEN_LIBRARY_SEARCH_URL, params={
        "title": title,
        "limit": limit,
        "fields": "title,author_name,isbn,cover_i,first_publish_year",
        "language": "eng",
    }, timeout=10)
    response.raise_for_status()
    docs = response.json().get("docs", [])

    seen_isbns = set()
    results = []
    for doc in docs:
        isbns = doc.get("isbn", [])
        isbn = next((i for i in isbns if len(i) == 13), isbns[0] if isbns else None)
        if not isbn or isbn in seen_isbns:
            continue
        seen_isbns.add(isbn)
        cover_i = doc.get("cover_i")
        results.append({
            "title": doc.get("title"),
            "author": doc.get("author_name", [None])[0],
            "isbn": isbn,
            "cover": _build_covers(cover_i),
            "first_publish_year": doc.get("first_publish_year"),
        })

    results.sort(key=lambda x: x["first_publish_year"] or 0, reverse=True)
    return results


def get_book_details(isbn: str) -> dict:
    bibkey = f"ISBN:{isbn}"
    response = requests.get(OPEN_LIBRARY_BOOKS_URL, params={
        "bibkeys": bibkey,
        "jscmd": "data",
        "format": "json",
    })
    response.raise_for_status()
    data = response.json().get(bibkey, {})

    covers = data.get("cover", {})
    google_data = _fetch_google_data(isbn)
    authors = data.get("authors", [])
    publishers = data.get("publishers", [])
    return {
        "isbn": isbn,
        "title": data.get("title"),
        "author": authors[0]["name"] if authors else None,
        "cover": {
            "small": covers.get("small"),
            "medium": covers.get("medium"),
            "large": covers.get("large"),
        },
        "description": google_data["description"],
        "categories": google_data["categories"],
        "number_of_pages": data.get("number_of_pages"),
        "publish_date": data.get("publish_date"),
        "publisher": publishers[0]["name"] if publishers else None,
        "source_api_id": data.get("key"),
    }


def _fetch_google_data(isbn: str) -> dict:
    try:
        response = requests.get(GOOGLE_BOOKS_URL, params={"q": f"isbn:{isbn}"}, timeout=5)
        response.raise_for_status()
        items = response.json().get("items", [])
        if items:
            volume_info = items[0].get("volumeInfo", {})
            return {
                "description": volume_info.get("description"),
                "categories": volume_info.get("categories", []),
            }
    except requests.RequestException:
        pass
    return {"description": None, "categories": []}


def _build_covers(cover_i: Optional[int]) -> dict:
    if not cover_i:
        return {"small": None, "medium": None, "large": None}
    return {
        "small": f"{OPEN_LIBRARY_COVERS_URL}/{cover_i}-S.jpg",
        "medium": f"{OPEN_LIBRARY_COVERS_URL}/{cover_i}-M.jpg",
        "large": f"{OPEN_LIBRARY_COVERS_URL}/{cover_i}-L.jpg",
    }
