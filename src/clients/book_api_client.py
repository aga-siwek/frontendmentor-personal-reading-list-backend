import requests

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_BOOKS_URL = "https://openlibrary.org/api/books"
OPEN_LIBRARY_COVERS_URL = "https://covers.openlibrary.org/b/id"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


def search_books_by_title(title: str, limit: int = 8) -> list[dict]:
    response = requests.get(OPEN_LIBRARY_SEARCH_URL, params={
        "title": title,
        "limit": limit,
        "fields": "title,author_name,isbn,cover_i",
    })
    response.raise_for_status()
    docs = response.json().get("docs", [])

    results = []
    for doc in docs:
        isbns = doc.get("isbn", [])
        isbn = next((i for i in isbns if len(i) == 13), isbns[0] if isbns else None)
        cover_i = doc.get("cover_i")
        results.append({
            "title": doc.get("title"),
            "author": doc.get("author_name", [None])[0],
            "isbn": isbn,
            "cover": _build_covers(cover_i),
        })
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

    cover_id = None
    covers = data.get("cover", {})
    if covers.get("small"):
        cover_id = covers["small"].split("/")[-1].replace("-S.jpg", "")

    google_data = _fetch_google_data(isbn)
    authors = data.get("authors", [])
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


def _build_covers(cover_i: int | None) -> dict:
    if not cover_i:
        return {"small": None, "medium": None, "large": None}
    return {
        "small": f"{OPEN_LIBRARY_COVERS_URL}/{cover_i}-S.jpg",
        "medium": f"{OPEN_LIBRARY_COVERS_URL}/{cover_i}-M.jpg",
        "large": f"{OPEN_LIBRARY_COVERS_URL}/{cover_i}-L.jpg",
    }
