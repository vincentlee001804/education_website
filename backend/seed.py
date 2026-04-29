import argparse

import bcrypt as bcrypt_lib

from .app import create_app
from .extensions import db
from .models import Role, User, UserRole


def ensure_roles():
    desired = ["student", "moderator", "admin"]
    for role_name in desired:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name))
    db.session.commit()


def create_user(email: str, password: str, display_name: str, roles: list[str]):
    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()
    if user:
        return user

    hashed = bcrypt_lib.hashpw(password.encode("utf-8"), bcrypt_lib.gensalt()).decode("utf-8")
    user = User(email=email, password_hash=hashed, display_name=display_name, is_active=True)
    db.session.add(user)
    db.session.flush()

    for role_name in roles:
        r = Role.query.filter_by(name=role_name).first()
        if r:
            db.session.add(UserRole(user_id=user.id, role_id=r.id))

    db.session.commit()
    return user


def main():
    parser = argparse.ArgumentParser(description="Seed initial roles/users for development/testing.")
    parser.add_argument("--email", required=True, help="Admin/mod email")
    parser.add_argument("--password", required=True, help="Admin/mod password")
    parser.add_argument("--display-name", default="Admin User", help="Display name")
    parser.add_argument("--roles", default="admin", help="Comma-separated roles (student,moderator,admin)")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        ensure_roles()
        roles = [r.strip() for r in args.roles.split(",") if r.strip()]
        create_user(args.email, args.password, args.display_name, roles)

    print("Seed complete.")


if __name__ == "__main__":
    main()

