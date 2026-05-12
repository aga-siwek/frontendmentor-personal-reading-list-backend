# Personal Reading List API

A RESTful API backend for a personal reading list application. Built with Flask and PostgreSQL, it allows users to manage their book collections, track reading progress, organize books into shelves, and set yearly reading goals.

## Features

- **User authentication** — JWT-based register and login
- **Book library** — search books by title, author, or ISBN via Google Books API (with Open Library fallback)
- **Reading list** — add books with status, rating, and personal notes
- **Reading progress** — track current page with automatic status updates and percentage calculation
- **Shelves** — organize books into custom named collections
- **Reading goals** — set yearly reading targets and track completion

## Tech Stack

- **Python 3.9+**
- **Flask** — web framework
- **SQLAlchemy** — ORM
- **PostgreSQL** — production database
- **Flask-JWT-Extended** — authentication
- **Flask-Bcrypt** — password hashing
- **Google Books API** — primary book data source
- **Open Library API** — fallback book data source
- **pytest** — testing

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database

### Installation

```bash
git clone <repo-url>
cd frontendmentor-personal-reading-list
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@host/dbname
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### Running the App

```bash
python main.py
```

The server will start at `http://localhost:5000`.

### Running Tests

```bash
python -m pytest tests/ -v
```

Tests use an in-memory SQLite database — no configuration required.

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/register/` | Register a new user |
| POST | `/users/login/` | Login and receive JWT token |

### Users

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/users/me/` | Get current user profile | User |
| PATCH | `/users/me/` | Update current user profile | User |
| DELETE | `/users/me/` | Delete current user account | User |
| GET | `/users/` | Get all users | Admin |
| GET | `/users/<id>/` | Get single user | Admin |
| PATCH | `/users/<id>/` | Update user | Admin |
| DELETE | `/users/<id>/` | Delete user | Admin |

### Books

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/books/search/?q=` | Search books by title, author, or ISBN | User |
| GET | `/books/<isbn>/` | Get book details | User |
| POST | `/books/<isbn>/` | Add book to reading list | User |
| PATCH | `/books/<isbn>/` | Update book on reading list | User |
| GET | `/books/me/` | Get all books on reading list | User |
| POST | `/books/<isbn>/progress/` | Add reading progress entry | User |
| GET | `/books/<isbn>/progress/` | Get reading progress history | User |

### Shelves

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/shelves/me/` | Get all shelves | User |
| POST | `/shelves/me/` | Create a shelf | User |
| GET | `/shelves/<id>/` | Get shelf with books | User |
| PATCH | `/shelves/<id>/` | Update shelf | User |
| DELETE | `/shelves/<id>/` | Delete shelf | User |
| POST | `/shelves/<id>/books/<isbn>/` | Add book to shelf | User |
| DELETE | `/shelves/<id>/books/<isbn>/` | Remove book from shelf | User |

### Reading Goals

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/goals/me/` | Get all reading goals | User |
| POST | `/goals/me/` | Create a reading goal | User |
| GET | `/goals/me/<year>/` | Get goal for a specific year | User |
| PATCH | `/goals/me/<year>/` | Update goal | User |
| DELETE | `/goals/me/<year>/` | Delete goal | User |

## Book Status Values

| Value | Description |
|-------|-------------|
| `want_to_read` | Added to reading list |
| `currently_reading` | Currently reading |
| `finished` | Finished reading |
| `recommended` | Recommended to others |
| `rejected` | Did not finish / not recommended |

## Request Examples

**Register**
```json
POST /users/register/
{
  "user_email": "user@example.com",
  "user_password": "password123"
}
```

**Add book to reading list**
```json
POST /books/9780747562184/
{
  "status": "currently_reading",
  "is_favourite": false,
  "notes": "Started for book club",
  "rating": null
}
```

**Add reading progress**
```json
POST /books/9780747562184/progress/
{
  "current_page": 150
}
```

**Create reading goal**
```json
POST /goals/me/
{
  "year": 2026,
  "goal": 24
}
```
