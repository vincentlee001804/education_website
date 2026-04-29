const API_BASE = "/api";

function readToken() {
  try {
    return window.localStorage.getItem("access_token");
  } catch (_) {
    return null;
  }
}

function authHeaders() {
  const token = readToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

async function apiFetch(path, options = {}) {
  const url = path.startsWith("/") ? path : `/${path}`;
  const headers = Object.assign({}, options.headers || {});
  const token = readToken();

  // If this looks like an authenticated call, attach token (opt-in).
  if (options.auth !== false && token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // For JSON requests we pass `body` as a JSON string; ensure content-type is set,
  // otherwise Flask's request.get_json() may return null.
  if (!headers["Content-Type"] && options.body) {
    if (typeof options.body === "string") {
      const trimmed = options.body.trim();
      if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
        headers["Content-Type"] = "application/json";
      }
    } else {
      headers["Content-Type"] = "application/json";
    }
  }

  const res = await fetch(url, Object.assign({}, options, { headers }));
  let payload = null;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    payload = await res.json();
  } else {
    payload = null;
  }

  if (!res.ok) {
    const message = payload?.error?.message || `Request failed (${res.status})`;
    const err = new Error(message);
    err.details = payload;
    throw err;
  }

  return payload;
}

function apiGet(url, options = {}) {
  return apiFetch(url, Object.assign({}, options, { method: "GET" }));
}

function apiPost(url, body, options = {}) {
  return apiFetch(url, Object.assign({}, options, { method: "POST", body: JSON.stringify(body || {}) }));
}

function apiPatch(url, body, options = {}) {
  return apiFetch(url, Object.assign({}, options, { method: "PATCH", body: JSON.stringify(body || {}) }));
}

function apiDelete(url, options = {}) {
  return apiFetch(url, Object.assign({}, options, { method: "DELETE" }));
}

async function downloadWithAuth(url, filenameBase = "download") {
  const token = readToken();
  if (!token) throw new Error("Not logged in");
  const res = await fetch(url, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const payloadText = await res.text().catch(() => "");
    throw new Error(payloadText || `Download failed (${res.status})`);
  }
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const cd = res.headers.get("content-disposition") || "";
  const match = cd.match(/filename="?([^"]+)"?/i);
  const filename = match ? match[1] : filenameBase;
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}

async function apiUploadFormData(url, formData, options = {}) {
  const token = readToken();
  if (!token && options.auth !== false) {
    throw new Error("Not logged in");
  }

  const headers = Object.assign({}, options.headers || {});
  if (token && options.auth !== false) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // IMPORTANT: Do not set Content-Type manually for FormData.
  const res = await fetch(url.startsWith("/") ? url : `/${url}`, {
    method: "POST",
    headers,
    body: formData,
  });

  let payload = null;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    payload = await res.json();
  } else {
    payload = null;
  }

  if (!res.ok) {
    const message = payload?.error?.message || `Upload failed (${res.status})`;
    const err = new Error(message);
    err.details = payload;
    throw err;
  }

  return payload;
}

