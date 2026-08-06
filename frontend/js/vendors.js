document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    async function loadVendors() {
        const response = await apiFetch("/vendors/");
        if (!response || !response.ok) return;
        const data = await response.json();
        const list = data.results ?? data;
    
        const tbody = document.querySelector("#vendors-table tbody");
        tbody.innerHTML = "";
    
        list.forEach((v) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${v.name}</td>
                <td>${v.country || "—"}</td>
                <td>${v.default_lead_time_days ?? "—"}</td>
                <td>${v.status}</td>
                <td>${v.performance_score ?? "Not yet scored"}</td>
                <td><button class="perf-btn" data-id="${v.id}" data-name="${v.name}">View Performance</button></td>
            `;
            tbody.appendChild(tr);
        });
    
        document.querySelectorAll(".perf-btn").forEach((btn) => {
            btn.addEventListener("click", () => showPerformance(btn.dataset.id, btn.dataset.name));
        });
    }
    
    async function showPerformance(vendorId, vendorName) {
        document.getElementById("perf-title").textContent = `Performance — ${vendorName}`;
        document.getElementById("perf-content").innerHTML = "Loading...";
        document.getElementById("perf-overlay").style.display = "flex";
    
        const [perfRes, costRes] = await Promise.all([
            apiFetch(`/vendors/${vendorId}/performance/`),
            apiFetch(`/vendors/${vendorId}/cost_trends/`),
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
    
    document.getElementById("add-vendor-btn").addEventListener("click", () => {
        openModal("Add Vendor", `
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
        `, async () => {
            const errorEl = document.getElementById("modal-error");
            const response = await apiFetch("/vendors/", {
                method: "POST",
                body: JSON.stringify({
                    name: document.getElementById("m-name").value,
                    contact_person: document.getElementById("m-contact").value,
                    email: document.getElementById("m-email").value,
                    phone: document.getElementById("m-phone").value,
                    country: document.getElementById("m-country").value,
                    payment_terms: document.getElementById("m-terms").value,
                    default_lead_time_days: document.getElementById("m-leadtime").value || null,
                    status: "active",
                }),
            });
            if (!response.ok) {
                errorEl.textContent = formatApiError(await response.json());
                return;
            }
            closeModal();
            loadVendors();
        });
    });
    
    loadVendors();