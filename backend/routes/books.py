import os
import uuid
from decimal import Decimal

from flask import Blueprint, jsonify, request, send_file, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from passlib.hash import bcrypt
from werkzeug.utils import secure_filename

from ..config import Config
from ..extensions import db
from ..models import (
    Book,
    BookCategory,
    Cart,
    CartItem,
    Ebook,
    Inventory,
    Order,
    OrderItem,
)


books_bp = Blueprint("books", __name__)


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


def _decimal_to_float(x) -> float:
    if x is None:
        return 0.0
    if isinstance(x, Decimal):
        return float(x)
    return float(x)


def _book_to_dict(b: Book, category_name: str | None = None):
    return {
        "id": b.id,
        "title": b.title,
        "author": b.author,
        "description": b.description,
        "category": category_name,
        "category_id": b.category_id,
        "price": _decimal_to_float(b.price),
        "image_url": b.image_url,
    }


def _get_or_create_active_cart(user_id: int) -> Cart:
    cart = Cart.query.filter_by(user_id=user_id, status="active").first()
    if cart:
        return cart
    cart = Cart(user_id=user_id, status="active")
    db.session.add(cart)
    db.session.commit()
    return cart


def _uploads_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path


def _validate_image(file_storage):
    if not file_storage:
        return False
    if not (file_storage.mimetype or "").startswith("image/"):
        return False
    return True


def _validate_pdf(file_storage):
    if not file_storage:
        return False
    ct = (file_storage.mimetype or "").lower()
    return ct == "application/pdf" or ct.endswith("/pdf")


@books_bp.get("/books")
def list_books():
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", type=int)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)

    q = Book.query
    if category_id is not None:
        q = q.filter(Book.category_id == category_id)
    if search:
        q = q.filter(Book.title.ilike(f"%{search}%"))
    if min_price is not None:
        q = q.filter(Book.price >= min_price)
    if max_price is not None:
        q = q.filter(Book.price <= max_price)

    books = q.order_by(Book.id.desc()).limit(100).all()
    categories = {c.id: c.name for c in BookCategory.query.all()}

    return jsonify({"data": [_book_to_dict(b, categories.get(b.category_id)) for b in books], "error": None})


@books_bp.get("/books/<int:book_id>")
def get_book(book_id: int):
    b = Book.query.get(book_id)
    if not b:
        return _json_error("Book not found", code="not_found", status_code=404)
    cat = BookCategory.query.get(b.category_id)
    return jsonify({"data": _book_to_dict(b, cat.name if cat else None), "error": None})


@books_bp.get("/books/categories")
def list_categories():
    cats = BookCategory.query.order_by(BookCategory.name.asc()).all()
    return jsonify({"data": [{"id": c.id, "name": c.name} for c in cats], "error": None})


@books_bp.get("/cart")
@jwt_required()
def get_cart():
    user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=user_id, status="active").first()
    if not cart:
        return jsonify({"data": {"items": [], "total": 0.0, "cart_id": None}, "error": None})

    items = CartItem.query.filter_by(cart_id=cart.id).all()
    categories = {c.id: c.name for c in BookCategory.query.all()}

    total = Decimal("0.00")
    out_items = []
    for it in items:
        b = Book.query.get(it.book_id)
        if not b:
            continue
        line_total = Decimal(it.unit_price_snapshot) * it.quantity
        total += line_total
        out_items.append(
            {
                "id": it.id,
                "book_id": it.book_id,
                "title": b.title,
                "category": categories.get(b.category_id),
                "price": _decimal_to_float(it.unit_price_snapshot),
                "quantity": it.quantity,
                "line_total": _decimal_to_float(line_total),
                "image_url": b.image_url,
            }
        )

    return jsonify({"data": {"cart_id": cart.id, "items": out_items, "total": _decimal_to_float(total)}, "error": None})


@books_bp.post("/cart/items")
@jwt_required()
def add_to_cart():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    book_id = payload.get("book_id")
    quantity = payload.get("quantity", 1)

    try:
        book_id = int(book_id)
        quantity = int(quantity)
    except Exception:
        return _json_error("Invalid book_id/quantity", code="invalid_payload")
    if quantity < 1 or quantity > 99:
        return _json_error("Quantity out of range", code="invalid_quantity")

    b = Book.query.get(book_id)
    if not b:
        return _json_error("Book not found", code="not_found", status_code=404)

    cart = _get_or_create_active_cart(user_id)
    existing = CartItem.query.filter_by(cart_id=cart.id, book_id=book_id).first()
    if existing:
        existing.quantity = min(99, existing.quantity + quantity)
    else:
        existing = CartItem(
            cart_id=cart.id,
            book_id=book_id,
            quantity=quantity,
            unit_price_snapshot=b.price,
        )
        db.session.add(existing)
    db.session.commit()
    return jsonify({"data": {"added": True, "cart_item_id": existing.id}, "error": None}), 201


