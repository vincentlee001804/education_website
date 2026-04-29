from datetime import datetime
from sqlalchemy import UniqueConstraint

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    roles = db.relationship("UserRole", back_populates="user", cascade="all, delete-orphan")


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)

    user_roles = db.relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(db.Model):
    __tablename__ = "user_roles"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="roles")
    role = db.relationship("Role", back_populates="user_roles")

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),)


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=True)


class Module(db.Model):
    __tablename__ = "modules"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"), nullable=False, index=True)
    title = db.Column(db.String(220), nullable=False)
    resource_type = db.Column(db.String(20), nullable=False)  # 'note' | 'video'
    content_text = db.Column(db.Text, nullable=True)  # for notes
    content_url = db.Column(db.String(500), nullable=True)  # for videos
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ResourceCompletion(db.Model):
    __tablename__ = "resource_completions"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), primary_key=True)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SavedResource(db.Model):
    __tablename__ = "saved_resources"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), primary_key=True)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ForumTopic(db.Model):
    __tablename__ = "forum_topics"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(220), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)  # active | hidden


class ForumPost(db.Model):
    __tablename__ = "forum_posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("forum_topics.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="visible", nullable=False)  # visible | hidden | deleted


class ForumReport(db.Model):
    __tablename__ = "forum_reports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey("forum_posts.id"), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    reason = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="open", nullable=False)  # open | resolved
    moderation_action = db.Column(db.String(50), nullable=True)
    moderated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class BookCategory(db.Model):
    __tablename__ = "book_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(220), nullable=False, index=True)
    author = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("book_categories.id"), nullable=True, index=True)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    image_url = db.Column(db.String(500), nullable=True)


class Inventory(db.Model):
    __tablename__ = "inventory"

    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), primary_key=True)
    stock_count = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Ebook(db.Model):
    __tablename__ = "ebooks"

    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), primary_key=True)
    pdf_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), default="active", nullable=False)  # active | checked_out
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "status", name="uq_cart_user_active"),)


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price_snapshot = db.Column(db.Numeric(10, 2), nullable=False, default=0)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), default="paid", nullable=False)  # paid | cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price_snapshot = db.Column(db.Numeric(10, 2), nullable=False, default=0)

