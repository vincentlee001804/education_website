from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from ..extensions import db
from ..models import Course, Book, ForumTopic

search_bp = Blueprint("search_bp", __name__)

@search_bp.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"data": {"courses": [], "books": [], "forum_topics": []}}), 200

    search_term = f"%{query}%"

    # Search Courses (title and description)
    courses = Course.query.filter(
        or_(Course.title.ilike(search_term), Course.description.ilike(search_term))
    ).limit(5).all()

    # Search Books (title and author)
    books = Book.query.filter(
        or_(Book.title.ilike(search_term), Book.author.ilike(search_term))
    ).limit(5).all()

    # Search Forum Topics (title)
    forum_topics = ForumTopic.query.filter(
        ForumTopic.title.ilike(search_term)
    ).limit(5).all()

    return jsonify({
        "data": {
            "courses": [
                {"id": c.id, "title": c.title, "description": c.description} for c in courses
            ],
            "books": [
                {"id": b.id, "title": b.title, "author": b.author} for b in books
            ],
            "forum_topics": [
                {"id": t.id, "title": t.title, "category": getattr(t, 'category', 'General')} for t in forum_topics
            ]
        }
    }), 200
