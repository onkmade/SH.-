from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from uuid import uuid4
import json
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this-in-production"

# -------------------- CONFIGURATION --------------------
UPLOAD_DIR = os.path.join("static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------- IN-MEMORY DATA STRUCTURES --------------------
CATEGORIES = [
    {"slug": "electronics", "name": "Electronics"},
    {"slug": "furniture", "name": "Furniture"},
    {"slug": "vehicles", "name": "Vehicles"},
    {"slug": "apparel", "name": "Apparel & Accessories"},
    {"slug": "home-garden", "name": "Home & Garden"},
    {"slug": "sporting", "name": "Sporting"},
    {"slug": "collectibles", "name": "Collectibles & Antiques"},
]

# Sample products with proper image paths
PRODUCTS = [
    {
        "id": "p1",
        "title": "Wireless Headphones",
        "price": 3200.00,
        "category": "electronics",
        "condition": "Like New",
        "description": "High-quality wireless headphones with noise cancellation. Barely used, in excellent condition.",
        "images": ["Images/item_4.jpeg"],
        "location": "Pune",
        "distance_miles": 2.3,
        "views": 45,
        "seller_name": "Demo Seller",
        "seller_contact": "+91 9999999999",
        "seller_id": "seller1",
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
        "blockchain_verified": True,
    },
    {
        "id": "p2",
        "title": "Wooden Coffee Table",
        "price": 5499.00,
        "category": "furniture",
        "condition": "Good",
        "description": "Solid wood coffee table with minor wear. Perfect for living rooms.",
        "images": ["Images/item_2.jpeg"],
        "location": "Mumbai",
        "distance_miles": 18.5,
        "views": 32,
        "seller_name": "Demo Seller",
        "seller_contact": "+91 9999999999",
        "seller_id": "seller1",
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
        "blockchain_verified": True,
    },
]

USERS = {}  # {email: {password_hash, name, id, created_at}}
WATCHLIST = {}  # {user_id: [product_ids]}
MESSAGES = []

# -------------------- HELPER FUNCTIONS --------------------

def get_current_user():
    """Get current logged-in user from session"""
    user_id = session.get('user_id')
    if user_id:
        for email, user_data in USERS.items():
            if user_data['id'] == user_id:
                return {
                    'id': user_data['id'],
                    'email': email,
                    'name': user_data.get('name', email.split('@')[0])
                }
    return None

def generate_qr_code(product_id):
    """Generate a simple base64 QR code placeholder"""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"Product ID: {product_id}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    except ImportError:
        # Fallback if qrcode not installed
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

def resolve_image_path(img):
    """Return correct URL based on where image lives"""
    if not img:
        return url_for("serve_assets", filename="Images/placeholder.jpeg")
    if img.startswith("uploads/"):
        return url_for("static", filename=img)
    elif img.startswith("Images/") or img.startswith("images/"):
        return url_for("serve_assets", filename=img)
    else:
        return img

# -------------------- CONTEXT PROCESSOR --------------------

@app.context_processor
def inject_globals():
    return {
        "categories": CATEGORIES,
        "now": datetime.utcnow(),
        "current_user": get_current_user()
    }

# -------------------- STATIC ROUTES --------------------

@app.route('/Assets/<path:filename>')
def serve_assets(filename):
    """Serve files from Assets directory"""
    assets_dir = os.path.join(app.root_path, 'Assets')
    return send_from_directory(assets_dir, filename)

# -------------------- AUTHENTICATION --------------------

@app.route("/auth/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", email.split("@")[0])

    if not email or not password:
        return jsonify({"ok": False, "error": "Email and password required"}), 400

    if email in USERS:
        return jsonify({"ok": False, "error": "User already exists"}), 400

    user_id = uuid4().hex[:12]
    USERS[email] = {
        "id": user_id,
        "password_hash": generate_password_hash(password),
        "name": name,
        "created_at": datetime.utcnow().isoformat()
    }
    WATCHLIST[user_id] = []

    session['user_id'] = user_id
    return jsonify({
        "ok": True,
        "user_id": user_id,
        "email": email,
        "name": name,
        "message": "Registration successful"
    }), 200

@app.route("/auth/login", methods=["POST"])
def login():
    """Login user"""
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"ok": False, "error": "Email and password required"}), 400

    user = USERS.get(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"ok": False, "error": "Invalid credentials"}), 401

    session['user_id'] = user['id']
    return jsonify({
        "ok": True,
        "user_id": user['id'],
        "email": email,
        "name": user.get('name', email.split('@')[0]),
        "message": "Login successful"
    }), 200

