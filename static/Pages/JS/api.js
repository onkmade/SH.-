// ==================== API CONFIG ====================

const API_BASE_URL = localStorage.getItem("API_BASE_URL") || "http://localhost:5000";

// ==================== API WRAPPER ====================

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
    if (!response.ok || data.error) throw new Error(data.error || "API request failed");
    return data;
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

// ==================== AUTH ====================

function initAuthForms() {
  const signUpButton = document.querySelector("#new-account .Sign-up");
  const signInButton = document.querySelector("#login-account .Sign-up");

  if (signUpButton) {
    signUpButton.addEventListener("click", async (e) => {
      e.preventDefault();
      const email = document.getElementById("email-up").value.trim();
      const password = document.getElementById("password-up").value;
      const policyChecked = document.getElementById("policy-up").checked;

      if (!email || !password) return alert("Please fill in all fields");
      if (!policyChecked) return alert("Please agree to the terms");

      signUpButton.disabled = true;
      signUpButton.textContent = "Signing up...";

      try {
        const data = await apiCall("/auth/register", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        alert("Registration successful!");
        localStorage.setItem("user_id", data.user_id);
        localStorage.setItem("user_email", data.email);
        setTimeout(() => (window.location.href = "/index.html"), 500);
      } catch (err) {
        alert("Registration failed: " + err.message);
      } finally {
        signUpButton.disabled = false;
        signUpButton.textContent = "Sign-Up";
      }
    });
  }

  if (signInButton) {
    signInButton.addEventListener("click", async (e) => {
      e.preventDefault();
      const email = document.getElementById("email-in").value.trim();
      const password = document.getElementById("password-in").value;

      if (!email || !password) return alert("Please fill in all fields");

      signInButton.disabled = true;
      signInButton.textContent = "Signing in...";

      try {
        const data = await apiCall("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        alert("Login successful!");
        localStorage.setItem("user_id", data.user_id);
        localStorage.setItem("user_email", data.email);
        setTimeout(() => (window.location.href = "/index.html"), 500);
      } catch (err) {
        alert("Login failed: " + err.message);
      } finally {
        signInButton.disabled = false;
        signInButton.textContent = "Sign-In";
      }
    });
  }
}

// ==================== SELL FORM ====================

function initSellForm() {
  const sellForm = document.querySelector(".sell-form");
  const listButton = document.querySelector(".list-btn");
  const uploadButton = document.getElementById("upload-images");
  let selectedFiles = [];
  let selectedCondition = "";

  if (!listButton) return;

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
      uploadButton.textContent = `${selectedFiles.length} Image(s) Selected`;
      uploadButton.style.backgroundColor = "#28a745";
    });
  }

  const conditionTags = document.querySelectorAll(".tag-cnd");
  conditionTags.forEach((tag) => {
    tag.addEventListener("click", () => {
      conditionTags.forEach((t) => t.classList.remove("selected"));
      tag.classList.add("selected");
      selectedCondition = tag.textContent.trim();
    });
  });

  listButton.addEventListener("click", async (e) => {
    e.preventDefault();
    const title = document.getElementById("item-title").value.trim();
    const category = document.getElementById("item-category").value;
    const price = document.getElementById("item-price").value;
    const description = document.getElementById("item-description").value.trim();
    const location = document.getElementById("location").value.trim();

    if (!title || !category || !price || !description || !location || !selectedCondition)
      return alert("Please fill in all required fields.");

    const formData = new FormData();
    formData.append("title", title);
    formData.append("category", category);
    formData.append("condition", selectedCondition);
    formData.append("price", price);
    formData.append("description", description);
    formData.append("location", location);

    selectedFiles.forEach((f) => formData.append("images", f));

    listButton.disabled = true;
    listButton.textContent = "Listing...";

    try {
      const res = await fetch(`/sell`, { method: "POST", body: formData });
      const data = await res.json();

      if (!data.ok) throw new Error(data.error || data.issues?.join(", ") || "Unknown error");

      alert(`Product listed successfully!\nID: ${data.product_id}`);
      showQRCodeModal(data.nano_tag.qr_code, data.product_id);
      sellForm.reset();
    } catch (err) {
      alert("Failed to list product: " + err.message);
    } finally {
      listButton.disabled = false;
      listButton.textContent = "List Item";
    }
  });
}

// ==================== QR MODAL ====================