@books_bp.patch("/cart/items/<int:item_id>")
@jwt_required()
def update_cart_item(item_id: int):
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    quantity = payload.get("quantity", None)
    try:
        quantity = int(quantity)
    except Exception:
        return _json_error("Invalid quantity", code="invalid_quantity")
    if quantity < 1 or quantity > 99:
        return _json_error("Quantity out of range", code="invalid_quantity")

    item = CartItem.query.get(item_id)
    if not item:
        return _json_error("Cart item not found", code="not_found", status_code=404)

    cart = Cart.query.get(item.cart_id)
    if not cart or cart.user_id != user_id or cart.status != "active":
        return _json_error("Forbidden", code="forbidden", status_code=403)

    item.quantity = quantity
    db.session.commit()
    return jsonify({"data": {"updated": True}, "error": None})


@books_bp.delete("/cart/items/<int:item_id>")
@jwt_required()
def delete_cart_item(item_id: int):
    user_id = int(get_jwt_identity())
    item = CartItem.query.get(item_id)
    if not item:
        return _json_error("Cart item not found", code="not_found", status_code=404)
    cart = Cart.query.get(item.cart_id)
    if not cart or cart.user_id != user_id or cart.status != "active":
        return _json_error("Forbidden", code="forbidden", status_code=403)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"data": {"deleted": True}, "error": None})


@books_bp.post("/checkout")
@jwt_required()
def checkout():
    user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=user_id, status="active").first()
    if not cart:
        return _json_error("Cart is empty", code="cart_empty", status_code=400)

    items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not items:
        return _json_error("Cart is empty", code="cart_empty", status_code=400)

    # Validate inventory
    for it in items:
        inv = Inventory.query.get(it.book_id)
        if not inv or inv.stock_count < it.quantity:
            return _json_error("Insufficient stock for one or more items", code="insufficient_stock", status_code=409)

    total = Decimal("0.00")
    for it in items:
        total += Decimal(it.unit_price_snapshot) * it.quantity

    # Commit as a single transaction
    for it in items:
        inv = Inventory.query.get(it.book_id)
        inv.stock_count -= it.quantity

    order = Order(user_id=user_id, total_amount=total, status="paid")
    db.session.add(order)
    db.session.flush()  # get order.id

    for it in items:
        db.session.add(
            OrderItem(
                order_id=order.id,
                book_id=it.book_id,
                quantity=it.quantity,
                unit_price_snapshot=it.unit_price_snapshot,
            )
        )

    cart.status = "checked_out"
    db.session.commit()

    return jsonify({"data": {"order_id": order.id, "total": _decimal_to_float(order.total_amount), "status": order.status}, "error": None}), 201


@books_bp.get("/orders")
@jwt_required()
def list_orders():
    user_id = int(get_jwt_identity())
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).limit(50).all()

    out = []
    for o in orders:
        items = OrderItem.query.filter_by(order_id=o.id).all()
        out_items = []
        for it in items:
            b = Book.query.get(it.book_id)
            out_items.append(
                {
                    "book_id": it.book_id,
                    "title": b.title if b else None,
                    "quantity": it.quantity,
                    "price": _decimal_to_float(it.unit_price_snapshot),
                }
            )
        out.append(
            {
                "order_id": o.id,
                "created_at": o.created_at.isoformat(),
                "status": o.status,
                "total_amount": _decimal_to_float(o.total_amount),
                "items": out_items,
            }
        )
    return jsonify({"data": out, "error": None})


@books_bp.get("/ebooks")
@jwt_required()
def list_ebooks():
    user_id = int(get_jwt_identity())

    # Books purchased via paid orders
    paid_orders = Order.query.filter_by(user_id=user_id, status="paid").all()
    paid_order_ids = [o.id for o in paid_orders]
    if not paid_order_ids:
        return jsonify({"data": [], "error": None})

    order_items = OrderItem.query.filter(OrderItem.order_id.in_(paid_order_ids)).all()
    book_ids = {it.book_id for it in order_items}

    ebooks = Ebook.query.filter(Ebook.book_id.in_(book_ids)).all()
    out = []
    for e in ebooks:
        b = Book.query.get(e.book_id)
        out.append(
            {
                "book_id": e.book_id,
                "title": b.title if b else None,
                "author": b.author if b else None,
                "image_url": b.image_url if b else None,
                "download_ready": True,
            }
        )
    return jsonify({"data": out, "error": None})


@books_bp.get("/ebooks/<int:book_id>/download")
@jwt_required()
def download_ebook(book_id: int):
    user_id = int(get_jwt_identity())

    # Verify ownership through paid orders
    owned = (
        OrderItem.query.join(Order, OrderItem.order_id == Order.id)
        .filter(Order.user_id == user_id, Order.status == "paid", OrderItem.book_id == book_id)
        .first()
    )
    if not owned:
        return _json_error("Ebook not found for this user", code="not_owned", status_code=404)

    e = Ebook.query.get(book_id)
    if not e:
        return _json_error("Ebook PDF not available", code="ebook_missing", status_code=404)

    if not os.path.isfile(e.pdf_path):
        return _json_error("Ebook file missing on server", code="file_missing", status_code=500)

    return send_file(
        e.pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=e.original_filename or f"ebook_{book_id}.pdf",
    )


