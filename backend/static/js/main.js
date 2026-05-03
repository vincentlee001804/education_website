function writeText(el, text) {
  if (!el) return;
  el.textContent = text;
}

function setStatusMessage(el, message, type = "info") {
  if (!el) return;
  el.className = "status";
  if (type === "good") el.classList.add("good");
  if (type === "bad") el.classList.add("bad");
  el.textContent = message;
}

async function withButtonLoading(btn, pendingText, callback) {
  if (!btn) return callback();
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = pendingText;
  try {
    return await callback();
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

function showToast(message, type = "info", durationMs = 3500) {
  let stack = document.getElementById("toast-stack");
  if (!stack) {
    stack = document.createElement("div");
    stack.id = "toast-stack";
    stack.className = "toast-stack";
    document.body.appendChild(stack);
  }
  
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  
  const icon = document.createElement("div");
  icon.className = "toast-icon";
  if (type === "good") {
    icon.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
  } else {
    icon.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
  }
  
  const content = document.createElement("div");
  content.className = "toast-content";
  content.textContent = message;
  
  toast.appendChild(icon);
  toast.appendChild(content);

  // Add a Login action if the message is about logging in
  if (message.toLowerCase().includes("log in") || message.toLowerCase().includes("sign in")) {
    const action = document.createElement("a");
    action.href = "/login";
    action.className = "toast-action";
    action.textContent = "Login";
    toast.appendChild(action);
    durationMs = 6000; // Keep it longer if it has an action
  }
  
  stack.appendChild(toast);
  
  window.setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    window.setTimeout(() => {
      toast.remove();
      if (stack && !stack.children.length) stack.remove();
    }, 300);
  }, durationMs);
}

window.setStatusMessage = setStatusMessage;
window.withButtonLoading = withButtonLoading;
window.showToast = showToast;

async function updateCartBadge() {
  const badgeEl = document.getElementById("cart-badge");
  if (!badgeEl) return;
  try {
    const payload = await apiGet("/api/cart", { auth: true });
    const cart = payload.data || {};
    const items = cart.items || [];
    let count = 0;
    items.forEach(it => { count += Number(it.quantity || 1); });
    if (count > 0) {
      badgeEl.textContent = String(count);
      badgeEl.style.display = "flex";
    } else {
      badgeEl.style.display = "none";
    }
  } catch (e) {
    badgeEl.style.display = "none";
  }
}
window.updateCartBadge = updateCartBadge;

async function refreshAuthUI() {
  const token = readToken?.() ?? null;
  const loginLinks = document.querySelectorAll("[data-auth='logged-out']");
  const userLinks = document.querySelectorAll("[data-auth='logged-in']");
  const avatarContainer = document.getElementById("user-avatar-container");
  const adminLinks = document.querySelectorAll("[data-auth='admin-only']");

  if (!token) {
    loginLinks.forEach((x) => {
      if (x.tagName === 'DIV' || x.tagName === 'SECTION') {
        x.style.display = "flex";
      } else {
        x.style.display = "inline-flex";
      }
    });
    userLinks.forEach((x) => (x.style.display = "none"));
    adminLinks.forEach((x) => (x.style.display = "none"));
    if (avatarContainer) avatarContainer.style.display = "none";
    return;
  }

  try {
    const payload = await apiGet("/api/auth/me", { auth: true });
    const user = payload.data;
    const roles = user.roles || [];
    const email = user.email || "User";
    const displayName = user.display_name || email.split('@')[0];
    const isAdmin = roles.includes("admin") || roles.includes("moderator");

    loginLinks.forEach((x) => (x.style.display = "none"));
    userLinks.forEach((x) => {
      if (x.tagName === 'DIV' || x.tagName === 'SECTION') {
        x.style.display = "flex";
      } else if (x.tagName === 'A' && x.classList.contains('dropdown-item')) {
        x.style.display = "flex";
      } else {
        x.style.display = "inline-flex";
      }
    });
    
    adminLinks.forEach((x) => {
      if (isAdmin) {
        x.style.display = x.classList.contains('dropdown-item') ? "flex" : "inline-flex";
      } else {
        x.style.display = "none";
      }
    });

    if (avatarContainer) {
      avatarContainer.style.display = "block";
      
      // Update avatar image
      const avatarImg = document.getElementById("user-avatar-img");
      if (avatarImg) {
        avatarImg.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=002B5B&color=fff`;
      }
      
      // Update dropdown info
      const ddName = document.getElementById("dropdown-user-name");
      const ddEmail = document.getElementById("dropdown-user-email");
      if (ddName) ddName.textContent = displayName;
      if (ddEmail) ddEmail.textContent = email;
    }

    window.__ME = user;
  } catch (e) {
    // Token invalid/expired.
    try {
      window.localStorage.removeItem("access_token");
    } catch (_) {}
    window.__ME = null;
    
    loginLinks.forEach((x) => (x.style.display = "inline-flex"));
    userLinks.forEach((x) => (x.style.display = "none"));
    adminLinks.forEach((x) => (x.style.display = "none"));
    if (avatarContainer) avatarContainer.style.display = "none";
  }
}

function setupDropdown() {
  const avatarBtn = document.getElementById("user-avatar-btn");
  const userDropdownMenu = document.getElementById("user-dropdown-menu");
  const notifBtn = document.getElementById("notification-btn");
  const notifDropdownMenu = document.getElementById("notification-dropdown");
  
  // Toggle user dropdown on click
  if (avatarBtn && userDropdownMenu) {
    avatarBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      userDropdownMenu.classList.toggle("show");
      if (notifDropdownMenu) notifDropdownMenu.classList.remove("show");
    });
  }

  // Toggle notification dropdown on click
  if (notifBtn && notifDropdownMenu) {
    notifBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      notifDropdownMenu.classList.toggle("show");
      if (userDropdownMenu) userDropdownMenu.classList.remove("show");
    });
  }

  // Close dropdowns when clicking outside
  document.addEventListener("click", (e) => {
    if (userDropdownMenu && userDropdownMenu.classList.contains("show") && !userDropdownMenu.contains(e.target)) {
      userDropdownMenu.classList.remove("show");
    }
    if (notifDropdownMenu && notifDropdownMenu.classList.contains("show") && !notifDropdownMenu.contains(e.target)) {
      notifDropdownMenu.classList.remove("show");
    }
  });
}

function setupLogout() {
  const btns = document.querySelectorAll(".logout-btn");
  btns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      try {
        window.localStorage.removeItem("access_token");
      } catch (_) {}
      window.__ME = null;
      location.href = "/";
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupLogout();
  setupDropdown();
  if (typeof readToken === "function" && typeof apiGet === "function") {
    refreshAuthUI().then(() => {
      if (window.__ME) {
        updateCartBadge();
      }
    });
  }
});

