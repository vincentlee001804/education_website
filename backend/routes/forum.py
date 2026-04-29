from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from ..extensions import db
from ..models import ForumTopic, ForumPost, ForumReport


forum_bp = Blueprint("forum", __name__)


def _json_error(message: str, code: str = "bad_request", status_code: int = 400):
    return jsonify({"data": None, "error": {"code": code, "message": message}}), status_code


def _require_roles(allowed):
    from functools import wraps
    from flask_jwt_extended import jwt_required

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_roles = claims.get("roles", [])
            if not any(r in user_roles for r in allowed):
                return _json_error("Forbidden", code="forbidden", status_code=403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def _topic_to_dict(t: ForumTopic):
    return {
        "id": t.id,
        "title": t.title,
        "created_by": t.created_by,
        "created_at": t.created_at.isoformat(),
        "is_locked": t.is_locked,
        "status": t.status,
    }


def _post_to_dict(p: ForumPost):
    return {
        "id": p.id,
        "topic_id": p.topic_id,
        "content": p.content,
        "created_by": p.created_by,
        "created_at": p.created_at.isoformat(),
        "status": p.status,
    }


@forum_bp.get("/forum/topics")
def list_topics():
    search = request.args.get("search", "").strip()
    q = ForumTopic.query.filter(ForumTopic.status != "hidden")
    if search:
        # Basic search for project scaffold
        q = q.filter(ForumTopic.title.ilike(f"%{search}%"))
    topics = q.order_by(ForumTopic.created_at.desc()).all()
    return jsonify({"data": [_topic_to_dict(t) for t in topics], "error": None})


@forum_bp.post("/forum/topics")
@jwt_required()
def create_topic():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()

    if not title or len(title) < 4 or len(title) > 220:
        return _json_error("Topic title must be between 4 and 220 chars", code="invalid_title")

    topic = ForumTopic(title=title, created_by=user_id, is_locked=False, status="active")
    db.session.add(topic)
    db.session.commit()
    return jsonify({"data": {"topic_id": topic.id}, "error": None}), 201


@forum_bp.get("/forum/topics/<int:topic_id>")
def get_topic(topic_id: int):
    t = ForumTopic.query.get(topic_id)
    if not t or t.status == "hidden":
        return _json_error("Topic not found", code="not_found", status_code=404)

    posts = (
        ForumPost.query.filter_by(topic_id=topic_id)
        .filter(ForumPost.status.in_(["visible"]))
        .order_by(ForumPost.created_at.asc())
        .all()
    )
    return jsonify({"data": {"topic": _topic_to_dict(t), "posts": [_post_to_dict(p) for p in posts]}, "error": None})


@forum_bp.post("/forum/topics/<int:topic_id>/posts")
@jwt_required()
def create_post(topic_id: int):
    user_id = int(get_jwt_identity())
    t = ForumTopic.query.get(topic_id)
    if not t or t.status == "hidden":
        return _json_error("Topic not found", code="not_found", status_code=404)
    if t.is_locked:
        return _json_error("Topic is locked", code="topic_locked", status_code=403)

    payload = request.get_json(silent=True) or {}
    content = (payload.get("content") or "").strip()
    if not content or len(content) < 1 or len(content) > 4000:
        return _json_error("Post content invalid", code="invalid_content")

    post = ForumPost(topic_id=topic_id, content=content, created_by=user_id, status="visible")
    db.session.add(post)
    db.session.commit()
    return jsonify({"data": {"post_id": post.id}, "error": None}), 201


@forum_bp.post("/forum/posts/<int:post_id>/report")
@jwt_required()
def report_post(post_id: int):
    user_id = int(get_jwt_identity())
    p = ForumPost.query.get(post_id)
    if not p:
        return _json_error("Post not found", code="not_found", status_code=404)

    payload = request.get_json(silent=True) or {}
    reason = (payload.get("reason") or "").strip()
    if not reason or len(reason) < 3 or len(reason) > 500:
        return _json_error("Reason must be between 3 and 500 chars", code="invalid_reason")

    # Allow multiple reports; simple scaffold
    report = ForumReport(post_id=post_id, reporter_id=user_id, reason=reason, status="open")
    db.session.add(report)
    db.session.commit()
    return jsonify({"data": {"report_id": report.id}, "error": None}), 201


@forum_bp.get("/mod/reports")
@_require_roles(["moderator", "admin"])
def list_reports():
    reports = (
        ForumReport.query.filter_by(status="open")
        .order_by(ForumReport.created_at.desc())
        .limit(200)
        .all()
    )
    data = []
    for r in reports:
        data.append(
            {
                "id": r.id,
                "post_id": r.post_id,
                "reporter_id": r.reporter_id,
                "reason": r.reason,
                "created_at": r.created_at.isoformat(),
                "status": r.status,
            }
        )
    return jsonify({"data": data, "error": None})


@forum_bp.post("/mod/reports/<int:report_id>/action")
@_require_roles(["moderator", "admin"])
def take_report_action(report_id: int):
    user_id = int(get_jwt_identity())
    report = ForumReport.query.get(report_id)
    if not report or report.status != "open":
        return _json_error("Report not found or already resolved", code="not_found", status_code=404)

    payload = request.get_json(silent=True) or {}
    action = (payload.get("action") or "").strip().lower()
    moderation_note = (payload.get("note") or "").strip()  # optional

    post = ForumPost.query.get(report.post_id)
    if not post:
        report.status = "resolved"
        report.moderation_action = action
        report.moderated_by = user_id
        db.session.commit()
        return jsonify({"data": {"resolved": True}, "error": None})

    if action == "hide":
        post.status = "hidden"
    elif action == "delete":
        post.status = "deleted"
    elif action == "lock_topic":
        topic = ForumTopic.query.get(post.topic_id)
        if topic:
            topic.is_locked = True
    elif action == "approve":
        # No change to content; just resolve the report
        pass
    else:
        return _json_error("Invalid moderation action", code="invalid_action", status_code=400)

    report.status = "resolved"
    report.moderation_action = action
    report.moderated_by = user_id
    db.session.commit()

    return jsonify({"data": {"resolved": True, "action": action}, "error": None})


@forum_bp.post("/mod/topics/<int:topic_id>/lock")
@_require_roles(["moderator", "admin"])
def lock_topic(topic_id: int):
    t = ForumTopic.query.get(topic_id)
    if not t:
        return _json_error("Topic not found", code="not_found", status_code=404)
    t.is_locked = True
    db.session.commit()
    return jsonify({"data": {"locked": True}, "error": None})


@forum_bp.post("/mod/topics/<int:topic_id>/hide")
@_require_roles(["moderator", "admin"])
def hide_topic(topic_id: int):
    t = ForumTopic.query.get(topic_id)
    if not t:
        return _json_error("Topic not found", code="not_found", status_code=404)
    t.status = "hidden"
    db.session.commit()
    return jsonify({"data": {"hidden": True}, "error": None})


@forum_bp.post("/mod/posts/<int:post_id>/hide")
@_require_roles(["moderator", "admin"])
def hide_post(post_id: int):
    p = ForumPost.query.get(post_id)
    if not p:
        return _json_error("Post not found", code="not_found", status_code=404)
    p.status = "hidden"
    db.session.commit()
    return jsonify({"data": {"hidden": True}, "error": None})


@forum_bp.delete("/mod/posts/<int:post_id>")
@_require_roles(["moderator", "admin"])
def delete_post(post_id: int):
    p = ForumPost.query.get(post_id)
    if not p:
        return _json_error("Post not found", code="not_found", status_code=404)
    p.status = "deleted"
    db.session.commit()
    return jsonify({"data": {"deleted": True}, "error": None})

