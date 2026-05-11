from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import (
    Subject,
    Course,
    Module,
    Resource,
    ResourceCompletion,
    SavedResource,
)


courses_bp = Blueprint("courses", __name__)


def _json_error(message: str, code: str = "bad_request", status_code: int = 400):
    return jsonify({"data": None, "error": {"code": code, "message": message}}), status_code


def _require_roles(allowed):
    from functools import wraps
    from flask_jwt_extended import jwt_required, get_jwt

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


def _resource_to_dict(r: Resource):
    return {
        "id": r.id,
        "module_id": r.module_id,
        "title": r.title,
        "resource_type": r.resource_type,
        "content_text": r.content_text,
        "content_url": r.content_url,
    }


@courses_bp.get("/courses")
def list_courses():
    # Optional: filter by subject_id
    subject_id = request.args.get("subject_id", type=int)
    q = Course.query
    if subject_id is not None:
        q = q.filter(Course.subject_id == subject_id)

    courses = q.order_by(Course.id.desc()).all()
    return jsonify(
        {
            "data": [
                {"id": c.id, "title": c.title, "description": c.description, "subject_id": c.subject_id}
                for c in courses
            ],
            "error": None,
        }
    )


@courses_bp.get("/courses/<int:course_id>")
def get_course(course_id: int):
    c = Course.query.get(course_id)
    if not c:
        return _json_error("Course not found", code="not_found", status_code=404)
    return jsonify(
        {
            "data": {"id": c.id, "title": c.title, "description": c.description, "subject_id": c.subject_id},
            "error": None,
        }
    )


@courses_bp.get("/courses/<int:course_id>/modules")
def list_modules(course_id: int):
    modules = Module.query.filter_by(course_id=course_id).order_by(Module.order_index.asc()).all()
    return jsonify(
        {"data": [{"id": m.id, "title": m.title, "course_id": m.course_id, "order_index": m.order_index} for m in modules], "error": None}
    )


@courses_bp.get("/modules/<int:module_id>/resources")
def list_resources(module_id: int):
    resources = Resource.query.filter_by(module_id=module_id).order_by(Resource.id.asc()).all()
    return jsonify({"data": [_resource_to_dict(r) for r in resources], "error": None})


@courses_bp.get("/resources/<int:resource_id>")
def get_resource(resource_id: int):
    r = Resource.query.get(resource_id)
    if not r:
        return _json_error("Resource not found", code="not_found", status_code=404)
    return jsonify({"data": _resource_to_dict(r), "error": None})


@courses_bp.post("/resources/<int:resource_id>/complete")
@jwt_required()
def complete_resource(resource_id: int):
    user_id = int(get_jwt_identity())
    r = Resource.query.get(resource_id)
    if not r:
        return _json_error("Resource not found", code="not_found", status_code=404)

    existing = ResourceCompletion.query.filter_by(user_id=user_id, resource_id=resource_id).first()
    if not existing:
        db.session.add(ResourceCompletion(user_id=user_id, resource_id=resource_id))
        db.session.commit()

    return jsonify({"data": {"resource_id": resource_id, "completed": True}, "error": None})


