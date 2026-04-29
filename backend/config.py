import os


class Config:
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(15 * 1024 * 1024)))  # 15 MB default

    # MySQL (SQLAlchemy URI)
    # Example:
    # mysql+pymysql://user:password@localhost:3306/education_website
    # For local dev, we default to SQLite so the app can boot without MySQL running.
    # Important: use an absolute path anchored to this module, so the same DB is used
    # whether you run via `python -m backend.app` or import `backend.app`.
    _default_sqlite_dir = os.path.join(os.path.dirname(__file__), "instance")
    os.makedirs(_default_sqlite_dir, exist_ok=True)
    _default_sqlite_path = os.path.join(_default_sqlite_dir, "dev.db")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{_default_sqlite_path}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me-too")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30"))

    # Uploads
    UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", os.path.join(os.path.dirname(__file__), "..", "uploads"))
    BOOK_IMAGE_DIR = os.path.join(UPLOAD_ROOT, "book_images")
    EBOOK_PDF_DIR = os.path.join(UPLOAD_ROOT, "ebook_pdfs")

