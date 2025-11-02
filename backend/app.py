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

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data/users', exist_ok=True)
os.makedirs('data/products', exist_ok=True)
os.makedirs('data/blockchain', exist_ok=True)

# ==================== DATA STORAGE ====================
class DataStore:
    """Simple file-based data storage"""
    
    @staticmethod
    def save_user(user_data):
        user_id = user_data['user_id']
        filepath = f"data/users/{user_id}.json"
        with open(filepath, 'w') as f:
            json.dump(user_data, f, indent=2)
    
    @staticmethod
    def get_user_by_email(email):
        for filename in os.listdir('data/users'):
            if filename.endswith('.json'):
                with open(f'data/users/{filename}', 'r') as f:
                    user = json.load(f)
                    if user['email'] == email:
                        return user
        return None
    
    @staticmethod
    def get_user_by_id(user_id):
        filepath = f"data/users/{user_id}.json"
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def save_product(product_data):
        product_id = product_data['product_id']
        filepath = f"data/products/{product_id}.json"
        with open(filepath, 'w') as f:
            json.dump(product_data, f, indent=2)
    
    @staticmethod
    def get_product(product_id):
        filepath = f"data/products/{product_id}.json"
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def get_all_products(category=None, seller_id=None):
        products = []
        for filename in os.listdir('data/products'):
            if filename.endswith('.json'):
                with open(f'data/products/{filename}', 'r') as f:
                    product = json.load(f)
                    if category and product.get('category') != category:
                        continue
                    if seller_id and product.get('seller_id') != seller_id:
                        continue
                    products.append(product)
        return sorted(products, key=lambda x: x['created_at'], reverse=True)

# ==================== BLOCKCHAIN SIMULATION ====================
class BlockchainManager:
    """Simulated blockchain for product verification"""
    
    @staticmethod
    def create_block(data):
        """Create a new block with product data"""
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
        latest_block = max(blocks, key=lambda x: os.path.getctime(f"data/blockchain/{x}"))
        with open(f"data/blockchain/{latest_block}", 'r') as f:
            block = json.load(f)
            return block['hash']
    
    @staticmethod
    def verify_ownership(product_id):
        """Verify product ownership chain"""
        for filename in os.listdir('data/blockchain'):
            with open(f'data/blockchain/{filename}', 'r') as f:
                block = json.load(f)
                if block['data'].get('product_id') == product_id:
                    return block
        return None

# ==================== AI VERIFICATION ====================
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
        all_products = DataStore.get_all_products()
        for product in all_products:
            for stored_hash in product.get('image_hashes', []):
                for new_hash in hashes:
                    similarity = imagehash.hex_to_hash(stored_hash) - imagehash.hex_to_hash(new_hash)
                    if similarity < 5:  # Very similar images
                        return {
                            'verified': False,
                            'reason': 'Similar images found in existing listings',
                            'similar_product_id': product['product_id']
                        }
        
        return {'verified': True, 'image_hashes': hashes}
    
    @staticmethod
    def verify_metadata(product_data):
        """Verify product metadata for inconsistencies"""
        issues = []
        
        # Check price reasonability
        price = float(product_data.get('price', 0))
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

# ==================== NANO-TAG SYSTEM ====================
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
        product = DataStore.get_product(product_id)
        if product and product.get('nano_tag', {}).get('tag_id') == tag_id:
            product['nano_tag']['activated'] = True
            product['nano_tag']['activated_at'] = datetime.now().isoformat()
            product['status'] = 'active'
            DataStore.save_product(product)
            return True
        return False

# ==================== UTILITY FUNCTIONS ====================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_user_id():
    return f"USR_{uuid.uuid4().hex[:12].upper()}"

def generate_product_id():
    return f"PRD_{uuid.uuid4().hex[:12].upper()}"

