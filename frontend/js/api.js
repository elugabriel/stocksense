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


const NAV_VISIBILITY = {
    super_admin: "all",
    org_admin: "all",
    executive: ["dashboard.html", "products.html", "movements.html", "vendors.html", "sales.html", "forecasting.html", "comparisons.html"],
    branch_manager: ["dashboard.html", "products.html", "stock-actions.html", "locations.html", "movements.html", "vendors.html", "sales.html", "comparisons.html"],
    warehouse_manager: ["dashboard.html", "products.html", "stock-actions.html", "locations.html", "movements.html"],
    inventory_officer: ["dashboard.html", "products.html", "stock-actions.html", "movements.html"],
    procurement_officer: ["dashboard.html", "products.html", "vendors.html", "purchase-orders.html"],
    sales_staff: ["dashboard.html", "products.html", "sales.html"],
    accountant: ["dashboard.html", "products.html", "sales.html", "forecasting.html", "comparisons.html"],
    vendor: ["dashboard.html"],
    customer: ["dashboard.html"],
};

async function applyRoleBasedNav() {
    const navbar = document.querySelector(".navbar");

    const response = await apiFetch("/dashboard/role-aware/");
    if (!response || !response.ok) {
        if (navbar) navbar.classList.add("nav-ready");
        return;
    }
    const data = await response.json();
    const role = data.user_role;

    const allowedPages = NAV_VISIBILITY[role];
    if (allowedPages === "all" || !allowedPages) {
        if (navbar) navbar.classList.add("nav-ready");
        return;
    }

    document.querySelectorAll(".navbar .nav-link").forEach((link) => {
        const href = link.getAttribute("href");
        if (link.classList.contains("alert-bell-link")) return;
        if (!allowedPages.includes(href)) {
            link.style.display = "none";
        }
    });

    const usersLink = document.querySelector('a[href="users.html"]');
    if (usersLink && !allowedPages.includes("users.html")) {
        usersLink.style.display = "none";
    }

    if (navbar) navbar.classList.add("nav-ready");
}

document.addEventListener("DOMContentLoaded", applyRoleBasedNav);

document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("nav-toggle");
    const links = document.getElementById("nav-links");
    if (toggle && links) {
        toggle.addEventListener("click", () => {
            links.classList.toggle("nav-links-open");
        });
    }
});