function showQRCodeModal(qrCode, productId) {
  const modal = document.createElement("div");
  modal.style.cssText = `
    position:fixed;top:0;left:0;width:100%;height:100%;
    background:rgba(0,0,0,0.8);display:flex;justify-content:center;align-items:center;z-index:9999;
  `;
  modal.innerHTML = `
    <div style="background:white;padding:2rem;border-radius:8px;text-align:center;">
      <h3>Your Product QR Code</h3>
      <img src="data:image/png;base64,${qrCode}" style="max-width:200px;margin:1rem;">
      <p>ID: ${productId}</p>
      <button id="activate" style="background:#28a745;color:white;padding:0.5rem 1rem;border:none;border-radius:6px;">Activate</button>
      <button id="close" style="background:#6c757d;color:white;padding:0.5rem 1rem;border:none;border-radius:6px;">Close</button>
    </div>
  `;
  document.body.appendChild(modal);

  modal.querySelector("#activate").addEventListener("click", async () => {
    try {
      await apiCall(`/products/activate/${productId}`, { method: "POST" });
      alert("Product activated successfully!");
      modal.remove();
      showContent("feed");
    } catch (err) {
      alert("Activation failed: " + err.message);
    }
  });

  modal.querySelector("#close").addEventListener("click", () => modal.remove());
}

// ==================== PRODUCT FEED ====================

let feedLoaded = false;

async function loadProductFeed(category = null) {
  if (feedLoaded && !category) return;
  feedLoaded = true;

  try {
    const endpoint = category ? `/products/feed?category=${category}` : `/products/feed`;
    const data = await apiCall(endpoint);

    const feedSection = document.querySelector("#feed .items-grid");
    if (!feedSection) return;
    feedSection.innerHTML = "";

    data.products.forEach((product) => feedSection.appendChild(createProductCard(product)));
  } catch (err) {
    console.error("Failed to load products:", err);
  }
}

function createProductCard(product) {
  const article = document.createElement("article");

  // Use the first valid image URL returned from the backend
  let imageSrc = product.images && product.images.length > 0
    ? product.images[0]
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

// ==================== PRODUCT DETAILS ====================

async function viewProductDetails(productId) {
  try {
    const data = await apiCall(`/products/${productId}`);
    const product = data.product;
    const verified = data.blockchain_verified ? "✓ Verified on Blockchain" : "Not verified";

    const modal = document.createElement("div");
    modal.style.cssText = `
      position:fixed;top:0;left:0;width:100%;height:100%;
      background:rgba(0,0,0,0.8);display:flex;justify-content:center;align-items:center;z-index:9999;
    `;
    modal.innerHTML = `
      <div style="background:white;padding:2rem;border-radius:8px;max-width:600px;overflow-y:auto;">
        <h2>${product.title}</h2>
        <img src="${product.images[0]}" style="max-width:100%;border-radius:6px;">
        <p><strong>Price:</strong> $${product.price}</p>
        <p><strong>Category:</strong> ${product.category}</p>
        <p><strong>Location:</strong> ${product.location}</p>
        <p><strong>Condition:</strong> ${product.condition}</p>
        <p style="color:#28a745">${verified}</p>
        <button onclick="this.closest('div').parentElement.remove()" style="margin-top:1rem;">Close</button>
      </div>
    `;
    document.body.appendChild(modal);
  } catch (err) {
    alert("Failed to load product: " + err.message);
  }
}

// ==================== WATCHLIST ====================

function toggleWatchlist(productId) {
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

// ==================== INIT ====================

document.addEventListener("DOMContentLoaded", () => {
  console.log("Marketplace Loaded");
  initAuthForms();
  if (document.querySelector(".sell-form")) initSellForm();
  if (document.getElementById("feed")) loadProductFeed();

  const userId = localStorage.getItem("user_id");
  if (userId) updateUIForLoggedInUser(localStorage.getItem("user_name") || localStorage.getItem("user_email"));

  document.querySelectorAll('[id^="link-"]').forEach((link) => {
    link.addEventListener("click", () => {
      const sectionId = link.id.replace("link-", "");
      const categories = ["electronics", "furniture", "vehicles", "apparel", "home", "sporting", "collectibles"];
      if (categories.includes(sectionId)) setTimeout(() => loadProductFeed(sectionId), 100);
      else if (sectionId === "feed") setTimeout(() => loadProductFeed(), 100);
    });
  });
});

function updateUIForLoggedInUser(name) {
  const userButton = document.querySelector(".user");
  if (userButton) {
    userButton.title = `Logged in as ${name}`;
    userButton.style.border = "2px solid #28a745";
  }
}

window.viewProductDetails = viewProductDetails;
window.toggleWatchlist = toggleWatchlist;
window.loadProductFeed = loadProductFeed;
