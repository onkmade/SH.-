(function () {
  const form = document.getElementById("sellerForm");
  const errorsEl = document.getElementById("formErrors");
  const preview = document.getElementById("imagePreview");
  const cards = document.getElementById("sellerCards");
  const MAX_MB = 5;
  const ALLOWED = ["jpg", "jpeg", "png"];

  // --- live validation ---
  function mark(el, ok) {
    el.classList.remove("valid", "invalid");
    el.classList.add(ok ? "valid" : "invalid");
  }

  function validateFieldset() {
    let ok = true;
    const title = document.getElementById("title");
    const category = document.getElementById("category");
    const condition = document.getElementById("condition");
    const price = document.getElementById("price");
    const images = document.getElementById("images");

    // requireds
    mark(title, !!title.value.trim()); ok = ok && !!title.value.trim();
    mark(category, !!category.value.trim()); ok = ok && !!category.value.trim();
    mark(condition, !!condition.value.trim()); ok = ok && !!condition.value.trim();

    const p = parseFloat(price.value);
    mark(price, !isNaN(p) && p > 0); ok = ok && (!isNaN(p) && p > 0);

    // files
    let filesOk = true;
    if (images.files.length === 0) filesOk = false;
    for (const f of images.files) {
      const ext = f.name.split(".").pop().toLowerCase();
      if (!ALLOWED.includes(ext)) filesOk = false;
      if (f.size > MAX_MB * 1024 * 1024) filesOk = false;
    }
    images.classList.toggle("invalid", !filesOk);
    images.classList.toggle("valid", filesOk);
    ok = ok && filesOk;

    errorsEl.textContent = ok ? "" : "Please complete all required fields and ensure images are JPG/PNG under 5MB.";
    return ok;
  }

  // image preview
  document.getElementById("images").addEventListener("change", () => {
    preview.innerHTML = "";
    for (const f of document.getElementById("images").files) {
      const url = URL.createObjectURL(f);
      const div = document.createElement("div");
      div.className = "card";
      div.innerHTML = `<img src="${url}" alt="" style="width:100%;height:160px;object-fit:cover;border-radius:8px" />`;
      preview.appendChild(div);
    }
    validateFieldset();
  });

  ["title","category","condition","price"].forEach(id => {
    const el = document.getElementById(id);
    el.addEventListener("input", validateFieldset);
    el.addEventListener("change", validateFieldset);
  });

  // --- card renderer ---
  function renderCard(p) {
    const img = (p.images && p.images[0]) ? `/media/${p.images[0]}` : "Assets/Images/placeholder.jpg";
    const nano = p.nano_tag?.tag_id || "—";
    const hashShort = (p.json_hash || "").slice(0, 10);
    const ai = p.ai_score ?? "—";
    const verified = p.verification_status || "unverified";

    const el = document.createElement("article");
    el.className = "card";
    el.innerHTML = `
      <img src="${img}" alt="" style="width:100%;height:160px;object-fit:cover;border-radius:8px" />
      <h3 style="margin:8px 0 0">${p.title}</h3>
      <div class="hint">${p.brand || ""} ${p.model || ""}</div>
      <div style="margin:6px 0;">
        <span class="tag">${p.condition}</span>
        <span class="tag">₹ ${p.price}</span>
        <span class="tag">AI ${ai}</span>
        <span class="tag">${verified}</span>
      </div>
      <div class="hint">Nano-tag: ${nano}</div>
      <div class="hint">JSON: ${hashShort ? hashShort + "…" : "—"}</div>

      <div style="display:flex;gap:8px;margin-top:10px">
        <button data-action="activate" data-id="${p.product_id}">Activate</button>
        <button data-action="verify" data-id="${p.product_id}">Verify</button>
        <button data-action="json" data-id="${p.product_id}">JSON</button>
        <button data-action="transfer" data-id="${p.product_id}">Transfer</button>
      </div>
    `;

    el.addEventListener("click", async (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      const id = btn.dataset.id;
      try {
        if (btn.dataset.action === "activate") {
          const r = await window.api.activateProduct(id);
          alert("Activated ✔  Block: " + r.block_id);
          refreshCards();
        } else if (btn.dataset.action === "verify") {
          const r = await window.api.verifyProduct(id);
          alert("Verified ✔  Hash: " + r.hash.slice(0,10) + "…");
          refreshCards();
        } else if (btn.dataset.action === "json") {
          const j = await window.api.getProductJSON(id);
          alert("JSON OK. Keys: " + Object.keys(j).join(", "));
          console.log("Product JSON", j);
        } else if (btn.dataset.action === "transfer") {
          const newOwner = prompt("New Owner ID?");
          if (!newOwner) return;
          const r = await window.api.transferOwnership(id, newOwner);
          alert("Transfer recorded ✔  Block: " + r.block_id);
          refreshCards();
        }
      } catch (err) {
        alert("Error: " + err.message);
      }
    });

    return el;
  }

  async function refreshCards() {
    try {
      const { products } = await window.api.getFeed();
      cards.innerHTML = "";
      products.forEach(p => cards.appendChild(renderCard(p)));
    } catch (e) {
      console.error(e);
    }
  }

  // --- submit handler ---
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!validateFieldset()) return;

    const fd = new FormData(form);
    // ensure all images included (input has name="images")
    const submitBtn = document.getElementById("submitBtn");
    submitBtn.disabled = true; submitBtn.textContent = "Submitting…";

    try {
      const res = await window.api.listProduct(fd);
      alert(`Listed ✔  ID: ${res.product_id} | AI: ${res.ai_score}`);
      form.reset();
      preview.innerHTML = "";
      await refreshCards();
    } catch (err) {
      errorsEl.textContent = err.message || "Submit failed";
    } finally {
      submitBtn.disabled = false; submitBtn.textContent = "Submit";
    }
  });

  // initial
  refreshCards();
})();
