from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "change-me"

# -------------------- BASIC IN-MEMORY DATA --------------------
CATEGORIES = [
    {"slug": "electronics", "name": "Electronics"},
    {"slug": "furniture", "name": "Furniture"},
    {"slug": "vehicles", "name": "Vehicles"},
    {"slug": "apparel", "name": "Apparel & Accessories"},
    {"slug": "home-garden", "name": "Home & Garden"},
    {"slug": "sporting", "name": "Sporting"},
    {"slug": "collectibles", "name": "Collectibles & Antiques"},
]

PRODUCTS = [
    {
        "id": "p1",
        "title": "Wireless Headphones",
        "price": 3200.00,
        "category": "electronics",
        "image": "Images/item_4.jpeg",  # from /Assets/Images
        "location": "Pune",
        "distance_miles": 2.3,
        "created_at": datetime.utcnow(),
    },
    {
        "id": "p2",
        "title": "Wooden Coffee Table",
        "price": 5499.00,
        "category": "furniture",
        "image": "Images/sample_table.jpg",  # from /Assets/Images
        "location": "Mumbai",
        "distance_miles": 18.5,
        "created_at": datetime.utcnow(),
    },
]

WATCHLIST = set()
MESSAGES = [
    {"from": "Aarav", "preview": "Is it still available?", "time": "10:24"},
    {"from": "Diya", "preview": "Can you ship to Pune?", "time": "09:11"},
]

