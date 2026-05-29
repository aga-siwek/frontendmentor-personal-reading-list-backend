# Personal Reading List API

> A production-ready RESTful API for tracking your reading life — built as a full-stack portfolio project.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat&logo=docker&logoColor=white)
![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=flat&logo=render&logoColor=white)

**Live API:** https://frontendmentor-personal-reading-list.onrender.com

---

## About the Project

This project started as a [Frontend Mentor](https://www.frontendmentor.io/) challenge and grew into a full-stack application with a custom-built backend. The goal was to go beyond a static frontend and build a real, deployable API that handles authentication, persistent data, and integration with external services.

The API powers a reading tracker where users can search for books, build a personal reading list, track their reading progress page by page, organise books into custom shelves, and set yearly reading goals.

**Key decisions and challenges:**

- **Dual book data source** — Google Books API is the primary source for searches. Because it does not reliably distinguish audiobooks from print editions, results are validated against Open Library before being returned to the client, filtering out audiobooks and ensuring consistent cover images and titles.
- **JWT authentication** — stateless authentication with access tokens stored on the client, keeping the API fully RESTful.
- **Automatic progress tracking** — adding a progress entry automatically updates the book's reading status (e.g. switches to `currently_reading` on first page logged, `finished` when the last page is reached).
- **Docker + Render deployment** — the full stack (app + PostgreSQL) runs locally via Docker Compose; in production the app deploys to Render with a managed Neon PostgreSQL database.

---

## Features

- **User authentication** — register, login, JWT-protected endpoints
- **Book search** — search by title, author, or ISBN; validated against two external APIs
- **Reading list** — add books with status, rating, favourite flag, and personal notes
- **Reading progress** — log current page; percentage and status update automatically
- **Shelves** — create custom collections and organise books between them
- **Reading goals** — set a yearly target and track how many books you've finished

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Language | Python 3.9 | Readable, wide ecosystem, strong typing support |
| Framework | Flask | Lightweight, unopinionated — good fit for a focused REST API |
| ORM | SQLAlchemy | Expressive query API, database-agnostic |
| Database | PostgreSQL | Relational integrity for books, shelves, and progress entries |
| Auth | Flask-JWT-Extended | Stateless JWT tokens, minimal setup |
| Password hashing | Flask-Bcrypt | Industry-standard bcrypt hashing |
| External APIs | Google Books + Open Library | Book metadata and cover images |
| WSGI server | Gunicorn | Production-grade, multi-worker HTTP server |
| Containerisation | Docker + Docker Compose | Reproducible local environment |
| Deployment | Render | Free-tier Docker hosting with automatic deploys from GitHub |
| Testing | pytest | Fast, fixture-based unit and integration tests |

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Option 1)
- Python 3.9+ and PostgreSQL (for Option 2)
- A free [Google Books API key](https://console.cloud.google.com/)

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Fill in your values:

```env
DATABASE_URL=postgresql://user:password@host/dbname
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
GOOGLE_BOOKS_API_KEY=your-google-books-api-key
```

---

### Option 1 — Docker (recommended)

```bash
git clone <repo-url>
cd frontendmentor-personal-reading-list
docker-compose up --build
```

The API starts at `http://localhost:5005`. The database is provisioned automatically.

```bash
docker-compose down       # stop containers
docker-compose down -v    # stop and remove database volume
```

---

### Option 2 — Local Setup

```bash
git clone <repo-url>
cd frontendmentor-personal-reading-list
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The API starts at `http://localhost:5000`.

---

### Running Tests

```bash
python -m pytest tests/ -v
```

Tests use an in-memory SQLite database — no external services required.

---

## Project Structure

```
.
├── src/
│   ├── clients/        # External API clients (Google Books, Open Library)
│   ├── models/         # SQLAlchemy models (User, Book, Shelf, ReadingGoal, ReadingProgress)
│   ├── routes/         # Flask blueprints (one per resource)
│   ├── services/       # Business logic layer
│   ├── config.py       # Environment-based configuration
│   └── database.py     # SQLAlchemy instance
├── tests/              # pytest test suite
├── main.py             # Application factory entry point
├── Dockerfile          # Production container image
├── docker-compose.yml  # Local development stack
└── requirements.txt    # Python dependencies
```

---

## Deployment

The project deploys to [Render](https://render.com) via Docker with a [Neon](https://neon.tech/) managed PostgreSQL database.

**To deploy your own instance:**

1. Push the repo to GitHub
2. Create a new **Web Service** on Render, select the repo, runtime: **Docker**
3. Add environment variables from `.env.example` in the Render dashboard
4. Deploy — Render builds the image and serves the API on a public HTTPS URL

> **Note:** On Render's free plan the service spins down after 15 minutes of inactivity. The first request after idle may take up to 30 seconds to respond.

---

## API Reference

All protected endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/register/` | Register a new user |
| POST | `/users/login/` | Login and receive a JWT token |

### Users

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/users/me/` | Get current user profile | User |
| PATCH | `/users/me/` | Update current user profile | User |
| DELETE | `/users/me/` | Delete current user account | User |
| GET | `/users/` | List all users | Admin |
| GET | `/users/<id>/` | Get a single user | Admin |
| PATCH | `/users/<id>/` | Update a user | Admin |
| DELETE | `/users/<id>/` | Delete a user | Admin |

### Books

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/books/search/?q=` | Search books by title, author, or ISBN | User |
| GET | `/books/<isbn>/` | Get book details | User |
| POST | `/books/<isbn>/` | Add book to reading list | User |
| PATCH | `/books/<isbn>/` | Update book on reading list | User |
| GET | `/books/me/` | Get all books on reading list | User |
| POST | `/books/<isbn>/progress/` | Log a reading progress entry | User |
| GET | `/books/<isbn>/progress/` | Get reading progress history | User |

### Shelves

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/shelves/me/` | Get all shelves | User |
| POST | `/shelves/me/` | Create a shelf | User |
| GET | `/shelves/<id>/` | Get a shelf with its books | User |
| PATCH | `/shelves/<id>/` | Rename a shelf | User |
| DELETE | `/shelves/<id>/` | Delete a shelf | User |
| POST | `/shelves/<id>/books/<isbn>/` | Add a book to a shelf | User |
| DELETE | `/shelves/<id>/books/<isbn>/` | Remove a book from a shelf | User |

### Reading Goals

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/goals/me/` | Get all reading goals | User |
| POST | `/goals/me/` | Create a reading goal | User |
| GET | `/goals/me/<year>/` | Get goal for a specific year | User |
| PATCH | `/goals/me/<year>/` | Update goal | User |
| DELETE | `/goals/me/<year>/` | Delete goal | User |

---

## Reference

### Book Status Values

| Value | Description |
|-------|-------------|
| `want_to_read` | Saved to reading list, not started |
| `currently_reading` | In progress |
| `finished` | Completed |
| `recommended` | Finished and recommended |
| `rejected` | Did not finish / not recommended |

### Request & Response Examples

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

**Log reading progress**
```json
POST /books/9780747562184/progress/
{
  "current_page": 150
}
```

**Create a reading goal**
```json
POST /goals/me/
{
  "year": 2026,
  "goal": 24
}
```
