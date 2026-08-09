const API_BASE = "http://127.0.0.1:8000/api/v1";

async function apiFetch(endpoint, options = {}) {
    const accessToken = localStorage.getItem("access_token");

    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };

    if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            headers["Authorization"] = `Bearer ${localStorage.getItem("access_token")}`;
            return fetch(`${API_BASE}${endpoint}`, { ...options, headers });
        } else {
            window.location.href = "index.html";
            return;
        }
    }

    return response;
}

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return false;

    const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: refreshToken }),
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem("access_token", data.access);
        return true;
    }
    return false;
}

function formatApiError(errorData) {
    if (typeof errorData === "string") return errorData;
    if (errorData.detail) return errorData.detail;

    function stringifyError(value) {
        if (Array.isArray(value)) {
            return value.map(stringifyError).filter(Boolean).join(" ");
        }
        if (value && typeof value === "object") {
            return Object.entries(value)
                .map(([k, v]) => `${k.replace(/_/g, " ")}: ${stringifyError(v)}`)
                .join(", ");
        }
        return String(value);
    }

    const lines = [];
    for (const [field, messages] of Object.entries(errorData)) {
        const fieldLabel = field.replace(/_/g, " ");
        lines.push(`${fieldLabel}: ${stringifyError(messages)}`);
    }
    return lines.join(" | ");
}


async function loadAlertBadge() {
    const badgeEl = document.getElementById("alert-badge-count");
    if (!badgeEl) return;

    const response = await apiFetch("/alerts/?resolved=false");
    if (!response || !response.ok) return;

    const data = await response.json();
    const list = data.results ?? data;
    const count = list.length;

    if (count > 0) {
        badgeEl.textContent = count > 99 ? "99+" : count;
        badgeEl.style.display = "inline-flex";
    } else {
        badgeEl.style.display = "none";
    }
}

document.addEventListener("DOMContentLoaded", loadAlertBadge);