UPLOAD_DIR = os.path.join("static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------

@app.context_processor
def inject_globals():
    return {"categories": CATEGORIES, "now": datetime.utcnow()}

# -------------------- STATIC ROUTES --------------------

# Serve /Assets/... (your custom assets folder)
@app.route('/Assets/<path:filename>/')
def serve_assets(filename):
    assets_dir = os.path.join(app.root_path, 'Assets')
    return send_from_directory(assets_dir, filename)

def resolve_image_path(img):
    if img.startswith("uploads/"):  # user upload
        return url_for("static", filename=img, _external=True)
    elif img.startswith("Images/") or img.startswith("images/"):  # asset
        return url_for("serve_assets", filename=img, _external=True)
    else:
        return img

# -------------------- FRONTEND HOME --------------------

@app.route("/")
def home():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", "").strip()
    items = PRODUCTS
    if q:
        items = [p for p in items if q.lower() in p["title"].lower()]
    if cat:
        items = [p for p in items if p["category"] == cat]
    return render_template(
        "index.html",
        products=items,
        q=q,
        current_category=cat,
        watchlist=WATCHLIST,
        messages=MESSAGES
    )

# -------------------- PRODUCT FEED --------------------

@app.route("/products/feed")
def product_feed():
    category = request.args.get("category", "").strip().lower()
    items = PRODUCTS
    if category:
        items = [p for p in items if p["category"].lower() == category]

    def resolve_image_path(img):
        """Return correct URL based on where image lives."""
        if img.startswith("uploads/"):  # user-uploaded file
            return url_for("static", filename=img)
        elif img.startswith("Images/") or img.startswith("images/"):  # app asset
            return url_for("serve_assets", filename=img)
        else:  # fallback
            return img

    products_data = []
    for p in items:
        raw_images = p.get("images", [p.get("image", "Images/placeholder.jpeg")])
        images = [resolve_image_path(img) for img in raw_images]

        products_data.append({
            "product_id": p["id"],
            "title": p["title"],
            "price": p["price"],
            "category": p["category"],
            "condition": p.get("condition", "Unknown"),
            "images": images,
            "location": p["location"],
        })

    return jsonify({"ok": True, "products": products_data})

# -------------------- PRODUCT DETAILS --------------------

@app.route("/products/<pid>")
def product_detail_api(pid):
    prod = next((p for p in PRODUCTS if p["id"] == pid), None)
    if not prod:
        return jsonify({"ok": False, "error": "Product not found"}), 404

    def resolve_image_path(img):
        if img.startswith("uploads/"):
            return url_for("static", filename=img)
        elif img.startswith("Images/") or img.startswith("images/"):
            return url_for("serve_assets", filename=img)
        else:
            return img

    raw_images = prod.get("images", [prod.get("image", "Images/placeholder.jpeg")])
    images = [resolve_image_path(img) for img in raw_images]

    product_data = {
        "product_id": prod["id"],
        "title": prod["title"],
        "price": prod["price"],
        "category": prod["category"],
        "condition": prod.get("condition", "Unknown"),
        "location": prod["location"],
        "description": prod.get("description", "No description provided."),
        "seller_name": "Demo Seller",
        "seller_contact": "+91 9999999999",
        "views": prod.get("views", 0),
        "images": images,
    }

    return jsonify({
        "ok": True,
        "product": product_data,
        "blockchain_verified": True
    })

# -------------------- PRODUCT ACTIVATION --------------------

@app.route("/products/activate/<pid>", methods=["POST"])
def activate_product(pid):
    prod = next((p for p in PRODUCTS if p["id"] == pid), None)
    if not prod:
        return jsonify({"ok": False, "error": "Product not found"}), 404

    prod["status"] = "active"
    prod["activated_at"] = datetime.utcnow()
    prod["blockchain_verified"] = True

    return jsonify({
        "ok": True,
        "status": "active",
        "product_id": pid,
        "message": f"Product {pid} activated successfully",
        "blockchain_verified": True,
        "activated_at": prod["activated_at"].isoformat() + "Z"
    }), 200

# -------------------- WATCHLIST --------------------

@app.route("/watchlist/toggle/<pid>", methods=["POST"])
def toggle_watchlist(pid):
    if pid in WATCHLIST:
        WATCHLIST.remove(pid)
        status = "removed"
    else:
        WATCHLIST.add(pid)
        status = "added"

    if request.headers.get("Accept") == "application/json":
        return jsonify({"ok": True, "status": status, "count": len(WATCHLIST)})

    flash(f"Watchlist {status}.", "success")
    return redirect(request.referrer or url_for("home"))

# -------------------- SELL / LIST PRODUCT --------------------

@app.route("/sell", methods=["POST"])
def sell():
    title = request.form.get("title", "").strip()
    price = request.form.get("price", "").strip()
    category = request.form.get("category", "").strip()
    location = request.form.get("location", "").strip()
    condition = request.form.get("condition", "").strip()

    issues = []
    if not title: issues.append("Title is required.")
    if not price: issues.append("Price is required.")
    if not category: issues.append("Category is required.")
    if not location: issues.append("Location is required.")
    if not condition: issues.append("Condition is required.")

    if issues:
        return jsonify({"ok": False, "issues": issues}), 400

    try:
        price_val = float(price)
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid price format."}), 400

    # Handle multiple image uploads
    image_paths = []
    if "images" in request.files:
        files = request.files.getlist("images")
        for f in files:
            if f.filename:
                fname = secure_filename(f"{uuid4().hex}_{f.filename}")
                save_path = os.path.join(UPLOAD_DIR, fname)
                f.save(save_path)
                image_paths.append(f"uploads/{fname}")

    if not image_paths:
        image_paths = ["Images/placeholder.jpeg"]

    pid = uuid4().hex[:8]
    PRODUCTS.append({
        "id": pid,
        "title": title,
        "price": price_val,
        "category": category,
        "condition": condition,
        "images": image_paths,
        "location": location,
        "distance_miles": 1.0,
        "created_at": datetime.utcnow(),
    })

    qr_code_url = f"/static/qrcodes/{pid}.png"

    return jsonify({
        "ok": True,
        "status": "listed",
        "product_id": pid,
        "message": "Product listed successfully",
        "nano_tag": {"qr_code": qr_code_url}
    }), 200

# -------------------- MISC ROUTES --------------------

@app.route("/feedback", methods=["POST"])
def feedback():
    name = request.form.get("name", "").strip()
    message = request.form.get("message", "").strip()
    flash("Thanks for the feedback!", "success")
    return redirect(url_for("home"))

@app.route("/settings", methods=["POST"])
def settings():
    flash("Settings saved.", "success")
    return redirect(url_for("home"))

@app.route("/category/<slug>")
def category(slug):
    items = [p for p in PRODUCTS if p["category"] == slug]
    return render_template(
        "index.html",
        products=items,
        current_category=slug,
        watchlist=WATCHLIST,
        messages=MESSAGES
    )

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True)
