#Secondhand Marketplace

Welcome to the Secondhand Marketplace! This platform allows users to buy and sell pre-owned items easily and securely. Whether you're looking to declutter your home or find a great deal on something you need, our marketplace is the perfect place to connect with other users.

## Features
- User Registration and Profiles: Create an account to start buying and selling items.
- Item Listings: Post items for sale with descriptions, photos, and prices.
- Search and Filter: Easily find items by category, price range, location, and more.
- Messaging System: Communicate directly with buyers and sellers.
- Secure Transactions: Safe payment options to ensure a smooth buying and selling experience.
- Reviews and Ratings: Leave feedback for buyers and sellers to build trust within the community.

## technologies Used
- Frontend: HTML, CSS, JavaScript.
- Backend: Django Framework.
- Database: SQLite/PostgreSQL.
- Deployment: Github pages.


## REQUIREMENTS TXT: 

INSTALLATION:
pip install -r requirements.txt

RUN SERVER:
python app.py

API ENDPOINTS SUMMARY:

Authentication:
- POST /api/auth/register - Register new user
- POST /api/auth/login - User login
- POST /api/auth/logout - User logout

Products:
- POST /api/products/list - Create product listing (with image upload)
- POST /api/products/activate/<id> - Activate nano-tag
- GET /api/products/feed - Get product feed
- GET /api/products/<id> - Get product details
- GET /api/products/verify/<id> - Verify via nano-tag scan
- POST /api/products/transfer/<id> - Transfer ownership
- GET /api/user/listings - Get user's listings
- GET /api/user/profile - Get user profile

FRONTEND INTEGRATION EXAMPLE:

// Register User
fetch('http://localhost:5000/api/auth/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123',
        name: 'John Doe',
        phone: '+91 9876543210',
        location: 'Mumbai'
    })
});

// List Product
const formData = new FormData();
formData.append('title', 'Cotton Belt Watch');
formData.append('category', 'accessories');
formData.append('condition', 'Like New');
formData.append('price', '11500');
formData.append('description', 'High quality watch in excellent condition');
formData.append('location', 'Mumbai, Maharashtra');

// Add images
formData.append('images', imageFile1);
formData.append('images', imageFile2);

fetch('http://localhost:5000/api/products/list', {
    method: 'POST',
    body: formData
});

// Get Product Feed
fetch('http://localhost:5000/api/products/feed')
    .then(res => res.json())
    .then(data => console.log(data.products));

// Verify Product (Nano-tag scan)
fetch('http://localhost:5000/api/products/verify/PRD_ABC123')
    .then(res => res.json())
    .then(data => {
        console.log('Verified:', data.verified);
        console.log('Blockchain verified:', data.blockchain_verified);
    });