# ==================== API ROUTES ====================

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    
    # Validate input
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    # Check if user exists
    if DataStore.get_user_by_email(data['email']):
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create user
    user_data = {
        'user_id': generate_user_id(),
        'email': data['email'],
        'password_hash': generate_password_hash(data['password']),
        'name': data.get('name', ''),
        'phone': data.get('phone', ''),
        'location': data.get('location', ''),
        'reputation_score': 100,
        'listings_count': 0,
        'sales_count': 0,
        'created_at': datetime.now().isoformat()
    }
    
    DataStore.save_user(user_data)
    
    # Create session
    session['user_id'] = user_data['user_id']
    
    return jsonify({
        'message': 'Registration successful',
        'user_id': user_data['user_id'],
        'email': user_data['email']
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.json
    
    user = DataStore.get_user_by_email(data.get('email'))
    if not user or not check_password_hash(user['password_hash'], data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    session['user_id'] = user['user_id']
    
    return jsonify({
        'message': 'Login successful',
        'user_id': user['user_id'],
        'email': user['email'],
        'name': user.get('name')
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'})

# Product Routes
@app.route('/api/products/list', methods=['POST'])
def list_product():
    """Create new product listing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Handle file uploads
    image_paths = []
    image_hashes = []
    
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files[:4]:  # Max 4 images
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
    seller = DataStore.get_user_by_id(session['user_id'])
    
    product = {
        'product_id': product_id,
        'seller_id': session['user_id'],
        'seller_name': seller.get('name', 'Anonymous'),
        'seller_contact': seller.get('phone', ''),
        'title': product_data['title'],
        'category': product_data['category'],
        'condition': product_data['condition'],
        'price': float(product_data['price']),
        'description': product_data['description'],
        'brand': product_data['brand'],
        'location': product_data['location'],
        'images': image_paths,
        'image_hashes': image_hashes,
        'status': 'pending',  # pending, active, sold, removed
        'views': 0,
        'watchlist_count': 0,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # Generate nano-tag
    nano_tag = NanoTagManager.generate_tag(product_id, product)
    product['nano_tag'] = nano_tag
    
    # Create blockchain record
    blockchain_data = {
        'product_id': product_id,
        'seller_id': session['user_id'],
        'action': 'created',
        'timestamp': datetime.now().isoformat(),
        'product_hash': hashlib.sha256(json.dumps(product, sort_keys=True).encode()).hexdigest()
    }
    block = BlockchainManager.create_block(blockchain_data)
    product['blockchain_id'] = block['block_id']
    
    # Save product
    DataStore.save_product(product)
    
    # Update seller stats
    seller['listings_count'] = seller.get('listings_count', 0) + 1
    DataStore.save_user(seller)
    
    return jsonify({
        'message': 'Product listed successfully',
        'product_id': product_id,
        'nano_tag': nano_tag,
        'blockchain_id': block['block_id'],
        'status': 'pending'
    }), 201

@app.route('/api/products/activate/<product_id>', methods=['POST'])
def activate_product(product_id):
    """Activate product after nano-tag attachment"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    product = DataStore.get_product(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if product['seller_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    tag_id = product.get('nano_tag', {}).get('tag_id')
    if NanoTagManager.activate_tag(tag_id, product_id):
        return jsonify({
            'message': 'Product activated successfully',
            'status': 'active'
        })
    
    return jsonify({'error': 'Activation failed'}), 400

@app.route('/api/products/feed', methods=['GET'])
def get_feed():
    """Get product feed"""
    category = request.args.get('category')
    products = DataStore.get_all_products(category=category)
    
    # Filter only active products
    active_products = [p for p in products if p.get('status') == 'active']
    
    # Remove sensitive data
    for product in active_products:
        product.pop('image_hashes', None)
        product.pop('blockchain_id', None)
    
    return jsonify({'products': active_products})

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details"""
    product = DataStore.get_product(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Increment views
    product['views'] = product.get('views', 0) + 1
    DataStore.save_product(product)
    
    # Get blockchain verification
    blockchain_record = BlockchainManager.verify_ownership(product_id)
    
    return jsonify({
        'product': product,
        'blockchain_verified': blockchain_record is not None,
        'blockchain_record': blockchain_record
    })

@app.route('/api/products/verify/<product_id>', methods=['GET'])
def verify_product(product_id):
    """Verify product via nano-tag scan"""
    product = DataStore.get_product(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Get blockchain verification
    blockchain_record = BlockchainManager.verify_ownership(product_id)
    
    # Get seller reputation
    seller = DataStore.get_user_by_id(product['seller_id'])
    
    return jsonify({
        'verified': True,
        'product': {
            'title': product['title'],
            'condition': product['condition'],
            'price': product['price'],
            'description': product['description'],
            'created_at': product['created_at']
        },
        'seller': {
            'name': seller.get('name'),
            'reputation_score': seller.get('reputation_score'),
            'sales_count': seller.get('sales_count')
        },
        'blockchain_verified': blockchain_record is not None,
        'nano_tag_activated': product.get('nano_tag', {}).get('activated', False)
    })

@app.route('/api/products/transfer/<product_id>', methods=['POST'])
def transfer_ownership(product_id):
    """Transfer product ownership (on purchase)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    product = DataStore.get_product(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Create blockchain record for ownership transfer
    blockchain_data = {
        'product_id': product_id,
        'from_user': product['seller_id'],
        'to_user': session['user_id'],
        'action': 'transferred',
        'price': product['price'],
        'timestamp': datetime.now().isoformat()
    }
    block = BlockchainManager.create_block(blockchain_data)
    
    # Update product
    product['status'] = 'sold'
    product['buyer_id'] = session['user_id']
    product['sold_at'] = datetime.now().isoformat()
    DataStore.save_product(product)
    
    # Update seller stats
    seller = DataStore.get_user_by_id(product['seller_id'])
    seller['sales_count'] = seller.get('sales_count', 0) + 1
    DataStore.save_user(seller)
    
    return jsonify({
        'message': 'Ownership transferred successfully',
        'blockchain_id': block['block_id']
    })

@app.route('/api/user/listings', methods=['GET'])
def get_user_listings():
    """Get current user's listings"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    products = DataStore.get_all_products(seller_id=session['user_id'])
    return jsonify({'listings': products})

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Get user profile"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = DataStore.get_user_by_id(session['user_id'])
    if user:
        user.pop('password_hash', None)
        return jsonify({'user': user})
    
    return jsonify({'error': 'User not found'}), 404

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)