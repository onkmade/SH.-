const API_BASE_URL = "http://localhost:5000/api";

// Utility function for API calls
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!data.success && data.error) {
      throw new Error(data.error);
    }

    return data;
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

// ==================== AUTHENTICATION ====================

// Handle Sign-Up Form
function initAuthForms() {
  const signUpSection = document.getElementById("new-account");
  const signInSection = document.getElementById("login-account");

  if (signUpSection) {
    const signUpButton = signUpSection.querySelector(".Sign-up");
    if (signUpButton) {
      signUpButton.addEventListener("click", async (e) => {
        e.preventDefault();

        const email = document.getElementById("email-up").value.trim();
        const password = document.getElementById("password-up").value;
        const policyChecked = document.getElementById("policy-up").checked;

        if (!email || !password) {
          alert("Please fill in all fields");
          return;
        }

        if (!policyChecked) {
          alert("Please agree to the terms & privacy policy");
          return;
        }

        signUpButton.disabled = true;
        signUpButton.textContent = "Signing up...";

        try {
          const data = await apiCall("/auth/register", {
            method: "POST",
            body: JSON.stringify({ email, password }),
          });

          if (data.success) {
            alert("Registration successful! Redirecting...");
            localStorage.setItem("user_id", data.user_id);
            localStorage.setItem("user_email", data.email);

            // Redirect to main page
            setTimeout(() => {
              window.location.href = "/index.html";
            }, 500);
          }
        } catch (error) {
          alert("Registration failed: " + error.message);
          signUpButton.disabled = false;
          signUpButton.textContent = "Sign-Up";
        }
      });
    }
  }

  // Handle Sign-In Form
  if (signInSection) {
    const signInButton = signInSection.querySelector(".Sign-up");
    if (signInButton) {
      signInButton.addEventListener("click", async (e) => {
        e.preventDefault();

        const email = document.getElementById("email-in").value.trim();
        const password = document.getElementById("password-in").value;

        if (!email || !password) {
          alert("Please fill in all fields");
          return;
        }

        signInButton.disabled = true;
        signInButton.textContent = "Signing in...";

        try {
          const data = await apiCall("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
          });

          if (data.success) {
            alert("Login successful!");
            localStorage.setItem("user_id", data.user_id);
            localStorage.setItem("user_email", data.email);
            localStorage.setItem("user_name", data.name || "");

            // Redirect to main page
            setTimeout(() => {
              window.location.href = "/index.html";
            }, 500);
          }
        } catch (error) {
          alert("Login failed: " + error.message);
          signInButton.disabled = false;
          signInButton.textContent = "Sign-In";
        }
      });
    }
  }
}

// ==================== PRODUCT LISTING ====================

