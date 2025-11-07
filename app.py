from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "change-me"  # for flash messages

# ---- Simple in-memory "DB" (swap with real DB later) ----
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
        "image": "images/sample_headphones.jpg",
        "location": "Pune",
        "distance_miles": 2.3,
        "created_at": datetime.utcnow(),
    },
    {
        "id": "p2",
        "title": "Wooden Coffee Table",
        "price": 5499.00,
        "category": "furniture",
        "image": "images/sample_table.jpg",
        "location": "Mumbai",
        "distance_miles": 18.5,
        "created_at": datetime.utcnow(),
    },
]

WATCHLIST = set()  # store product IDs
MESSAGES = [
    {"from": "Aarav", "preview": "Is it still available?", "time": "10:24"},
    {"from": "Diya", "preview": "Can you ship to Pune?", "time": "09:11"},
]

UPLOAD_DIR = os.path.join("static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------

@app.context_processor
def inject_globals():
    return {
        "categories": CATEGORIES,
        "now": datetime.utcnow(),
    }

@app.route("/")
def home():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", "").strip()
    items = PRODUCTS
    if q:
        items = [p for p in items if q.lower() in p["title"].lower()]
    if cat:
        items = [p for p in items if p["category"] == cat]
    return render_template("index.html",
                           products=items,
                           q=q,
                           current_category=cat,
                           watchlist=WATCHLIST,
                           messages=MESSAGES)

@app.route("/product/<pid>")
def product_detail(pid):
    prod = next((p for p in PRODUCTS if p["id"] == pid), None)
    if not prod:
        flash("Product not found.", "error")
        return redirect(url_for("home"))
    return render_template("index.html",
                           products=[prod],
                           detail_view=True,
                           watchlist=WATCHLIST,
                           messages=MESSAGES)

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

@app.route("/sell", methods=["POST"])
def sell():
    title = request.form.get("title", "").strip()
    price = request.form.get("price", "").strip()
    category = request.form.get("category", "").strip()
    location = request.form.get("location", "").strip()
    image_path = None

    if "image" in request.files and request.files["image"].filename:
        f = request.files["image"]
        fname = secure_filename(f"{uuid4().hex}_{f.filename}")
        save_path = os.path.join(UPLOAD_DIR, fname)
        f.save(save_path)
        image_path = f"uploads/{fname}"

    try:
        price_val = float(price)
    except ValueError:
        flash("Invalid price.", "error")
        return redirect(url_for("home"))

    pid = uuid4().hex[:8]
    PRODUCTS.append({
        "id": pid,
        "title": title or "Untitled Item",
        "price": price_val,
        "category": category or "electronics",
        "image": f"images/placeholder.jpg" if not image_path else image_path,
        "location": location or "Unknown",
        "distance_miles": 1.0,
        "created_at": datetime.utcnow(),
    })
    flash("Item listed successfully!", "success")
    return redirect(url_for("product_detail", pid=pid))

@app.route("/feedback", methods=["POST"])
def feedback():
    name = request.form.get("name", "").strip()
    message = request.form.get("message", "").strip()
    # In real app: save to DB / send email
    flash("Thanks for the feedback!", "success")
    return redirect(url_for("home"))

@app.route("/settings", methods=["POST"])
def settings():
    # Persist theme/lang/etc. in DB/session in a real app
    flash("Settings saved.", "success")
    return redirect(url_for("home"))

# Helper route for category pages (optional deep link)
@app.route("/category/<slug>")
def category(slug):
    items = [p for p in PRODUCTS if p["category"] == slug]
    return render_template("index.html",
                           products=items,
                           current_category=slug,
                           watchlist=WATCHLIST,
                           messages=MESSAGES)

if __name__ == "__main__":
    # Run like: python app.py  (then open http://127.0.0.1:5000)
    app.run(debug=True)
