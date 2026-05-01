# Education Website

Full-stack education website built with Flask (server-side templates) + JSON APIs.

## Features
- User registration + JWT login
- Bookstore with cart + checkout
- Course browsing, modules/resources, and progress tracking
- Forum with topics/posts and moderation (admin/mod roles)

## Tech Stack
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- SQLite (default for local dev) or MySQL (optional)

## Run locally (Windows / PowerShell)
1. Create and activate a virtual environment:
   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. (Recommended) set secure keys. The app reads:
   - `FLASK_SECRET_KEY`
   - `JWT_SECRET_KEY`
   
   If you do not set them, the app uses insecure dev defaults.
4. Start the server:
   ```powershell
   python -m backend.app
   ```
   The default port is **5000**. If that port is already in use, pick another (for example **5001**) before starting:
   ```powershell
   $env:PORT = "5001"
   python -m backend.app
   ```
5. Open the URL shown in the terminal (e.g. `http://localhost:5000` or `http://localhost:5001` if you set `PORT`).

## Website pages (server routes)
- `/` (home)
- `/login`
- `/register`
- `/bookstore`
- `/cart`
- `/my-ebooks`
- `/forum`
- `/courses`
- `/course/<course_id>`
- `/portal`
- `/admin`

## API (base URL: `/api`)
### Health
- `GET /health`

### Auth
- `POST /api/auth/register` (email, password, display_name)
- `POST /api/auth/login` (email, password)
- `GET /api/auth/me` (requires JWT)

### Books / Store
- `GET /api/books` (query filters: `search`, `category_id`, `min_price`, `max_price`)
- `GET /api/books/<book_id>`
- `GET /api/books/categories`
- `GET /api/cart` (JWT)
- `POST /api/cart/items` (JWT)
- `PATCH /api/cart/items/<item_id>` (JWT)
- `DELETE /api/cart/items/<item_id>` (JWT)
- `POST /api/checkout` (JWT)
- `GET /api/orders` (JWT)
- `GET /api/ebooks` (JWT)
- `GET /api/ebooks/<book_id>/download` (JWT)

### Courses
- `GET /api/courses`
- `GET /api/courses/<course_id>`
- `GET /api/courses/<course_id>/modules`
- `GET /api/modules/<module_id>/resources`
- `POST /api/resources/<resource_id>/complete` (JWT)
- `POST /api/resources/<resource_id>/save` (JWT)
- `DELETE /api/resources/<resource_id>/save` (JWT)
- `GET /api/progress` (JWT)
- `GET /api/completions` (JWT)
- `GET /api/saved` (JWT)

### Forum
- `GET /api/forum/topics`
- `POST /api/forum/topics` (JWT)
- `GET /api/forum/topics/<topic_id>`
- `POST /api/forum/topics/<topic_id>/posts` (JWT)
- `POST /api/forum/posts/<post_id>/report` (JWT)
- Moderation endpoints under `/api/mod/...` (JWT, role-protected)

## Local dev notes
- The database file is stored under `backend/instance/dev.db` and is ignored by git.
- The uploads directory is created automatically (see `.gitignore` for what is ignored).

