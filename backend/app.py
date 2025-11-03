"""
SecondHand Marketplace - Dynamic Backend System
Handles authentication, product listing, blockchain integration, AI verification, and nano-tags
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import hashlib
import uuid
import os
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import base64
from PIL import Image
import imagehash

# --- START DATABASE IMPORTS & CONFIGURATION ---
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Text, DateTime, func, ForeignKey
# --- END DATABASE IMPORTS & CONFIGURATION ---

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
# Configure CORS for API requests. When the frontend uses `fetch(..., credentials: 'include')`
# the server must allow credentials and set a specific origin (cannot be '*').
# Adjust the origins list to match where you serve the frontend (example below uses port 5500).
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:5501"
]}})

# --- START DATABASE CONFIGURATION ---
# Use SQLite database, which will create a file named 'site.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# --- END DATABASE CONFIGURATION ---


# Configuration
UPLOAD_FOLDER = 'uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data/blockchain', exist_ok=True) # Blockchain file simulation remains

# ==================== DATA MODELS (REPLACING DataStore) ====================

class User(db.Model):
    __tablename__ = 'user'
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    name: Mapped[str] = mapped_column(String(100), default='')
    phone: Mapped[str] = mapped_column(String(20), default='')
    location: Mapped[str] = mapped_column(String(100), default='')
    reputation_score: Mapped[int] = mapped_column(Integer, default=100)
    listings_count: Mapped[int] = mapped_column(Integer, default=0)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    products = relationship("Product", foreign_keys='Product.seller_id', back_populates="seller")
    
    def to_dict(self):
        return {
            'user_id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'location': self.location,
            'reputation_score': self.reputation_score,
            'listings_count': self.listings_count,
            'sales_count': self.sales_count,
            'created_at': self.created_at.isoformat()
        }

class Product(db.Model):
    __tablename__ = 'product'
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    seller_id: Mapped[str] = mapped_column(String(50), ForeignKey('user.id'), nullable=True) # Nullable for anonymous
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str] = mapped_column(String(100), default='')
    location: Mapped[str] = mapped_column(String(100), default='')
    images: Mapped[str] = mapped_column(Text, default='') # Stored as comma-separated string
    image_hashes: Mapped[str] = mapped_column(Text, default='') # Stored as comma-separated string
    status: Mapped[str] = mapped_column(String(20), default='pending') # pending, active, sold, removed
    views: Mapped[int] = mapped_column(Integer, default=0)
    watchlist_count: Mapped[int] = mapped_column(Integer, default=0)
    nano_tag: Mapped[str] = mapped_column(Text, default='{}') # Stored as JSON string
    blockchain_id: Mapped[str] = mapped_column(String(50), default='')
    buyer_id: Mapped[str] = mapped_column(String(50), ForeignKey('user.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    seller = relationship("User", foreign_keys=[seller_id], back_populates="products")

    def to_dict(self):
        seller_name = self.seller.name if self.seller else ('Anonymous Seller' if self.seller_id == ANONYMOUS_SELLER_ID else 'N/A')
        seller_contact = self.seller.phone if self.seller else ('N/A' if self.seller_id == ANONYMOUS_SELLER_ID else 'N/A')
        
        return {
            'product_id': self.id,
            'seller_id': self.seller_id,
            'seller_name': seller_name,
            'seller_contact': seller_contact,
            'title': self.title,
            'category': self.category,
            'condition': self.condition,
            'price': self.price,
            'description': self.description,
            'brand': self.brand,
            'location': self.location,
            'images': self.images.split(',') if self.images else [],
            'image_hashes': self.image_hashes.split(',') if self.image_hashes else [],
            'status': self.status,
            'views': self.views,
            'watchlist_count': self.watchlist_count,
            'nano_tag': _safe_load_json(self.nano_tag),
            'blockchain_id': self.blockchain_id,
            'buyer_id': self.buyer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.created_at else None
        }

# Define an anonymous seller ID for unauthenticated listings
ANONYMOUS_SELLER_ID = "ANON_USR_001"

# ==================== BLOCKCHAIN SIMULATION (Modified to use DB) ====================
class BlockchainManager:
    """Simulated blockchain for product verification"""
    
    @staticmethod
    def create_block(data):
        """Create a new block with product data (still file-based for simulation)"""
        block_id = str(uuid.uuid4())
        previous_hash = BlockchainManager._get_last_block_hash()
        
        block = {
            'block_id': block_id,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'previous_hash': previous_hash,
            'hash': BlockchainManager._calculate_hash(data, previous_hash)
        }
        
        # Save block
        filepath = f"data/blockchain/{block_id}.json"
        os.makedirs('data/blockchain', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(block, f, indent=2)
        
        return block
    
    @staticmethod
    def _calculate_hash(data, previous_hash):
        """Calculate SHA-256 hash"""
        content = json.dumps(data, sort_keys=True) + previous_hash
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def _get_last_block_hash():
        """Get hash of the last block"""
        blocks = os.listdir('data/blockchain')
        if not blocks:
            return "0" * 64  # Genesis block
        
        # Get most recent block
        # Use Product model to ensure we find a valid product block if possible
        latest_block_filename = max(blocks, key=lambda x: os.path.getctime(f"data/blockchain/{x}"))
        with open(f"data/blockchain/{latest_block_filename}", 'r') as f:
            block = json.load(f)
            return block['hash']
    
    @staticmethod
    def verify_ownership(product_id):
        """Verify product ownership chain by checking DB status and file record."""
        product = db.session.get(Product, product_id)
        if product and product.status != 'removed':
            for filename in os.listdir('data/blockchain'):
                if filename.endswith('.json'):
                    with open(f'data/blockchain/{filename}', 'r') as f:
                        block = json.load(f)
                        if block['data'].get('product_id') == product_id and block['data'].get('action') == 'created':
                            return block
        return None

# ==================== AI VERIFICATION (Modified to use DB) ====================
class AIVerifier:
    """AI-assisted product verification"""
    
    @staticmethod
    def verify_images(image_paths):
        """Check for duplicate/similar images using perceptual hashing"""
        hashes = []
        for path in image_paths:
            try:
                img = Image.open(path)
                img_hash = imagehash.average_hash(img)
                hashes.append(str(img_hash))
            except Exception as e:
                print(f"Error hashing image {path}: {e}")
        
        # Check for duplicates in database
        all_products = db.session.execute(db.select(Product)).scalars().all()
        for product in all_products:
            stored_hashes = product.image_hashes.split(',') if product.image_hashes else []
            for stored_hash in stored_hashes:
                for new_hash in hashes:
                    try:
                        similarity = imagehash.hex_to_hash(stored_hash) - imagehash.hex_to_hash(new_hash)
                        if similarity < 5:  # Very similar images
                            return {
                                'verified': False,
                                'reason': 'Similar images found in existing listings',
                                'similar_product_id': product.id
                            }
                    except ValueError:
                        continue # Skip invalid hashes
        
        return {'verified': True, 'image_hashes': hashes}
    
    @staticmethod
    def verify_metadata(product_data):
        """Verify product metadata for inconsistencies"""
        issues = []
        
        # Check price reasonability
        try:
            price = float(product_data.get('price', 0))
        except ValueError:
            price = 0
            
        if price <= 0:
            issues.append('Invalid price')
        elif price > 1000000:
            issues.append('Price seems unusually high')
        
        # Check required fields
        required = ['title', 'category', 'condition', 'description']
        for field in required:
            if not product_data.get(field):
                issues.append(f'Missing required field: {field}')
        
        # Check description length
        description = product_data.get('description', '')
        if len(description) < 20:
            issues.append('Description too short (minimum 20 characters)')
        
        return {
            'verified': len(issues) == 0,
            'issues': issues
        }

# ==================== NANO-TAG SYSTEM (Modified to use DB) ====================
class NanoTagManager:
    """Manage QR codes and nano-tags for products"""
    
    @staticmethod
    def generate_tag(product_id, product_data):
        """Generate QR code with product verification URL"""
        # Create verification URL
        verify_url = f"https://secondhand.com/verify/{product_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'tag_id': str(uuid.uuid4()),
            'product_id': product_id,
            'qr_code': img_str,
            'verify_url': verify_url,
            'activated': False,
            'created_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def activate_tag(tag_id, product_id):
        """Activate a nano-tag after physical attachment"""
        product = db.session.get(Product, product_id)
        if product:
            try:
                nano_tag_data = json.loads(product.nano_tag)
            except json.JSONDecodeError:
                return False
                
            if nano_tag_data.get('tag_id') == tag_id:
                nano_tag_data['activated'] = True
                nano_tag_data['activated_at'] = datetime.now().isoformat()
                
                product.nano_tag = json.dumps(nano_tag_data) # Save updated JSON string
                product.status = 'active'
                product.updated_at = datetime.now() 
                
                db.session.commit()
                return True
        return False

# ==================== UTILITY FUNCTIONS ====================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _safe_load_json(raw):
    """Safely load JSON from a string, returning an empty dict on failure."""
    try:
        if not raw:
            return {}
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}

def generate_user_id():
    return f"USR_{uuid.uuid4().hex[:12].upper()}"

def generate_product_id():
    return f"PRD_{uuid.uuid4().hex[:12].upper()}"

# ==================== API ROUTES (Rewritten for DB) ====================

@app.route('/', methods=['GET'])
def server_status():
    """Confirms the Flask server is running and provides a hint."""
    return jsonify({
        'status': 'Backend API server is running',
        'message': 'This is the API server. To view the application, open your index.html file in your web browser.'
    }), 200

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    # Check if user exists
    user_exists = db.session.execute(db.select(User).filter_by(email=data['email'])).scalar_one_or_none()
    if user_exists:
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create user
    user = User(
        id=generate_user_id(),
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        name=data.get('name', ''),
        phone=data.get('phone', ''),
        location=data.get('location', '')
    )
    
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    
    return jsonify({
        'message': 'Registration successful',
        'user_id': user.id,
        'email': user.email
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.json
    
    user = db.session.execute(db.select(User).filter_by(email=data.get('email'))).scalar_one_or_none()
    
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    session['user_id'] = user.id
    
    return jsonify({
        'message': 'Login successful',
        'user_id': user.id,
        'email': user.email,
        'name': user.name
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'})

# Product Routes
@app.route('/api/products/list', methods=['POST'])
def list_product():
    """Create new product listing, bypassing authentication for anonymous users."""
    
    # Determine seller ID: logged-in user or anonymous placeholder
    seller_id = session.get('user_id', ANONYMOUS_SELLER_ID)
    
    # Fetch seller object (will be None if anonymous)
    seller = db.session.get(User, seller_id) if seller_id != ANONYMOUS_SELLER_ID else None
    
    # Handle file uploads
    image_paths = []
    image_hashes = []
    
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files[:4]: 
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                image_paths.append(filepath)

    # Get form data
    product_data = {
        'title': request.form.get('title'),
        'category': request.form.get('category'),
        'condition': request.form.get('condition'),
        'price': request.form.get('price'),
        'description': request.form.get('description'),
        'brand': request.form.get('brand', ''),
        'location': request.form.get('location'),
    }
    
    # AI Verification - Metadata
    metadata_check = AIVerifier.verify_metadata(product_data)
    if not metadata_check['verified']:
        return jsonify({
            'error': 'Product verification failed',
            'issues': metadata_check['issues']
        }), 400
    
    # AI Verification - Images
    if image_paths:
        image_check = AIVerifier.verify_images(image_paths)
        if not image_check['verified']:
            return jsonify({
                'error': 'Image verification failed',
                'reason': image_check['reason']
            }), 400
        image_hashes = image_check['image_hashes']
    
    # Create product
    product_id = generate_product_id()
    
    product_obj = Product(
        id=product_id,
        seller_id=seller.id if seller else ANONYMOUS_SELLER_ID,
        title=product_data['title'],
        category=product_data['category'],
        condition=product_data['condition'],
        price=float(product_data['price']),
        description=product_data['description'],
        brand=product_data['brand'],
        location=product_data['location'],
        images=','.join(image_paths),
        image_hashes=','.join(image_hashes),
        status='pending'
    )
    
    # Generate nano-tag
    nano_tag = NanoTagManager.generate_tag(product_id, product_obj.to_dict())
    product_obj.nano_tag = json.dumps(nano_tag)
    
    # Create blockchain record (still file-based simulation for the block)
    blockchain_data = {
        'product_id': product_id,
        'seller_id': product_obj.seller_id,
        'action': 'created',
        'timestamp': datetime.now().isoformat(),
        'product_hash': hashlib.sha256(json.dumps(product_obj.to_dict(), sort_keys=True).encode()).hexdigest()
    }
    block = BlockchainManager.create_block(blockchain_data)
    product_obj.blockchain_id = block['block_id']
    
    # Save product
    db.session.add(product_obj)
    
    # Update seller stats (only if logged in)
    if seller:
        seller.listings_count = seller.listings_count + 1
    
    db.session.commit()
    
    return jsonify({
        'message': 'Product listed successfully',
        'product_id': product_id,
        'nano_tag': nano_tag,
        'blockchain_id': block['block_id'],
        'status': 'pending'
    }), 201

@app.route('/api/products/activate/<product_id>', methods=['POST'])
def activate_product(product_id):
    """Activate product after nano-tag attachment."""
    try:
        # 1️⃣ Tìm sản phẩm
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # 2️⃣ Kiểm tra quyền sở hữu
        current_user_id = session.get('user_id', ANONYMOUS_SELLER_ID)
        if product.seller_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # 3️⃣ Đọc tag_id an toàn
        nano_tag_data = _safe_load_json(product.nano_tag)
        tag_id = nano_tag_data.get('tag_id') if nano_tag_data else None
        if not tag_id:
            return jsonify({'error': 'Missing or invalid nano-tag data'}), 400

        # 4️⃣ Kích hoạt tag
        success = NanoTagManager.activate_tag(tag_id, product_id)
        if not success:
            return jsonify({'error': 'Activation failed'}), 400

        # 5️⃣ Cập nhật trạng thái sản phẩm
        product.status = 'active'
        db.session.commit()

        return jsonify({
            'message': 'Product activated successfully',
            'status': product.status
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

@app.route('/api/products/feed', methods=['GET'])
def get_feed():
    """Get product feed"""
    category = request.args.get('category')
    
    query = db.select(Product).order_by(Product.created_at.desc())
    if category:
        query = query.filter_by(category=category)
        
    active_products = db.session.execute(query).scalars().all()
    
    products_data = []
    for product in active_products:
        p_dict = product.to_dict()
        p_dict.pop('image_hashes', None)
        p_dict.pop('blockchain_id', None)
        products_data.append(p_dict)

    return jsonify({'products': products_data})

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details"""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Increment views
    product.views += 1
    db.session.commit()
    
    # Get blockchain verification
    blockchain_record = BlockchainManager.verify_ownership(product_id)
    
    return jsonify({
        'product': product.to_dict(),
        'blockchain_verified': blockchain_record is not None,
        'blockchain_record': blockchain_record
    })