@books_bp.get("/uploads/book-images/<path:filename>")
def public_book_image(filename: str):
    # Public read for images.
    # Stored names are uuid-based so traversal risk is low; still we keep it in the target directory.
    safe_name = os.path.basename(filename)
    img_dir = Config.BOOK_IMAGE_DIR
    if not os.path.isfile(os.path.join(img_dir, safe_name)):
        return _json_error("Image not found", code="not_found", status_code=404)
    return send_from_directory(img_dir, safe_name)


@books_bp.post("/admin/books")
@_require_roles(["moderator", "admin"])
def admin_create_book():
    payload = request.get_json(silent=True) or {}

    title = (payload.get("title") or "").strip()
    author = (payload.get("author") or "").strip() or None
    description = (payload.get("description") or "").strip() or None
    price = payload.get("price", None)
    stock_count = payload.get("stock_count", 0)
    category_id = payload.get("category_id", None)
    category_name = (payload.get("category_name") or "").strip() or None

    if not title or len(title) < 2 or len(title) > 220:
        return _json_error("Invalid title", code="invalid_title")
    try:
        price = Decimal(str(price))
    except Exception:
        return _json_error("Invalid price", code="invalid_price")
    if price < 0:
        return _json_error("Price must be >= 0", code="invalid_price")
    try:
        stock_count = int(stock_count)
    except Exception:
        return _json_error("Invalid stock_count", code="invalid_stock")
    if stock_count < 0:
        return _json_error("stock_count must be >= 0", code="invalid_stock")

    category = None
    if category_id is not None:
        category = BookCategory.query.get(int(category_id))
        if not category:
            return _json_error("category_id not found", code="invalid_category", status_code=404)
    elif category_name:
        category = BookCategory.query.filter_by(name=category_name).first()
        if not category:
            category = BookCategory(name=category_name)
            db.session.add(category)
            db.session.flush()
    else:
        return _json_error("Provide category_id or category_name", code="missing_category")

    b = Book(
        title=title,
        author=author,
        description=description,
        category_id=category.id,
        price=price,
        image_url=None,
    )
    db.session.add(b)
    db.session.flush()

    db.session.add(Inventory(book_id=b.id, stock_count=stock_count))
    db.session.commit()

    return jsonify({"data": {"book_id": b.id}, "error": None}), 201


@books_bp.post("/admin/books/<int:book_id>/image")
@_require_roles(["moderator", "admin"])
def admin_upload_book_image(book_id: int):
    b = Book.query.get(book_id)
    if not b:
        return _json_error("Book not found", code="not_found", status_code=404)

    if "file" not in request.files:
        return _json_error("Missing file field", code="missing_file")

    file = request.files["file"]
    if not _validate_image(file):
        return _json_error("Invalid image type", code="invalid_image", status_code=400)

    uploads = _uploads_dir(Config.BOOK_IMAGE_DIR)
    ext = os.path.splitext(secure_filename(file.filename or ""))[-1].lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(uploads, filename)
    file.save(save_path)

    b.image_url = f"/api/uploads/book-images/{filename}"
    db.session.commit()
    return jsonify({"data": {"image_url": b.image_url}, "error": None}), 201


@books_bp.post("/admin/books/<int:book_id>/ebook")
@_require_roles(["moderator", "admin"])
def admin_upload_ebook_pdf(book_id: int):
    b = Book.query.get(book_id)
    if not b:
        return _json_error("Book not found", code="not_found", status_code=404)

    if "file" not in request.files:
        return _json_error("Missing file field", code="missing_file")

    file = request.files["file"]
    if not _validate_pdf(file):
        return _json_error("Only PDF is allowed for ebooks", code="invalid_pdf", status_code=400)

    uploads = _uploads_dir(Config.EBOOK_PDF_DIR)
    filename = f"{uuid.uuid4().hex}.pdf"
    save_path = os.path.join(uploads, filename)
    file.save(save_path)

    size = None
    try:
        size = os.path.getsize(save_path)
    except Exception:
        size = None

    ebook = Ebook.query.get(book_id)
    if not ebook:
        ebook = Ebook(book_id=book_id, pdf_path=save_path, original_filename=None, file_size_bytes=size)
        db.session.add(ebook)
    else:
        ebook.pdf_path = save_path
        ebook.file_size_bytes = size

    ebook.original_filename = secure_filename(file.filename or "") or ebook.original_filename
    db.session.commit()
    return jsonify({"data": {"ebook_saved": True}, "error": None}), 201