@courses_bp.delete("/resources/<int:resource_id>/complete")
@jwt_required()
def uncomplete_resource(resource_id: int):
    user_id = int(get_jwt_identity())
    existing = ResourceCompletion.query.filter_by(user_id=user_id, resource_id=resource_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return jsonify({"data": {"resource_id": resource_id, "completed": False}, "error": None})


@courses_bp.post("/resources/<int:resource_id>/save")
@jwt_required()
def save_resource(resource_id: int):
    user_id = int(get_jwt_identity())
    r = Resource.query.get(resource_id)
    if not r:
        return _json_error("Resource not found", code="not_found", status_code=404)

    existing = SavedResource.query.filter_by(user_id=user_id, resource_id=resource_id).first()
    if not existing:
        db.session.add(SavedResource(user_id=user_id, resource_id=resource_id))
        db.session.commit()

    return jsonify({"data": {"resource_id": resource_id, "saved": True}, "error": None})


@courses_bp.delete("/resources/<int:resource_id>/save")
@jwt_required()
def unsave_resource(resource_id: int):
    user_id = int(get_jwt_identity())
    existing = SavedResource.query.filter_by(user_id=user_id, resource_id=resource_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return jsonify({"data": {"resource_id": resource_id, "saved": False}, "error": None})


@courses_bp.get("/progress")
@jwt_required()
def get_progress():
    user_id = int(get_jwt_identity())
    course_id = request.args.get("course_id", type=int)

    if course_id is not None:
        course = Course.query.get(course_id)
        if not course:
            return _json_error("Course not found", code="not_found", status_code=404)

        module_ids = [m.id for m in Module.query.filter_by(course_id=course_id).all()]
        if not module_ids:
            total_resources = 0
            completed_count = 0
            saved_count = 0
        else:
            resource_ids = [r.id for r in Resource.query.filter(Resource.module_id.in_(module_ids)).all()]
            total_resources = len(resource_ids)
            if not resource_ids:
                completed_count = 0
                saved_count = 0
            else:
                completed_count = (
                    ResourceCompletion.query.filter_by(user_id=user_id)
                    .filter(ResourceCompletion.resource_id.in_(resource_ids))
                    .count()
                )
                saved_count = (
                    SavedResource.query.filter_by(user_id=user_id)
                    .filter(SavedResource.resource_id.in_(resource_ids))
                    .count()
                )
    else:
        # Compute per-user progress across all resources.
        total_resources = Resource.query.count()
        completed_count = ResourceCompletion.query.filter_by(user_id=user_id).count()
        saved_count = SavedResource.query.filter_by(user_id=user_id).count()

    percent = 0 if total_resources == 0 else int((completed_count / total_resources) * 100)
    return jsonify(
        {
            "data": {
                "total_resources": total_resources,
                "completed_count": completed_count,
                "progress_percent": percent,
                "saved_count": saved_count,
            },
            "error": None,
        }
    )


@courses_bp.get("/completions")
@jwt_required()
def list_completions():
    user_id = int(get_jwt_identity())
    rows = ResourceCompletion.query.filter_by(user_id=user_id).all()
    return jsonify({"data": {"resource_ids": [r.resource_id for r in rows]}, "error": None})


@courses_bp.get("/saved")
@jwt_required()
def list_saved():
    user_id = int(get_jwt_identity())
    saved = (
        SavedResource.query.filter_by(user_id=user_id)
        .order_by(SavedResource.saved_at.desc())
        .all()
    )
    out = []
    for s in saved:
        r = Resource.query.get(s.resource_id)
        if not r:
            continue
        mod = Module.query.get(r.module_id) if r.module_id is not None else None
        out.append(
            {
                **_resource_to_dict(r),
                "saved_at": s.saved_at.isoformat(),
                "course_id": (mod.course_id if mod else None),
            }
        )
    return jsonify({"data": {"resources": out}, "error": None})


# --------------------
# Admin (create content)
# --------------------


@courses_bp.get("/subjects")
def list_subjects():
    subs = Subject.query.order_by(Subject.name.asc()).all()
    return jsonify({"data": [{"id": s.id, "name": s.name} for s in subs], "error": None})


@courses_bp.post("/admin/subjects")
@_require_roles(["moderator", "admin"])
def admin_create_subject():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name or len(name) < 2 or len(name) > 120:
        return _json_error("Subject name must be 2-120 characters", code="invalid_name")

    existing = Subject.query.filter_by(name=name).first()
    if existing:
        return jsonify({"data": {"subject_id": existing.id}, "error": None}), 200

    sub = Subject(name=name)
    db.session.add(sub)
    db.session.flush()
    db.session.commit()
    return jsonify({"data": {"subject_id": sub.id}, "error": None}), 201


@courses_bp.post("/admin/courses")
@_require_roles(["moderator", "admin"])
def admin_create_course():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip() or None
    subject_id = payload.get("subject_id", None)
    subject_name = (payload.get("subject_name") or "").strip() or None

    if not title or len(title) < 2 or len(title) > 220:
        return _json_error("Course title must be 2-220 characters", code="invalid_title")

    subject = None
    if subject_id is not None and str(subject_id).strip() != "":
        subject = Subject.query.get(int(subject_id))
        if not subject:
            return _json_error("subject_id not found", code="invalid_subject", status_code=404)
    elif subject_name:
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(name=subject_name)
            db.session.add(subject)
            db.session.flush()

    course = Course(title=title, description=description, subject_id=subject.id if subject else None)
    db.session.add(course)
    db.session.flush()
    db.session.commit()
    return jsonify({"data": {"course_id": course.id}, "error": None}), 201


@courses_bp.post("/admin/courses/<int:course_id>/modules")
@_require_roles(["moderator", "admin"])
def admin_create_module(course_id: int):
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    order_index = payload.get("order_index", 0)

    course = Course.query.get(course_id)
    if not course:
        return _json_error("Course not found", code="not_found", status_code=404)

    try:
        order_index = int(order_index)
    except Exception:
        return _json_error("order_index must be an integer", code="invalid_order_index")

    if not title or len(title) < 2 or len(title) > 220:
        return _json_error("Module title must be 2-220 characters", code="invalid_title")

    mod = Module(course_id=course_id, title=title, order_index=order_index)
    db.session.add(mod)
    db.session.flush()
    db.session.commit()
    return jsonify({"data": {"module_id": mod.id}, "error": None}), 201


@courses_bp.post("/admin/modules/<int:module_id>/resources")
@_require_roles(["moderator", "admin"])
def admin_create_resource(module_id: int):
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    resource_type = (payload.get("resource_type") or "").strip().lower()
    content_text = (payload.get("content_text") or "").strip() or None
    content_url = (payload.get("content_url") or "").strip() or None

    mod = Module.query.get(module_id)
    if not mod:
        return _json_error("Module not found", code="module_not_found", status_code=404)

    if not title or len(title) < 2 or len(title) > 220:
        return _json_error("Resource title must be 2-220 characters", code="invalid_title")

    if resource_type not in ("note", "video"):
        return _json_error("resource_type must be 'note' or 'video'", code="invalid_resource_type")

    if resource_type == "note":
        if not content_text:
            return _json_error("content_text is required for notes", code="missing_content_text")
        content_url = None
    else:
        if not content_url:
            return _json_error("content_url is required for videos", code="missing_content_url")
        content_text = None

    res = Resource(
        module_id=module_id,
        title=title,
        resource_type=resource_type,
        content_text=content_text,
        content_url=content_url,
    )
    db.session.add(res)
    db.session.flush()
    db.session.commit()
    return jsonify({"data": {"resource_id": res.id}, "error": None}), 201


@courses_bp.delete("/admin/resources/<int:resource_id>")
@_require_roles(["moderator", "admin"])
def admin_delete_resource(resource_id: int):
    res = Resource.query.get(resource_id)
    if not res:
        return _json_error("Resource not found", code="not_found", status_code=404)

    ResourceCompletion.query.filter_by(resource_id=resource_id).delete(synchronize_session=False)
    SavedResource.query.filter_by(resource_id=resource_id).delete(synchronize_session=False)
    db.session.delete(res)
    db.session.commit()
    return jsonify({"data": {"deleted": True, "resource_id": resource_id}, "error": None})


@courses_bp.patch("/admin/resources/<int:resource_id>")
@_require_roles(["moderator", "admin"])
def admin_update_resource(resource_id: int):
    r = Resource.query.get(resource_id)
    if not r:
        return _json_error("Resource not found", code="not_found", status_code=404)

    payload = request.get_json(silent=True) or {}

    title = payload.get("title")
    if title:
        r.title = title

    resource_type = payload.get("resource_type")
    if resource_type:
        r.resource_type = resource_type

    content_text = payload.get("content_text")
    if content_text is not None:
        r.content_text = content_text

    content_url = payload.get("content_url")
    if content_url is not None:
        r.content_url = content_url

    db.session.commit()
    return jsonify({"data": {"updated": True, "resource_id": r.id}, "error": None})


@courses_bp.delete("/admin/modules/<int:module_id>")
@_require_roles(["moderator", "admin"])
def admin_delete_module(module_id: int):
    mod = Module.query.get(module_id)
    if not mod:
        return _json_error("Module not found", code="not_found", status_code=404)

    resources = Resource.query.filter_by(module_id=module_id).all()
    resource_ids = [r.id for r in resources]
    if resource_ids:
        ResourceCompletion.query.filter(ResourceCompletion.resource_id.in_(resource_ids)).delete(synchronize_session=False)
        SavedResource.query.filter(SavedResource.resource_id.in_(resource_ids)).delete(synchronize_session=False)
        Resource.query.filter(Resource.id.in_(resource_ids)).delete(synchronize_session=False)

    db.session.delete(mod)
    db.session.commit()
    return jsonify({"data": {"deleted": True, "module_id": module_id}, "error": None})


@courses_bp.delete("/admin/courses/<int:course_id>")
@_require_roles(["moderator", "admin"])
def admin_delete_course(course_id: int):
    course = Course.query.get(course_id)
    if not course:
        return _json_error("Course not found", code="not_found", status_code=404)

    modules = Module.query.filter_by(course_id=course_id).all()
    module_ids = [m.id for m in modules]
    if module_ids:
        resources = Resource.query.filter(Resource.module_id.in_(module_ids)).all()
        resource_ids = [r.id for r in resources]
        if resource_ids:
            ResourceCompletion.query.filter(ResourceCompletion.resource_id.in_(resource_ids)).delete(synchronize_session=False)
            SavedResource.query.filter(SavedResource.resource_id.in_(resource_ids)).delete(synchronize_session=False)
            Resource.query.filter(Resource.id.in_(resource_ids)).delete(synchronize_session=False)
        Module.query.filter(Module.id.in_(module_ids)).delete(synchronize_session=False)

    db.session.delete(course)
    db.session.commit()
    return jsonify({"data": {"deleted": True, "course_id": course_id}, "error": None})


@courses_bp.delete("/admin/subjects/<int:subject_id>")
@_require_roles(["moderator", "admin"])
def admin_delete_subject(subject_id: int):
    sub = Subject.query.get(subject_id)
    if not sub:
        return _json_error("Subject not found", code="not_found", status_code=404)

    has_courses = Course.query.filter_by(subject_id=subject_id).first() is not None
    if has_courses:
        return _json_error(
            "Cannot delete subject with existing courses. Move/delete courses first.",
            code="subject_has_courses",
            status_code=409,
        )

    db.session.delete(sub)
    db.session.commit()
    return jsonify({"data": {"deleted": True, "subject_id": subject_id}, "error": None})


@courses_bp.patch("/admin/subjects/<int:subject_id>")
@_require_roles(["moderator", "admin"])
def admin_update_subject(subject_id: int):
    sub = Subject.query.get(subject_id)
    if not sub:
        return _json_error("Subject not found", code="not_found", status_code=404)

    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    if name and len(name.strip()) >= 2:
        sub.name = name.strip()

    db.session.commit()
    return jsonify({"data": {"updated": True, "subject_id": sub.id}, "error": None})


@courses_bp.patch("/admin/courses/<int:course_id>")
@_require_roles(["moderator", "admin"])
def admin_update_course(course_id: int):
    c = Course.query.get(course_id)
    if not c:
        return _json_error("Course not found", code="not_found", status_code=404)

    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    description = payload.get("description")
    
    if title and len(title.strip()) >= 2:
        c.title = title.strip()
    if "description" in payload:
        c.description = description.strip() if description else None

    db.session.commit()
    return jsonify({"data": {"updated": True, "course_id": c.id}, "error": None})


@courses_bp.patch("/admin/modules/<int:module_id>")
@_require_roles(["moderator", "admin"])
def admin_update_module(module_id: int):
    m = Module.query.get(module_id)
    if not m:
        return _json_error("Module not found", code="not_found", status_code=404)

    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    order_index = payload.get("order_index")

    if title and len(title.strip()) >= 2:
        m.title = title.strip()
    if order_index is not None:
        try:
            m.order_index = int(order_index)
        except ValueError:
            pass

    db.session.commit()
    return jsonify({"data": {"updated": True, "module_id": m.id}, "error": None})