@app.route('/api/products/verify/<product_id>', methods=['GET'])
def verify_product(product_id):
    """Verify product via nano-tag scan"""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Get blockchain verification
    blockchain_record = BlockchainManager.verify_ownership(product_id)
    
    # Get seller reputation
    seller = db.session.get(User, product.seller_id)
    
    return jsonify({
        'verified': True,
        'product': {
            'title': product.title,
            'condition': product.condition,
            'price': product.price,
            'description': product.description,
            'created_at': product.created_at.isoformat()
        },
        'seller': {
            'name': seller.name if seller else 'Anonymous',
            'reputation_score': seller.reputation_score if seller else 0,
            'sales_count': seller.sales_count if seller else 0
        },
        'blockchain_verified': blockchain_record is not None,
        'nano_tag_activated': _safe_load_json(product.nano_tag).get('activated', False)
    })

@app.route('/api/products/transfer/<product_id>', methods=['POST'])
def transfer_ownership(product_id):
    """Transfer product ownership (on purchase)"""
    buyer_id = session.get('user_id')
    if not buyer_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    product = db.session.get(Product, product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Create blockchain record for ownership transfer
    blockchain_data = {
        'product_id': product_id,
        'from_user': product.seller_id,
        'to_user': buyer_id,
        'action': 'transferred',
        'price': product.price,
        'timestamp': datetime.now().isoformat()
    }
    block = BlockchainManager.create_block(blockchain_data)
    
    # Update product
    product.status = 'sold'
    product.buyer_id = buyer_id
    
    # Update seller stats
    seller = db.session.get(User, product.seller_id)
    if seller:
        seller.sales_count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': 'Ownership transferred successfully',
        'blockchain_id': block['block_id']
    })

@app.route('/api/user/listings', methods=['GET'])
def get_user_listings():
    """Get current user's listings"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    products = db.session.execute(
        db.select(Product).filter_by(seller_id=user_id).order_by(Product.created_at.desc())
    ).scalars().all()

    return jsonify({'listings': [p.to_dict() for p in products]})

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Get user profile"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = db.session.get(User, user_id)
    if user:
        return jsonify({'user': user.to_dict()})
    
    return jsonify({'error': 'User not found'}), 404

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    with app.app_context():
        # This creates the 'site.db' file and all necessary tables 
        # based on the User and Product models defined above.
        db.create_all() 
    app.run(debug=True, host='0.0.0.0', port=5000)