// Handle Sell Form Submission
function initSellForm() {
  const sellForm = document.querySelector(".sell-form");
  const listButton = document.querySelector(".list-btn");
  const uploadButton = document.getElementById("upload-images");
  let selectedFiles = [];

  if (!listButton) return;

  // Handle image upload
  if (uploadButton) {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/png,image/jpeg,image/jpg";
    fileInput.multiple = true;
    fileInput.style.display = "none";
    document.body.appendChild(fileInput);

    uploadButton.addEventListener("click", (e) => {
      e.preventDefault();
      fileInput.click();
    });

    fileInput.addEventListener("change", (e) => {
      selectedFiles = Array.from(e.target.files).slice(0, 4);

      if (selectedFiles.length > 0) {
        uploadButton.textContent = `${selectedFiles.length} Image(s) Selected`;
        uploadButton.style.backgroundColor = "#28a745";
      }
    });
  }

  // Handle condition selection
  const conditionTags = document.querySelectorAll(".tag-cnd");
  let selectedCondition = "";

  conditionTags.forEach((tag) => {
    tag.addEventListener("click", () => {
      conditionTags.forEach((t) => {
        t.classList.remove("selected");
        t.style.transform = "";
        t.style.boxShadow = "";
      });
      tag.classList.add("selected");
      tag.style.transform = "scale(1.05)";
      tag.style.boxShadow = "0 4px 8px rgba(0,0,0,0.2)";
      selectedCondition = tag.textContent.trim();
    });
  });

  // Handle form submission
  listButton.addEventListener("click", async (e) => {
    e.preventDefault();

    // Get form values without checking login
    const title = document.getElementById("item-title").value.trim();
    const category = document.getElementById("item-category").value;
    const price = document.getElementById("item-price").value;
    const description = document
      .getElementById("item-description")
      .value.trim();
    const location = document.getElementById("location").value.trim();
    const name = document.getElementById("name")?.value.trim() || "";
    const contact = document.getElementById("contact")?.value.trim() || "";

    if (
      !title ||
      !category ||
      !price ||
      !description ||
      !location ||
      !selectedCondition
    ) {
      alert("Please fill in all required fields and select a condition");
      return;
    }

    if (selectedFiles.length === 0) {
      alert("Please upload at least one image");
      return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("category", category);
    formData.append("condition", selectedCondition);
    formData.append("price", price);
    formData.append("description", description);
    formData.append("location", location);
    formData.append("brand", "");

    selectedFiles.forEach((file) => {
      formData.append("images", file);
    });

    listButton.textContent = "Listing...";
    listButton.disabled = true;

    try {
      const response = await fetch(`${API_BASE_URL}/products/list`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      const data = await response.json();

      if (data.error || data.issues) {
        throw new Error(data.error || data.issues.join(", "));
      }

      alert(
        `Product listed successfully!\n\nProduct ID: ${data.product_id}\nStatus: ${data.status}\n\nYour QR code has been generated!`
      );

      showQRCodeModal(data.nano_tag.qr_code, data.product_id);

      if (sellForm) sellForm.reset();
      selectedFiles = [];
      uploadButton.textContent = "Upload Images";
      uploadButton.style.backgroundColor = "#1f2937";
      conditionTags.forEach((t) => {
        t.classList.remove("selected");
        t.style.transform = "";
        t.style.boxShadow = "";
      });
      selectedCondition = "";
    } catch (error) {
      alert("Failed to list product: " + error.message);
    } finally {
      listButton.textContent = "List Item";
      listButton.disabled = false;
    }
  });
}

// Show QR Code Modal
function showQRCodeModal(qrCodeBase64, productId) {
  const modal = document.createElement("div");
  modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;

  modal.innerHTML = `
        <div style="background: white; padding: 2rem; border-radius: 8px; text-align: center; max-width: 500px;">
            <h3 style="margin-bottom: 1rem;">Your Product QR Code</h3>
            <img src="data:image/png;base64,${qrCodeBase64}" alt="QR Code" style="max-width: 300px; margin: 1rem auto;">
            <p style="margin: 1rem 0; color: #666;">Product ID: ${productId}</p>
            <p style="margin: 1rem 0; color: #666; font-size: 0.9rem;">
                Print this QR code and attach it to your product. After physical attachment, click "Activate" to make your listing live.
            </p>
            <button id="activate-btn" style="background: #28a745; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 6px; cursor: pointer; margin: 0.5rem;">
                Activate Listing
            </button>
            <button id="close-modal" style="background: #6c757d; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 6px; cursor: pointer; margin: 0.5rem;">
                Close
            </button>
        </div>
    `;

  document.body.appendChild(modal);

  // Handle activation
  document
    .getElementById("activate-btn")
    .addEventListener("click", async () => {
      try {
        await apiCall(`/products/activate/${productId}`, {
          method: "POST",
        });
        alert("Product activated successfully! Your listing is now live.");
        modal.remove();
        showContent("feed"); // Switch to feed view
      } catch (error) {
        alert("Activation failed: " + error.message);
      }
    });

  // Handle close
  document.getElementById("close-modal").addEventListener("click", () => {
    modal.remove();
  });
}

// ==================== PRODUCT FEED ====================

// Load products into feed
async function loadProductFeed(category = null) {
  try {
    const endpoint = category
      ? `/products/feed?category=${category}`
      : "/products/feed";
    const data = await apiCall(endpoint);

    const feedSection = document.querySelector("#feed .items-grid");
    if (!feedSection) return;

    // Clear existing items (keep first 3 static ones or clear all)
    feedSection.innerHTML = "";

    // Render products
    data.products.forEach((product) => {
      const article = createProductCard(product);
      feedSection.appendChild(article);
    });
  } catch (error) {
    console.error("Failed to load products:", error);
  }
}

// Create product card element
function createProductCard(product) {
  const article = document.createElement("article");

  // Get first image or placeholder
  const imageSrc =
    product.images && product.images.length > 0
      ? `/uploads/products/${product.images[0].split("/").pop()}`
      : "Assets/Images/placeholder.jpeg";

  article.innerHTML = `
        <img src="${imageSrc}" alt="${product.title}" onerror="this.src='Assets/Images/placeholder.jpeg'">
        <figcaption>
            <button onclick="toggleWatchlist('${product.product_id}')">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m14.479 19.374-.971.939a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5a5.2 5.2 0 0 1-.219 1.49"/>
                    <path d="M15 15h6"/><path d="M18 12v6"/>
                </svg>
            </button>
        </figcaption>
        <div class="card-info">
            <h4>${product.title}</h4>
            <h6>${product.category}</h6>
        </div>
        <button class="place">${product.location}</button>
        <div class="card-btn">
            <button class="price-tag">$ ${product.price}</button>
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

// View product details
async function viewProductDetails(productId) {
  try {
    const data = await apiCall(`/products/${productId}`);

    // Create detail modal
    const modal = document.createElement("div");
    modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            overflow-y: auto;
        `;

    const product = data.product;
    const verified = data.blockchain_verified
      ? "✓ Verified on Blockchain"
      : "Not verified";

    modal.innerHTML = `
            <div style="background: white; padding: 2rem; border-radius: 8px; max-width: 600px; max-height: 90vh; overflow-y: auto;">
                <h2 style="margin-bottom: 1rem;">${product.title}</h2>
                <div style="margin: 1rem 0;">
                    <img src="/uploads/products/${product.images[0]
                      ?.split("/")
                      .pop()}" alt="${
      product.title
    }" style="max-width: 100%; border-radius: 6px;">
                </div>
                <p style="color: #28a745; font-weight: bold;">${verified}</p>
                <p style="margin: 0.5rem 0;"><strong>Price:</strong> $${
                  product.price
                }</p>
                <p style="margin: 0.5rem 0;"><strong>Condition:</strong> ${
                  product.condition
                }</p>
                <p style="margin: 0.5rem 0;"><strong>Category:</strong> ${
                  product.category
                }</p>
                <p style="margin: 0.5rem 0;"><strong>Location:</strong> ${
                  product.location
                }</p>
                <p style="margin: 0.5rem 0;"><strong>Description:</strong> ${
                  product.description
                }</p>
                <p style="margin: 0.5rem 0;"><strong>Seller:</strong> ${
                  product.seller_name
                }</p>
                <p style="margin: 0.5rem 0;"><strong>Contact:</strong> ${
                  product.seller_contact
                }</p>
                <p style="margin: 0.5rem 0; color: #666; font-size: 0.9rem;"><strong>Views:</strong> ${
                  product.views
                }</p>
                <button onclick="this.closest('div').parentElement.remove()" style="background: #6c757d; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 6px; cursor: pointer; margin-top: 1rem; width: 100%;">
                    Close
                </button>
            </div>
        `;

    document.body.appendChild(modal);
  } catch (error) {
    alert("Failed to load product details: " + error.message);
  }
}

// Toggle watchlist
function toggleWatchlist(productId) {
  // Store in localStorage for now
  let watchlist = JSON.parse(localStorage.getItem("watchlist") || "[]");

  if (watchlist.includes(productId)) {
    watchlist = watchlist.filter((id) => id !== productId);
    alert("Removed from watchlist");
  } else {
    watchlist.push(productId);
    alert("Added to watchlist");
  }

  localStorage.setItem("watchlist", JSON.stringify(watchlist));
}

// ==================== USER LISTINGS ====================

// Load user's listings
async function loadUserListings() {
  try {
    const data = await apiCall("/user/listings");

    const listingsSection = document.querySelector("#itemlisted .items-grid");
    if (!listingsSection) return;

    listingsSection.innerHTML = "";

    data.listings.forEach((product) => {
      const article = createProductCard(product);
      listingsSection.appendChild(article);
    });
  } catch (error) {
    console.error("Failed to load listings:", error);
  }
}

// ==================== INITIALIZATION ====================

document.addEventListener("DOMContentLoaded", () => {
  console.log("SecondHand Marketplace Loaded");

  // Initialize authentication forms
  initAuthForms();

  // Initialize sell form if on main page
  if (document.querySelector(".sell-form")) {
    initSellForm();
  }

  // Load products on page load
  if (document.getElementById("feed")) {
    loadProductFeed();
  }

  // Check if user is logged in
  const userId = localStorage.getItem("user_id");
  const userName = localStorage.getItem("user_name");
  const userEmail = localStorage.getItem("user_email");

  if (userId) {
    console.log(`Welcome back, ${userName || userEmail}!`);
    updateUIForLoggedInUser(userName || userEmail);
  }

  // Load user listings when viewing that section
  const itemListedLink = document.getElementById("link-itemlisted");
  if (itemListedLink) {
    itemListedLink.addEventListener("click", () => {
      setTimeout(() => loadUserListings(), 100);
    });
  }

  // Reload feed when clicking on category links
  const categoryLinks = document.querySelectorAll('[id^="link-"]');
  categoryLinks.forEach((link) => {
    link.addEventListener("click", function () {
      const sectionId = this.id.replace("link-", "");
      // If it's a category, reload with filter
      const categories = [
        "electronics",
        "furniture",
        "vehicles",
        "apparel",
        "home",
        "sporting",
        "collectibles",
      ];
      if (categories.includes(sectionId)) {
        setTimeout(() => loadProductFeed(sectionId), 100);
      } else if (sectionId === "feed") {
        setTimeout(() => loadProductFeed(), 100);
      }
    });
  });
});

// Update UI for logged in user
function updateUIForLoggedInUser(name) {
  // You can add user name display, logout button, etc.
  const userButton = document.querySelector(".user");
  if (userButton) {
    userButton.title = `Logged in as ${name}`;
    userButton.style.border = "2px solid #28a745";
  }
}

// Make functions globally available
window.viewProductDetails = viewProductDetails;
window.toggleWatchlist = toggleWatchlist;
window.loadProductFeed = loadProductFeed;
