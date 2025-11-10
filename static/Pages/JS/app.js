// ==================== GLOBAL STATE ====================
let currentUser = null;
let currentSection = 'feed';

// ==================== UTILITY FUNCTIONS ====================

function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `notification-toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== CONTENT SWITCHING ====================

function showContent(sectionId) {
    console.log('Switching to section:', sectionId);
    currentSection = sectionId;
    
    // Hide all content sections
    const allSections = document.querySelectorAll('.content-section');
    allSections.forEach(section => {
        section.classList.remove('active-content');
        section.style.display = 'none';
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.style.display = 'block';
        setTimeout(() => targetSection.classList.add('active-content'), 10);
    }
    
    // Update active nav link
    const allNavLinks = document.querySelectorAll('.nav-links');
    allNavLinks.forEach(link => link.classList.remove('active'));
    
    const activeLink = document.getElementById(`link-${sectionId}`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    
    // Load content based on section
    if (sectionId === 'feed') {
        loadProductFeed();
    } else if (sectionId === 'watchlist') {
        loadWatchlist();
    } else if (['electronics', 'furniture', 'vehicles', 'apparel', 'home-garden', 'sporting', 'collectibles'].includes(sectionId)) {
        loadProductFeed(sectionId);
    }
}

// Make showContent globally available
window.showContent = showContent;

// ==================== PRODUCT RENDERING ====================

function createProductCard(product) {
    const article = document.createElement('article');
    article.className = 'product-card';
    article.dataset.productId = product.product_id;
    
    const imageSrc = product.images && product.images.length > 0
        ? product.images[0]
        : '/Assets/Images/placeholder.jpeg';
    
    article.innerHTML = `
        <div class="card-image-wrapper">
            <img src="${imageSrc}" alt="${product.title}" onerror="this.src='/Assets/Images/placeholder.jpeg'">
            <figcaption>
                <button class="wishlist-btn" onclick="toggleWatchlist('${product.product_id}', event)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m14.479 19.374-.971.939a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5a5.2 5.2 0 0 1-.219 1.49"/>
                        <path d="M15 15h6"/><path d="M18 12v6"/>
                    </svg>
                </button>
            </figcaption>
        </div>
        <div class="card-info">
            <h4>${product.title}</h4>
            <h6>${product.category}</h6>
        </div>
        <button class="place">${product.location}</button>
        <div class="card-btn">
            <button class="price-tag">₹ ${product.price.toFixed(2)}</button>
            <div class="btn-grp">
                <button class="view_details" onclick="viewProductDetails('${product.product_id}')">
                    <p>View Details</p>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 12A10 10 0 1 1 12 2"/><path d="M22 2 12 12"/><path d="M16 2h6v6"/>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    return article;
}

// ==================== PRODUCT FEED ====================

async function loadProductFeed(category = null) {
    const feedSection = document.querySelector('#feed .items-grid');
    if (!feedSection) return;
    
    // Show loading state
    feedSection.innerHTML = '<p>Loading products...</p>';
    
    try {
        const endpoint = category ? `/products/feed?category=${category}` : '/products/feed';
        const response = await fetch(endpoint);
        const data = await response.json();
        
        if (!data.ok) {
            throw new Error(data.error || 'Failed to load products');
        }
        
        feedSection.innerHTML = '';
        
        if (data.products.length === 0) {
            feedSection.innerHTML = '<div class="empty-state"><p>No products found.</p></div>';
            return;
        }
        
        data.products.forEach(product => {
            feedSection.appendChild(createProductCard(product));
        });
        
    } catch (error) {
        console.error('Failed to load products:', error);
        feedSection.innerHTML = '<div class="empty-state"><p>Failed to load products. Please try again.</p></div>';
        showNotification('Failed to load products', 'error');
    }
}

// Make it globally available
window.loadProductFeed = loadProductFeed;

// ==================== PRODUCT DETAILS ====================

async function viewProductDetails(productId) {
    try {
        const response = await fetch(`/products/${productId}`);
        const data = await response.json();
        
        if (!data.ok) {
            throw new Error(data.error || 'Failed to load product');
        }
        
        const product = data.product;
        const verified = data.blockchain_verified ? '✓ Verified on Blockchain' : 'Not verified';
        const verifiedClass = data.blockchain_verified ? 'verified' : 'unverified';
        
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content product-detail-modal">
                <h2>${product.title}</h2>
                <img src="${product.images[0]}" alt="${product.title}" onerror="this.src='/Assets/Images/placeholder.jpeg'">
                
                <div class="verification-badge ${verifiedClass}">${verified}</div>
                
                <div class="detail-row">
                    <span class="detail-label">Price:</span>
                    <span class="detail-value price-tag">₹${product.price}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Category:</span>
                    <span class="detail-value">${product.category}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Condition:</span>
                    <span class="detail-value">${product.condition}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Location:</span>
                    <span class="detail-value">${product.location}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Description:</span>
                    <span class="detail-value">${product.description}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Seller:</span>
                    <span class="detail-value">${product.seller_name}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Contact:</span>
                    <span class="detail-value">${product.seller_contact}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Views:</span>
                    <span class="detail-value">${product.views}</span>
                </div>
                
                <button class="modal-button modal-button-secondary" onclick="this.closest('.modal-overlay').remove()">
                    Close
                </button>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
    } catch (error) {
        console.error('Failed to load product details:', error);
        showNotification('Failed to load product details', 'error');
    }
}

