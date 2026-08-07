document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "index.html";
});

const KPI_LABELS = {
    revenue_30d: "Revenue (Last 30 Days)",
    active_alerts: "Active Alerts",
    critical_alerts: "Critical Alerts",
    low_stock_count: "Low Stock Alerts",
    sales_today: "Sales Today",
    active_vendors: "Active Vendors",
    total_inventory_value: "Total Inventory Value",
};

async function loadRoleAwareDashboard() {
    const response = await apiFetch("/dashboard/role-aware/");
    if (!response || !response.ok) return;
    const data = await response.json();

    document.getElementById("dashboard-heading").textContent = `Welcome, ${data.role_display}`;

    let sectionHtml = "";
    if (data.view_type === "executive") {
        sectionHtml = `
            <h3>Executive Overview</h3>
            <p><strong>Revenue (30 days):</strong> ${data.revenue_last_30_days}</p>
            <p><strong>Active Alerts:</strong> ${data.active_alerts} (${data.critical_alerts} critical)</p>
            <p><strong>Active Vendors:</strong> ${data.active_vendors}</p>`;
    } else if (data.view_type === "financial") {
        sectionHtml = `
            <h3>Financial Overview</h3>
            <p><strong>Revenue (30 days):</strong> ${data.revenue_last_30_days}</p>`;
    } else if (data.view_type === "warehouse_operations") {
        sectionHtml = `
            <h3>Warehouse Operations</h3>
            <p><strong>Low Stock Alerts:</strong> ${data.low_stock_alerts}</p>
            <p><strong>Expiry Alerts:</strong> ${data.expiry_alerts}</p>`;
    } else if (data.view_type === "sales_floor") {
        sectionHtml = `
            <h3>Today's Sales</h3>
            <p><strong>Transactions:</strong> ${data.sales_today_count}</p>
            <p><strong>Revenue Today:</strong> ${data.sales_today_revenue}</p>`;
    } else if (data.view_type === "procurement") {
        sectionHtml = `
            <h3>Procurement Overview</h3>
            <p><strong>Pending Reorder Alerts:</strong> ${data.pending_reorder_alerts}</p>
            <p><strong>Active Vendors:</strong> ${data.active_vendors}</p>`;
    } else {
        sectionHtml = `<p>No specialized view configured for this role yet.</p>`;
    }

    let roleSection = document.getElementById("role-overview-section");
    if (!roleSection) {
        roleSection = document.createElement("section");
        roleSection.id = "role-overview-section";
        document.getElementById("kpi-panel").insertAdjacentElement("afterend", roleSection);
    }
    roleSection.innerHTML = sectionHtml;
}

async function loadStockTables() {
    const response = await apiFetch("/dashboard/stock/");
    if (!response || !response.ok) return;
    const data = await response.json();

    const productBody = document.querySelector("#by-product-table tbody");
    productBody.innerHTML = "";
    data.by_product.forEach((row) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${row.product__sku}</td><td>${row.product__name}</td><td>${row.total_quantity}</td>`;
        productBody.appendChild(tr);
    });

    const warehouseBody = document.querySelector("#by-warehouse-table tbody");
    warehouseBody.innerHTML = "";
    data.by_warehouse.forEach((row) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${row.warehouse__name}</td><td>${row.warehouse__branch__name ?? "—"}</td><td>${row.total_quantity}</td>`;
        warehouseBody.appendChild(tr);
    });
}

async function loadKPIs() {
    const response = await apiFetch("/dashboard/kpis/");
    if (!response || !response.ok) return;
    const data = await response.json();

    const cardsEl = document.getElementById("kpi-cards");
    cardsEl.innerHTML = "";

    data.selected_kpis.forEach((key) => {
        const kpi = data.kpi_data[key];
        if (!kpi || kpi.error) return;
        const card = document.createElement("div");
        card.className = "kpi-card";
        card.innerHTML = `<div class="kpi-label">${kpi.label}</div><div class="kpi-value">${kpi.value}</div>`;
        cardsEl.appendChild(card);
    });

    window._availableKpis = data.available_kpis;
    window._selectedKpis = data.selected_kpis;
}

document.getElementById("customize-kpis-btn").addEventListener("click", () => {
    const checkboxesEl = document.getElementById("kpi-checkboxes");
    checkboxesEl.innerHTML = window._availableKpis.map((key) => {
        const checked = window._selectedKpis.includes(key) ? "checked" : "";
        const label = KPI_LABELS[key] || key;
        return `<label class="kpi-checkbox-label"><input type="checkbox" value="${key}" ${checked}> ${label}</label>`;
    }).join("");
    document.getElementById("kpi-modal-overlay").style.display = "flex";
});

document.getElementById("cancel-kpis-btn").addEventListener("click", () => {
    document.getElementById("kpi-modal-overlay").style.display = "none";
});

document.getElementById("save-kpis-btn").addEventListener("click", async () => {
    const checked = Array.from(document.querySelectorAll("#kpi-checkboxes input:checked")).map((el) => el.value);

    const response = await apiFetch("/dashboard/kpis/", {
        method: "POST",
        body: JSON.stringify({ selected_kpis: checked }),
    });

    if (response && response.ok) {
        document.getElementById("kpi-modal-overlay").style.display = "none";
        loadKPIs();
    }
});

loadKPIs();
loadRoleAwareDashboard();
loadStockTables();