from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
import bcrypt as bcrypt_lib

from ..extensions import db
from ..models import Role, User, UserRole


auth_bp = Blueprint("auth", __name__)


def _json_error(message: str, code: str = "bad_request", status_code: int = 400):
    return jsonify({"data": None, "error": {"code": code, "message": message}}), status_code


def _get_user_roles_from_db(user_id: int):
    rows = (
        db.session.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    return sorted([r[0] for r in rows])


def _roles_claims_for_user(user_id: int):
    roles = _get_user_roles_from_db(user_id)
    if not roles:
        roles = ["student"]
    return roles


def _hash_password(password: str) -> str:
    # Bcrypt hashes are limited to 72 bytes per password. We validate earlier,
    # so hashing should be safe here.
    pw = password.encode("utf-8")
    salt = bcrypt_lib.gensalt()
    hashed = bcrypt_lib.hashpw(pw, salt)
    return hashed.decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    pw = password.encode("utf-8")
    hashed = password_hash.encode("utf-8")
    return bcrypt_lib.checkpw(pw, hashed)


def require_roles(*allowed_roles: str):
    # Decorator defined inline to keep this project scaffold simple.
    from functools import wraps
    from flask_jwt_extended import jwt_required

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_roles = claims.get("roles", [])
            if not any(r in user_roles for r in allowed_roles):
                return _json_error("Forbidden", code="forbidden", status_code=403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    display_name = (payload.get("display_name") or "").strip()

    if not email or "@" not in email:
        return _json_error("A valid email is required", code="invalid_email")
    if len(password) < 8:
        return _json_error("Password must be at least 8 characters", code="weak_password")
    # passlib+bcrypt enforces the 72-byte limit (in UTF-8); validate early.
    try:
        password_bytes_len = len(str(password).encode("utf-8"))
    except Exception:
        password_bytes_len = 999
    if password_bytes_len > 72:
        return _json_error("Password too long (max 72 bytes for bcrypt)", code="password_too_long")

    if User.query.filter_by(email=email).first():
        return _json_error("Email already registered", code="email_taken")

    student_role = Role.query.filter_by(name="student").first()
    if not student_role:
        student_role = Role(name="student")
        db.session.add(student_role)
        db.session.flush()

    user = User(
        email=email,
        password_hash=_hash_password(password),
        display_name=display_name or None,
        is_active=True,
    )
    db.session.add(user)
    db.session.flush()

    db.session.add(UserRole(user_id=user.id, role_id=student_role.id))
    db.session.commit()

    roles = _roles_claims_for_user(user.id)
    token = create_access_token(identity=str(user.id), additional_claims={"roles": roles})

    return jsonify({"data": {"access_token": token}, "error": None}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active:
        return _json_error("Invalid credentials", code="invalid_credentials", status_code=401)
    if not _verify_password(password, user.password_hash):
        return _json_error("Invalid credentials", code="invalid_credentials", status_code=401)

    roles = _roles_claims_for_user(user.id)
    token = create_access_token(identity=str(user.id), additional_claims={"roles": roles})
    return jsonify({"data": {"access_token": token}, "error": None}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    from flask_jwt_extended import get_jwt_identity

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user:
        return _json_error("User not found", code="user_not_found", status_code=404)

    roles = get_jwt().get("roles", _roles_claims_for_user(user.id))
    return jsonify(
        {
            "data": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "roles": roles,
            },
            "error": None,
        }
    )


@auth_bp.post("/forgot-password")
def forgot_password():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return _json_error("A valid email is required", code="invalid_email")
    return jsonify({"data": {"message": f"Password reset link sent to {email}"}, "error": None}), 200


@auth_bp.get("/admin/users")
@require_roles("admin")
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    out = []
    for u in users:
        roles = _get_user_roles_from_db(u.id)
        if not roles: roles = ["student"]
        out.append({
            "id": u.id,
            "email": u.email,
            "display_name": u.display_name,
            "roles": roles,
            "is_active": u.is_active
        })
    return jsonify({"data": out, "error": None}), 200


@auth_bp.patch("/admin/users/<int:user_id>/role")
@require_roles("admin")
def admin_update_user_role(user_id: int):
    payload = request.get_json(silent=True) or {}
    new_role = (payload.get("role") or "").strip().lower()
    
    if new_role not in ["student", "moderator", "admin"]:
        return _json_error("Invalid role", code="invalid_role")
        
    user = User.query.get(user_id)
    if not user:
        return _json_error("User not found", code="not_found", status_code=404)
        
    role_obj = Role.query.filter_by(name=new_role).first()
    if not role_obj:
        role_obj = Role(name=new_role)
        db.session.add(role_obj)
        db.session.flush()
        
    UserRole.query.filter_by(user_id=user.id).delete()
    db.session.add(UserRole(user_id=user.id, role_id=role_obj.id))
    db.session.commit()
    
    return jsonify({"data": {"message": f"Role updated to {new_role}"}, "error": None}), 200
