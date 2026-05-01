import os

from flask import Flask, send_from_directory
from flask_migrate import Migrate

from .config import Config
from .extensions import db, jwt
from .routes.auth import auth_bp
from .routes.books import books_bp
from .routes.courses import courses_bp
from .routes.forum import forum_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_object(Config)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    db.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(books_bp, url_prefix="/api")
    app.register_blueprint(courses_bp, url_prefix="/api")
    app.register_blueprint(forum_bp, url_prefix="/api")

    # Static "frontend" pages: no server-side rendering; HTML is static and
    # fetches API JSON.
    @app.route("/", methods=["GET"])
    def index():
        return send_from_directory(app.template_folder, "index.html")

    @app.route("/login", methods=["GET"])
    def login_page():
        return send_from_directory(app.template_folder, "login.html")

    @app.route("/register", methods=["GET"])
    def register_page():
        return send_from_directory(app.template_folder, "register.html")

    @app.route("/bookstore", methods=["GET"])
    def bookstore_page():
        return send_from_directory(app.template_folder, "bookstore.html")

    @app.route("/cart", methods=["GET"])
    def cart_page():
        return send_from_directory(app.template_folder, "cart.html")

    @app.route("/my-ebooks", methods=["GET"])
    def my_ebooks_page():
        return send_from_directory(app.template_folder, "my-ebooks.html")

    @app.route("/forum", methods=["GET"])
    def forum_page():
        return send_from_directory(app.template_folder, "forum.html")

    @app.route("/courses", methods=["GET"])
    def courses_page():
        return send_from_directory(app.template_folder, "courses.html")

    @app.route("/course/<int:course_id>", methods=["GET"])
    def course_page(course_id: int):
        return send_from_directory(app.template_folder, "course.html")

    @app.route("/portal", methods=["GET"])
    def portal_page():
        return send_from_directory(app.template_folder, "portal.html")

    @app.route("/admin", methods=["GET"])
    def admin_page():
        return send_from_directory(app.template_folder, "admin.html")

    @app.route("/admin/courses", methods=["GET"])
    def admin_courses_page():
        return send_from_directory(app.template_folder, "admin-courses.html")

    @app.route("/admin/bookstore", methods=["GET"])
    def admin_bookstore_page():
        return send_from_directory(app.template_folder, "admin-bookstore.html")

    @app.route("/admin/users", methods=["GET"])
    def admin_users_page():
        return send_from_directory(app.template_folder, "admin-users.html")

    # Helpful health check.
    @app.route("/health", methods=["GET"])
    def health():
        return {"ok": True, "service": "education-website-api"}, 200

    with app.app_context():
        # For early development we create tables automatically.
        # For production / grading you can switch to migrations.
        db.create_all()

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    create_app().run(host="0.0.0.0", port=port, debug=True)

