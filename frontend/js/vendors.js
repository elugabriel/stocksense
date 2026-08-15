document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "index.html";
});

let vendors = [];

async function loadVendors() {
    const response = await apiFetch("/vendors/");
    if (!response || !response.ok) return;
    const data = await response.json();
    vendors = data.results ?? data;

    const tbody = document.querySelector("#vendors-table tbody");
    tbody.innerHTML = "";

    vendors.forEach((v) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${v.name}</td>
            <td>${v.country || "—"}</td>
            <td>${v.default_lead_time_days ?? "—"}</td>
            <td>${v.status}</td>
            <td>${v.performance_score ?? "Not yet scored"}</td>
            <td>
                <button class="perf-btn" data-id="${v.id}" data-name="${v.name}">View Performance</button>
                <button class="edit-btn" data-id="${v.id}">Edit</button>
                <button class="delete-btn" data-id="${v.id}">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    document.querySelectorAll(".perf-btn").forEach((btn) => {
        btn.addEventListener("click", () => showPerformance(btn.dataset.id, btn.dataset.name));
    });
    document.querySelectorAll(".edit-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const vendor = vendors.find((v) => v.id == btn.dataset.id);
            openVendorModal(vendor);
        });
    });
    document.querySelectorAll(".delete-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            if (!confirm("Delete this vendor? This cannot be undone.")) return;
            const response = await apiFetch(`/vendors/${btn.dataset.id}/`, { method: "DELETE" });
            if (response && response.ok) {
                loadVendors();
            } else {
                alert("Failed to delete vendor. They may still have purchase orders tied to them.");
            }
        });
    });
}

async function showPerformance(vendorId, vendorName) {
    document.getElementById("perf-title").textContent = `Performance — ${vendorName}`;
    document.getElementById("perf-content").innerHTML = "Loading...";
    document.getElementById("perf-overlay").style.display = "flex";

    const [perfRes, costRes, historyRes] = await Promise.all([
        apiFetch(`/vendors/${vendorId}/performance/`),
        apiFetch(`/vendors/${vendorId}/cost_trends/`),
        apiFetch(`/vendors/${vendorId}/purchase_history/`),
    ]);

    let html = "";

    if (perfRes && perfRes.ok) {
        const perf = await perfRes.json();
        html += `
            <p><strong>Total Orders:</strong> ${perf.total_orders}</p>
            <p><strong>Received Orders:</strong> ${perf.received_orders}</p>
            <p><strong>On-Time Rate:</strong> ${perf.on_time_rate_percent ?? "N/A"}%</p>
            <p><strong>Average Lead Time:</strong> ${perf.average_lead_time_days ?? "N/A"} days</p>
            <p><strong>Quoted Lead Time:</strong> ${perf.quoted_lead_time_days ?? "N/A"} days</p>
        `;
    }

    if (costRes && costRes.ok) {
        const cost = await costRes.json();
        if (cost.cost_history && cost.cost_history.length > 0) {
            html += `<h4>Cost History</h4><ul>`;
            cost.cost_history.forEach((c) => {
                html += `<li>${c.order_date} — ${c.product_sku}: ${c.unit_cost} (PO ${c.order_number})</li>`;
            });
            html += `</ul>`;
        } else {
            html += `<p><em>No purchase order history yet.</em></p>`;
        }
    }

    if (historyRes && historyRes.ok) {
        const orders = await historyRes.json();
        const list = orders.results ?? orders;
        if (list.length > 0) {
            html += `<h4>Purchase Order History</h4><table><thead><tr><th>Order #</th><th>Status</th><th>Expected</th><th>Actual</th></tr></thead><tbody>`;
            list.forEach((po) => {
                html += `<tr><td>${po.order_number}</td><td>${po.status}</td><td>${po.expected_delivery_date || "—"}</td><td>${po.actual_delivery_date || "—"}</td></tr>`;
            });
            html += `</tbody></table>`;
        } else {
            html += `<p><em>No purchase orders yet with this vendor.</em></p>`;
        }
    }

    document.getElementById("perf-content").innerHTML = html;
}

document.getElementById("perf-close").addEventListener("click", () => {
    document.getElementById("perf-overlay").style.display = "none";
});

function openModal(title, formHtml, onSubmit) {
    document.getElementById("modal-title").textContent = title;
    document.getElementById("modal-form").innerHTML = formHtml + `
        <button type="submit">Save</button>
        <p id="modal-error" class="error"></p>
    `;
    document.getElementById("modal-overlay").style.display = "flex";
    document.getElementById("modal-form").onsubmit = async (e) => {
        e.preventDefault();
        await onSubmit();
    };
}

function closeModal() {
    document.getElementById("modal-overlay").style.display = "none";
}

document.getElementById("modal-overlay").addEventListener("click", (e) => {
    if (e.target.id === "modal-overlay") closeModal();
});

