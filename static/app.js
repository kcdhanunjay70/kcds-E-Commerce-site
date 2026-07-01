const state = {
  products: [],
  categories: [],
  cart: { items: [], subtotal: 0, shipping: 0, tax: 0, total: 0, count: 0 },
  orders: [],
  stats: {},
  query: "",
  category: "",
  orderQuery: "",
};

const statsEl = document.getElementById("stats");
const productGrid = document.getElementById("productGrid");
const categoryFilter = document.getElementById("categoryFilter");
const searchInput = document.getElementById("searchInput");
const cartList = document.getElementById("cartList");
const cartTotals = document.getElementById("cartTotals");
const clearCart = document.getElementById("clearCart");
const checkoutForm = document.getElementById("checkoutForm");
const checkoutMessage = document.getElementById("checkoutMessage");
const productForm = document.getElementById("admin");
const productMessage = document.getElementById("productMessage");
const orderRows = document.getElementById("orderRows");
const orderSearch = document.getElementById("orderSearch");

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.success === false) {
    throw new Error(data.message || "Request failed");
  }
  return data;
}

function rupees(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function renderStats() {
  const cards = [
    ["Products", state.stats.productCount || 0],
    ["Orders", state.stats.orderCount || 0],
    ["Revenue", rupees(state.stats.revenue || 0)],
    ["Stock", state.stats.stock || 0],
    ["Cart", state.cart.count || 0],
  ];
  statsEl.innerHTML = cards.map(([label, value]) => `
    <article class="stat"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span></article>
  `).join("");
}

function renderFilters() {
  const current = categoryFilter.value;
  categoryFilter.innerHTML = `<option value="">All Categories</option>${state.categories.map((item) => `<option>${escapeHtml(item)}</option>`).join("")}`;
  categoryFilter.value = state.categories.includes(current) ? current : "";
}

function renderProducts() {
  const query = state.query.toLowerCase();
  const products = state.products.filter((item) => {
    const text = [item.name, item.category, item.description, item.sku].join(" ").toLowerCase();
    return (!state.category || item.category === state.category) && (!query || text.includes(query));
  });
  productGrid.innerHTML = products.map((item) => `
    <article class="product-card">
      <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.name)}">
      <div class="product-body">
        <span>${escapeHtml(item.category)} | ${escapeHtml(item.rating)} star</span>
        <strong>${escapeHtml(item.name)}</strong>
        <p>${escapeHtml(item.description)}</p>
        <div class="product-meta">
          <b>${rupees(item.price)}</b>
          <small>${escapeHtml(item.stock)} in stock</small>
        </div>
        <button type="button" data-add-cart="${escapeHtml(item.id)}">Add to Cart</button>
      </div>
    </article>
  `).join("") || `<article class="product-card empty"><div class="product-body"><strong>No products found</strong><p>Try another category or search.</p></div></article>`;
  productGrid.querySelectorAll("[data-add-cart]").forEach((button) => {
    button.addEventListener("click", () => addToCart(button.dataset.addCart));
  });
}

function renderCart() {
  cartList.innerHTML = state.cart.items.map((item) => `
    <article class="cart-item">
      <img src="${escapeHtml(item.product.image)}" alt="${escapeHtml(item.product.name)}">
      <div>
        <strong>${escapeHtml(item.product.name)}</strong>
        <p>${rupees(item.product.price)} x ${escapeHtml(item.quantity)}</p>
      </div>
      <div class="cart-controls">
        <button type="button" data-cart-dec="${escapeHtml(item.product.id)}">-</button>
        <b>${escapeHtml(item.quantity)}</b>
        <button type="button" data-cart-inc="${escapeHtml(item.product.id)}">+</button>
      </div>
      <strong>${rupees(item.lineTotal)}</strong>
    </article>
  `).join("") || `<article class="cart-item empty"><div><strong>Your cart is empty</strong><p>Add products to start checkout.</p></div></article>`;

  cartTotals.innerHTML = `
    <span><small>Subtotal</small><b>${rupees(state.cart.subtotal)}</b></span>
    <span><small>Shipping</small><b>${rupees(state.cart.shipping)}</b></span>
    <span><small>Tax</small><b>${rupees(state.cart.tax)}</b></span>
    <span><small>Total</small><b>${rupees(state.cart.total)}</b></span>
  `;
  cartList.querySelectorAll("[data-cart-inc]").forEach((button) => {
    button.addEventListener("click", () => updateCart(button.dataset.cartInc, 1));
  });
  cartList.querySelectorAll("[data-cart-dec]").forEach((button) => {
    button.addEventListener("click", () => updateCart(button.dataset.cartDec, -1));
  });
}

function renderOrders() {
  const query = state.orderQuery.toLowerCase();
  const rows = state.orders.filter((item) => {
    const text = [item.orderNo, item.customerName, item.email, item.phone, item.status].join(" ").toLowerCase();
    return !query || text.includes(query);
  });
  orderRows.innerHTML = rows.map((item) => `
    <tr>
      <td><strong>${escapeHtml(item.orderNo)}</strong><br>${escapeHtml(new Date(item.createdAt).toLocaleString())}</td>
      <td>${escapeHtml(item.customerName)}<br>${escapeHtml(item.email)} | ${escapeHtml(item.phone)}</td>
      <td>${escapeHtml(item.items.map((orderItem) => `${orderItem.productName} x ${orderItem.quantity}`).join(", "))}</td>
      <td><strong>${rupees(item.total)}</strong><br>Tax ${rupees(item.tax)}</td>
      <td><span class="status">${escapeHtml(item.status)}</span></td>
    </tr>
  `).join("") || `<tr><td colspan="5">No orders placed yet.</td></tr>`;
}

async function refresh() {
  const [productsData, cartData, ordersData, statsData] = await Promise.all([
    api("/api/products"),
    api("/api/cart"),
    api("/api/orders"),
    api("/api/stats"),
  ]);
  state.products = productsData.products || [];
  state.categories = productsData.categories || [];
  state.cart = cartData.cart || state.cart;
  state.orders = ordersData.orders || [];
  state.stats = statsData.stats || {};
  renderFilters();
  renderProducts();
  renderCart();
  renderOrders();
  renderStats();
}

async function addToCart(productId) {
  await api("/api/cart", { method: "POST", body: JSON.stringify({ productId, quantity: 1 }) });
  await refresh();
}

async function updateCart(productId, delta) {
  const item = state.cart.items.find((cartItem) => String(cartItem.product.id) === String(productId));
  const quantity = Math.max(0, (item?.quantity || 0) + delta);
  await api(`/api/cart/${productId}`, { method: "PATCH", body: JSON.stringify({ quantity }) });
  await refresh();
}

searchInput.addEventListener("input", () => {
  state.query = searchInput.value;
  renderProducts();
});

categoryFilter.addEventListener("change", () => {
  state.category = categoryFilter.value;
  renderProducts();
});

orderSearch.addEventListener("input", () => {
  state.orderQuery = orderSearch.value;
  renderOrders();
});

clearCart.addEventListener("click", async () => {
  await api("/api/cart", { method: "DELETE" });
  await refresh();
});

checkoutForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  checkoutMessage.textContent = "Placing order...";
  checkoutMessage.className = "form-message";
  try {
    const payload = Object.fromEntries(new FormData(checkoutForm).entries());
    const data = await api("/api/orders", { method: "POST", body: JSON.stringify(payload) });
    checkoutForm.reset();
    checkoutMessage.textContent = `Order ${data.order.orderNo} placed successfully.`;
    checkoutMessage.className = "form-message ok";
    await refresh();
  } catch (error) {
    checkoutMessage.textContent = error.message;
    checkoutMessage.className = "form-message bad";
  }
});

productForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  productMessage.textContent = "Saving product...";
  productMessage.className = "form-message";
  try {
    const payload = Object.fromEntries(new FormData(productForm).entries());
    await api("/api/products", { method: "POST", body: JSON.stringify(payload) });
    productForm.reset();
    productMessage.textContent = "Product saved successfully.";
    productMessage.className = "form-message ok";
    await refresh();
  } catch (error) {
    productMessage.textContent = error.message;
    productMessage.className = "form-message bad";
  }
});

refresh().catch((error) => {
  statsEl.innerHTML = `<article class="stat"><strong>!</strong><span>${escapeHtml(error.message)}</span></article>`;
});