@app.route("/auth/logout", methods=["POST"])
def logout():
    """Logout user"""
    session.pop('user_id', None)
    return jsonify({"ok": True, "message": "Logged out successfully"}), 200

@app.route("/auth/me", methods=["GET"])
def get_current_user_info():
    """Get current user info"""
    user = get_current_user()
    if user:
        return jsonify({"ok": True, "user": user}), 200
    return jsonify({"ok": False, "error": "Not authenticated"}), 401

# -------------------- FRONTEND HOME --------------------

@app.route("/")
def home():
    """Main home page"""
    return render_template("index.html")

# -------------------- PRODUCT FEED --------------------

@app.route("/products/feed")
def product_feed():
    """Get product feed with optional category filter"""
    category = request.args.get("category", "").strip().lower()
    search_query = request.args.get("q", "").strip().lower()
    
    items = PRODUCTS.copy()
    
    # Filter by category
    if category:
        items = [p for p in items if p["category"].lower() == category]
    
    # Filter by search query
    if search_query:
        items = [p for p in items if search_query in p["title"].lower() or search_query in p.get("description", "").lower()]
    
    # Sort by created_at (newest first)
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    products_data = []
    for p in items:
        raw_images = p.get("images", ["Images/placeholder.jpeg"])
        images = [resolve_image_path(img) for img in raw_images]

        products_data.append({
            "product_id": p["id"],
            "title": p["title"],
            "price": p["price"],
            "category": p["category"],
            "condition": p.get("condition", "Unknown"),
            "images": images,
            "location": p["location"],
            "views": p.get("views", 0),
            "status": p.get("status", "active"),
        })

    return jsonify({"ok": True, "products": products_data})

# -------------------- PRODUCT DETAILS --------------------

@app.route("/products/<pid>")
def product_detail_api(pid):
    """Get detailed product information"""
    prod = next((p for p in PRODUCTS if p["id"] == pid), None)
    if not prod:
        return jsonify({"ok": False, "error": "Product not found"}), 404

    # Increment view count
    prod["views"] = prod.get("views", 0) + 1

    raw_images = prod.get("images", ["Images/placeholder.jpeg"])
    images = [resolve_image_path(img) for img in raw_images]

    product_data = {
        "product_id": prod["id"],
        "title": prod["title"],
        "price": prod["price"],
        "category": prod["category"],
        "condition": prod.get("condition", "Unknown"),
        "location": prod["location"],
        "description": prod.get("description", "No description provided."),
        "seller_name": prod.get("seller_name", "Anonymous"),
        "seller_contact": prod.get("seller_contact", "N/A"),
        "views": prod.get("views", 0),
        "images": images,
        "status": prod.get("status", "active"),
        "created_at": prod.get("created_at", datetime.utcnow().isoformat()),
    }

    return jsonify({
        "ok": True,
        "product": product_data,
        "blockchain_verified": prod.get("blockchain_verified", True)
    })

# -------------------- PRODUCT ACTIVATION --------------------

@app.route("/products/activate/<pid>", methods=["POST"])
def activate_product(pid):
    """Activate a product listing"""
    prod = next((p for p in PRODUCTS if p["id"] == pid), None)
    if not prod:
        return jsonify({"ok": False, "error": "Product not found"}), 404

    prod["status"] = "active"
    prod["activated_at"] = datetime.utcnow().isoformat()
    prod["blockchain_verified"] = True

    return jsonify({
        "ok": True,
        "status": "active",
        "product_id": pid,
        "message": f"Product {pid} activated successfully",
        "blockchain_verified": True,
        "activated_at": prod["activated_at"]
    }), 200