function openVendorModal(vendor) {
    const isEdit = !!vendor;
    openModal(isEdit ? "Edit Vendor" : "Add Vendor", `
        <label>Name</label>
        <input type="text" id="m-name" required>
        <label>Contact Person</label>
        <input type="text" id="m-contact">
        <label>Email</label>
        <input type="email" id="m-email">
        <label>Phone</label>
        <input type="text" id="m-phone">
        <label>Country</label>
        <input type="text" id="m-country">
        <label>Payment Terms</label>
        <input type="text" id="m-terms" placeholder="e.g. Net 30">
        <label>Default Lead Time (days)</label>
        <input type="number" id="m-leadtime">
        <label>Status</label>
        <select id="m-status">
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
        </select>
    `, async () => {
        const errorEl = document.getElementById("modal-error");
        const response = await apiFetch(isEdit ? `/vendors/${vendor.id}/` : "/vendors/", {
            method: isEdit ? "PATCH" : "POST",
            body: JSON.stringify({
                name: document.getElementById("m-name").value,
                contact_person: document.getElementById("m-contact").value,
                email: document.getElementById("m-email").value,
                phone: document.getElementById("m-phone").value,
                country: document.getElementById("m-country").value,
                payment_terms: document.getElementById("m-terms").value,
                default_lead_time_days: document.getElementById("m-leadtime").value || null,
                status: document.getElementById("m-status").value,
            }),
        });
        if (!response.ok) {
            errorEl.textContent = formatApiError(await response.json());
            return;
        }
        closeModal();
        loadVendors();
    });

    document.getElementById("m-name").value = vendor ? vendor.name : "";
    document.getElementById("m-contact").value = vendor ? (vendor.contact_person ?? "") : "";
    document.getElementById("m-email").value = vendor ? (vendor.email ?? "") : "";
    document.getElementById("m-phone").value = vendor ? (vendor.phone ?? "") : "";
    document.getElementById("m-country").value = vendor ? (vendor.country ?? "") : "";
    document.getElementById("m-terms").value = vendor ? (vendor.payment_terms ?? "") : "";
    document.getElementById("m-leadtime").value = vendor ? (vendor.default_lead_time_days ?? "") : "";
    document.getElementById("m-status").value = vendor ? vendor.status : "active";
}

document.getElementById("add-vendor-btn").addEventListener("click", () => openVendorModal(null));

loadVendors();

document.getElementById("run-clustering-btn").addEventListener("click", async () => {
    const resultEl = document.getElementById("clustering-result");
    resultEl.innerHTML = "<p><em>Analyzing vendors...</em></p>";

    const response = await apiFetch("/vendors/");
    if (!response || !response.ok) return;
    const data = await response.json();
    const vendorList = data.results ?? data;

    // Gather performance data for each vendor first
    const vendorMetrics = [];
    for (const v of vendorList) {
        const perfRes = await apiFetch(`/vendors/${v.id}/performance/`);
        if (perfRes && perfRes.ok) {
            const perf = await perfRes.json();
            vendorMetrics.push({
                vendor_id: v.id,
                vendor_name: v.name,
                on_time_rate: perf.on_time_rate_percent ?? 0,
                average_lead_time_days: perf.average_lead_time_days ?? (v.default_lead_time_days ?? 14),
                total_orders: perf.total_orders ?? 0,
            });
        }
    }

    if (vendorMetrics.length < 3) {
        resultEl.innerHTML = `<p class="error">Need at least 3 vendors with order history to run clustering (have ${vendorMetrics.length}).</p>`;
        return;
    }

    try {
        const clusterRes = await fetch("http://127.0.0.1:8001/vendor-clusters", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ vendors: vendorMetrics, n_clusters: 3 }),
        });
        const clusterData = await clusterRes.json();

        if (clusterData.error) {
            resultEl.innerHTML = `<p class="error">${clusterData.error}</p>`;
            return;
        }

        const tierColors = { "Top Tier": "#27ae60", "Mid Tier": "#f39c12", "Needs Improvement": "#e74c3c", "Lowest Tier": "#c0392b" };

        let html = `<table><thead><tr><th>Vendor</th><th>Tier</th><th>On-Time Rate</th><th>Avg Lead Time</th></tr></thead><tbody>`;
        clusterData.vendors.forEach((v) => {
            const color = tierColors[v.tier] || "#8a94a1";
            html += `<tr>
                <td>${v.vendor_name}</td>
                <td><span class="severity-badge" style="background:${color}22; color:${color};">${v.tier}</span></td>
                <td>${v.on_time_rate}%</td>
                <td>${v.average_lead_time_days} days</td>
            </tr>`;
        });
        html += `</tbody></table>`;
        resultEl.innerHTML = html;
    } catch (err) {
        resultEl.innerHTML = "<p class='error'>Could not reach the AI Engine for clustering (port 8001).</p>";
    }
});