// Make it globally available
window.viewProductDetails = viewProductDetails;

// ==================== WATCHLIST ====================

async function toggleWatchlist(productId, event) {
    if (event) event.stopPropagation();
    
    if (!currentUser) {
        showNotification('Please login to use watchlist', 'error');
        showContent('settings'); // Redirect to login
        return;
    }
    
    try {
        const response = await fetch(`/watchlist/toggle/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!data.ok) {
            throw new Error(data.error || 'Failed to update watchlist');
        }
        
        showNotification(`Product ${data.status} watchlist`, 'success');
        
        // Update button appearance if needed
        const button = event?.target?.closest('.wishlist-btn');
        if (button) {
            if (data.status === 'added') {
                button.style.color = 'red';
            } else {
                button.style.color = 'currentColor';
            }
        }
        
    } catch (error) {
        console.error('Failed to toggle watchlist:', error);
        showNotification(error.message, 'error');
    }
}

// Make it globally available
window.toggleWatchlist = toggleWatchlist;

async function loadWatchlist() {
    const watchlistSection = document.querySelector('#watchlist .items-grid');
    if (!watchlistSection) return;
    
    if (!currentUser) {
        watchlistSection.innerHTML = '<div class="empty-state"><p>Please login to view your watchlist.</p></div>';
        return;
    }
    
    watchlistSection.innerHTML = '<p>Loading watchlist...</p>';
    
    try {
        const response = await fetch('/watchlist');
        const data = await response.json();
        
        if (!data.ok) {
            throw new Error(data.error || 'Failed to load watchlist');
        }
        
        watchlistSection.innerHTML = '';
        
        if (data.products.length === 0) {
            watchlistSection.innerHTML = '<div class="empty-state"><p>Your watchlist is empty.</p></div>';
            return;
        }
        
        data.products.forEach(product => {
            watchlistSection.appendChild(createProductCard(product));
        });
        
    } catch (error) {
        console.error('Failed to load watchlist:', error);
        watchlistSection.innerHTML = '<div class="empty-state"><p>Failed to load watchlist.</p></div>';
    }
}

// ==================== AUTHENTICATION UI UPDATE ====================

function updateUIForLoggedInUser(user) {
    currentUser = user;
    
    const userButton = document.querySelector('.user');
    if (userButton) {
        userButton.title = `Logged in as ${user.name || user.email}`;
        userButton.classList.add('logged-in');
    }
}

async function checkAuthStatus() {
    try {
        const response = await fetch('/auth/me');
        const data = await response.json();
        
        if (data.ok && data.user) {
            updateUIForLoggedInUser(data.user);
        }
    } catch (error) {
        console.log('Not authenticated');
    }
}

// ==================== SEARCH FUNCTIONALITY ====================

function initSearch() {
    const searchInput = document.querySelector('.hs-wrap input[type="search"]');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length < 2) return;
        
        searchTimeout = setTimeout(async () => {
            try {
                const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.ok) {
                    const feedSection = document.querySelector('#feed .items-grid');
                    if (feedSection) {
                        feedSection.innerHTML = '';
                        data.products.forEach(product => {
                            feedSection.appendChild(createProductCard(product));
                        });
                    }
                }
            } catch (error) {
                console.error('Search failed:', error);
            }
        }, 500);
    });
}

// ==================== FORM TOGGLE (Auth Page) ====================

function initAuthForms() {
    const signUpSection = document.getElementById('new-account');
    const signInSection = document.getElementById('login-account');
    const signInBtn = document.getElementById('sign-in-btn');
    const signUpBtn = document.getElementById('sign-up-btn');

    if (!signUpSection || !signInSection) return;

    const toggleForms = (event, showForm, hideForm) => {
        event.preventDefault();
        
        hideForm.style.opacity = '0';
        setTimeout(() => {
            hideForm.style.display = 'none';
            showForm.style.display = 'block';
            setTimeout(() => {
                showForm.style.opacity = '1';
            }, 10);
        }, 300);
    };

    if (signInBtn) {
        signInBtn.addEventListener('click', (e) => {
            toggleForms(e, signInSection, signUpSection);
        });
    }

    if (signUpBtn) {
        signUpBtn.addEventListener('click', (e) => {
            toggleForms(e, signUpSection, signInSection);
        });
    }
    
    // Set initial state
    signUpSection.style.display = 'block';
    signUpSection.style.opacity = '1';
    signInSection.style.display = 'none';
    signInSection.style.opacity = '0';
}

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Marketplace App Loaded');
    
    // Check authentication status
    checkAuthStatus();
    
    // Initialize search
    initSearch();
    
    // Initialize auth forms if on auth page
    initAuthForms();
    
    // Show initial content (feed)
    showContent('feed');
    
    // Setup navigation links
    const navLinks = document.querySelectorAll('.nav-links');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const linkId = this.id;
            if (linkId.startsWith('link-')) {
                const sectionId = linkId.replace('link-', '');
                showContent(sectionId);
            }
        });
    });
});