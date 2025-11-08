// Main Content Switching - Define globally before DOMContentLoaded
function showContent(sectionId) {
    console.log('Switching to section:', sectionId); // Debug log
    
    // Get all content sections
    const allSections = document.querySelectorAll('.content-section');
    console.log('Found sections:', allSections.length); // Debug log
    
    // Remove active class from all sections
    allSections.forEach(section => {
        section.classList.remove('active-content');
    });
    
    // Add active class to the selected section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active-content');
        console.log('Activated section:', sectionId); // Debug log
    } else {
        console.error('Section not found:', sectionId); // Debug log
    }
    
    // Update active nav link styling
    const allNavLinks = document.querySelectorAll('.nav-links');
    allNavLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    const activeLink = document.getElementById(`link-${sectionId}`);
    if (activeLink) {
        activeLink.classList.add('active');
        console.log('Activated link:', `link-${sectionId}`); // Debug log
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Loaded'); // Debug log
    
    const signUpSection = document.getElementById('new-account');
    const signInSection = document.getElementById('login-account');

    const signInBtn = document.getElementById('sign-in-btn');
    const signUpBtn = document.getElementById('sign-up-btn');

    /**
     * Toggles the visibility of the forms.
     * @param {Event} event - The click event.
     * @param {HTMLElement} showForm - The form section to show.
     * @param {HTMLElement} hideForm - The form section to hide.
     */
    const toggleForms = (event, showForm, hideForm) => {
        event.preventDefault(); // Stop the <a> tag from navigating
        
        hideForm.style.opacity = '0';
        setTimeout(() => {
            hideForm.style.display = 'none';
            
            // Show the target form
            showForm.style.display = 'block'; // Or 'grid', depending on your CSS layout
            setTimeout(() => {
                showForm.style.opacity = '1';
            }, 10); // Small delay to ensure display:block is applied first
            
        }, 300); // Wait for the opacity transition (0.3s) to finish before setting display:none
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
    
    if (signUpSection && signInSection) {
        signUpSection.style.display = 'block';
        signUpSection.style.opacity = '1';
        signInSection.style.display = 'none';
        signInSection.style.opacity = '0';
    }

    showContent('feed');
    
    const navLinks = document.querySelectorAll('.nav-links');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const linkId = this.id;
            if (linkId.startsWith('link-')) {
                e.preventDefault();
                const sectionId = linkId.replace('link-', '');
                showContent(sectionId);
            }
        });
    });
});


// ========================== View Detail JS 

// Global element references
const feedView = document.getElementById('feed-view');
const detailView = document.getElementById('detail-view');
const feedContainer = document.getElementById('feed-container');
const detailContent = document.getElementById('detail-content');
const mainContent = document.getElementById('main-content');


/**
 * Creates the HTML string for a single product card, matching the user's provided structure.
 * @param {Object} product - The product data object.
 * @returns {string} The HTML string for the card.
 */
function createProductCardHTML(product) {
    // Placeholder URL uses data from the object for dynamic content
    const imgSize = 400;
    const imgUrl = `https://placehold.co/${imgSize}x${imgSize}/${product.color}/${product.text}?text=${product.title.replace(/\s/g, '+')}`;

    return `
        <article class="product-card" data-product-id="${product.id}">
            <div class="card-image-wrapper">
                <img src="${imgUrl}" alt="${product.title}" onerror="this.onerror=null; this.src='https://placehold.co/400x400/808080/FFFFFF?text=Item+Fail';" />
                <figcaption>
                    <button class="wishlist-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-heart-plus">
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
            <button class="place">${product.city}</button>
            <div class="card-btn">
                <button class="price-tag">$ ${product.price}</button>
                <div class="btn-grp">
                    <button class="view_details" onclick="handleProductClick(event, ${product.id})">
                        <p>View Details</p>
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-arrow-out-up-right"><path d="M22 12A10 10 0 1 1 12 2"/><path d="M22 2 12 12"/><path d="M16 2h6v6"/></svg>
                    </button>
                </div>
            </div>
        </article>
    `;
}

/**
 * Renders all product data into the feed container.
 */
function renderProducts() {
    feedContainer.innerHTML = productData.map(createProductCardHTML).join('');
}

/**
 * Switches the view to show the main product feed.
 */
function showFeedView() {
    detailView.style.display = 'none';
    feedView.style.display = 'block';
    mainContent.scrollTop = 0;
}

/**
 * Switches the view to show the details for the selected product.
 * @param {number} productId - The ID of the clicked product.
 */
function showDetailView(productId) {
    const product = productData.find(p => p.id === productId);
    if (!product) return;

    // 1. Hide the feed view and show the detail view
    feedView.style.display = 'none';
    detailView.style.display = 'block';
    mainContent.scrollTop = 0;

    // 2. Create rich, detailed content for the featured area
    const imgUrl = `https://placehold.co/800x600/${product.color}/${product.text}?text=${product.title.replace(/\s/g, '+')}`;

    const detailHTML = `
        <div class="detail-layout">
            <div class="detail-image-wrapper">
                <img src="${imgUrl}" alt="${product.title}" onerror="this.onerror=null; this.src='https://placehold.co/800x600/808080/FFFFFF?text=Image+Load+Fail';" />
            </div>
            <div class="detail-info">
                <h3>${product.title}</h3>
                <p style="font-size: 1.125rem; color: #94a3b8; margin-bottom: 0.5rem;">Category: <span style="font-weight: 600; color: white;">${product.category}</span></p>
                <p style="font-size: 1.125rem; color: #94a3b8; margin-bottom: 1.5rem;">Location: <span style="font-weight: 600; color: white;">${product.city}</span></p>
                
                <div style="padding: 1rem; background: #15202b; border-radius: 0.5rem; margin-bottom: 2rem; border-left: 3px solid #7ED321;">
                    <p style="font-size: 1.5rem; font-weight: 800; color: #7ED321; margin: 0;">Price: $ ${product.price}</p>
                </div>

                <p style="font-size: 1.15rem; color: white; margin-bottom: 1.5rem; line-height: 1.6;">
                    ${product.description}
                </p>
                
                <div class="detail-meta-group">
                    <p style="color: #94a3b8;"><strong>Condition:</strong> <span class="detail-meta-tag" style="background-color: #3b82f6;">Verified Pre-Owned</span></p>
                    <p style="color: #94a3b8;"><strong>Seller Rating:</strong> <span class="detail-meta-tag" style="background-color: #facc15; color: #000;">★★★★★</span> (4.9/5)</p>
                    <p style="color: #94a3b8;"><strong>Posted:</strong> <span class="detail-meta-tag">2 days ago</span></p>
                </div>
                <button class="detail-button">
                    Contact Seller
                </button>
            </div>
        </div>
    `;

    // 3. Insert the new content
    detailContent.innerHTML = detailHTML;
}

/**
 * Main click handler that initiates the view switch.
 */
function handleProductClick(event, productId) {
    // Stop propagation to prevent accidental clicks on the parent card if any
    event.stopPropagation();
    showDetailView(productId);
}

// Initial setup when the page loads
window.onload = () => {
    renderProducts();
    // Start on the feed view
    showFeedView(); 
};