# -------------------- WATCHLIST --------------------

@app.route("/watchlist/toggle/<pid>", methods=["POST"])
def toggle_watchlist(pid):
    """Toggle product in user's watchlist"""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "Authentication required"}), 401
    
    user_id = user['id']
    if user_id not in WATCHLIST:
        WATCHLIST[user_id] = []
    
    if pid in WATCHLIST[user_id]:
        WATCHLIST[user_id].remove(pid)
        status = "removed"
    else:
        WATCHLIST[user_id].append(pid)
        status = "added"

    return jsonify({
        "ok": True,
        "status": status,
        "count": len(WATCHLIST[user_id])
    })

@app.route("/watchlist", methods=["GET"])
def get_watchlist():
    """Get user's watchlist products"""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "Authentication required"}), 401
    
    user_id = user['id']
    watchlist_ids = WATCHLIST.get(user_id, [])
    
    watchlist_products = []
    for pid in watchlist_ids:
        prod = next((p for p in PRODUCTS if p["id"] == pid), None)
        if prod:
            raw_images = prod.get("images", ["Images/placeholder.jpeg"])
            images = [resolve_image_path(img) for img in raw_images]
            
            watchlist_products.append({
                "product_id": prod["id"],
                "title": prod["title"],
                "price": prod["price"],
                "category": prod["category"],
                "condition": prod.get("condition", "Unknown"),
                "images": images,
                "location": prod["location"],
            })
    
    return jsonify({"ok": True, "products": watchlist_products})

# -------------------- SELL / LIST PRODUCT --------------------

@app.route("/sell", methods=["POST"])
def sell():
    """List a new product for sale"""
    user = get_current_user()
    
    title = request.form.get("title", "").strip()
    price = request.form.get("price", "").strip()
    category = request.form.get("category", "").strip()
    location = request.form.get("location", "").strip()
    condition = request.form.get("condition", "").strip()
    description = request.form.get("description", "").strip()
    seller_name = request.form.get("name", "Anonymous").strip()
    seller_contact = request.form.get("contact", "N/A").strip()

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
    
    new_product = {
        "id": pid,
        "title": title,
        "price": price_val,
        "category": category,
        "condition": condition,
        "description": description,
        "images": image_paths,
        "location": location,
        "distance_miles": 1.0,
        "views": 0,
        "seller_name": seller_name,
        "seller_contact": seller_contact,
        "seller_id": user['id'] if user else "anonymous",
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending",
        "blockchain_verified": False,
    }
    
    PRODUCTS.append(new_product)

    qr_code_data = generate_qr_code(pid)

    return jsonify({
        "ok": True,
        "status": "listed",
        "product_id": pid,
        "message": "Product listed successfully",
        "nano_tag": {
            "qr_code": qr_code_data,
            "product_id": pid
        }
    }), 200

# -------------------- SEARCH --------------------

@app.route("/search")
def search():
    """Search products"""
    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "").strip().lower()
    
    if not query and not category:
        return jsonify({"ok": True, "products": []})
    
    items = PRODUCTS.copy()
    
    if query:
        items = [p for p in items if query in p["title"].lower() or query in p.get("description", "").lower()]
    
    if category:
        items = [p for p in items if p["category"].lower() == category]
    
    products_data = []
    for p in items:
        raw_images = p.get("images", ["Images/placeholder.jpeg"])
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

# -------------------- MISC ROUTES --------------------

@app.route("/feedback", methods=["POST"])
def feedback():
    """Submit feedback"""
    data = request.get_json() if request.is_json else request.form
    name = data.get("name", "").strip()
    message = data.get("message", "").strip()
    
    # Store feedback (in production, save to database)
    print(f"Feedback from {name}: {message}")
    
    return jsonify({"ok": True, "message": "Thank you for your feedback!"})

@app.route("/settings", methods=["POST"])
def settings():
    """Update user settings"""
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "Authentication required"}), 401
    
    # Handle settings update (in production, save to database)
    return jsonify({"ok": True, "message": "Settings saved successfully"})

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)