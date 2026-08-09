document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    // --- Discontinuation candidates ---
    async function loadDiscontinuationCandidates() {
        const response = await apiFetch("/alerts/?resolved=false");
        if (!response || !response.ok) return;
        const data = await response.json();
        const list = data.results ?? data;
    
        const candidates = list.filter((a) => a.message && a.message.includes("discontinuation candidate"));
        const container = document.getElementById("discontinuation-list");
    
        if (candidates.length === 0) {
            container.innerHTML = "<p><em>No discontinuation candidates flagged right now.</em></p>";
            return;
        }
    
        container.innerHTML = candidates.map((c) => `
            <div class="kpi-card" style="border-left-color:#8a94a1; margin-bottom:10px;">
                <p style="margin:0;">${c.message}</p>
            </div>
        `).join("");
    }
    
    document.getElementById("run-checks-btn").addEventListener("click", async () => {
        const response = await apiFetch("/alerts/run-checks/", { method: "POST" });
        if (response && response.ok) {
            const data = await response.json();
            alert(`Checks complete. ${data.total} new alert(s) created.`);
            loadDiscontinuationCandidates();
        }
    });
    
    // --- Best vendor for reorder ---
    document.getElementById("find-best-vendor-btn").addEventListener("click", async () => {
        const productId = document.getElementById("bv-product-id").value;
        const resultEl = document.getElementById("best-vendor-result");
        if (!productId) return;
    
        resultEl.innerHTML = "<p><em>Searching...</em></p>";
        const response = await apiFetch(`/products/${productId}/best-vendor/`);
        if (!response || !response.ok) {
            resultEl.innerHTML = "<p class='error'>Could not fetch recommendation.</p>";
            return;
        }
        const data = await response.json();
    
        if (data.error) {
            resultEl.innerHTML = `<p class="error">${data.error}</p>`;
            return;
        }
    
        const best = data.recommended_vendor;
        let html = `
            <div class="kpi-card" style="border-left-color:#27ae60; margin-top:15px;">
                <p><strong>Recommended:</strong> ${best.vendor_name}</p>
                <p><strong>Performance Score:</strong> ${best.performance_score ?? "Not yet scored"}</p>
                <p><strong>Average Unit Cost:</strong> ${best.average_unit_cost}</p>
                <p><strong>Previously Ordered:</strong> ${best.total_units_previously_ordered} units</p>
                <p><strong>Quoted Lead Time:</strong> ${best.quoted_lead_time_days ?? "N/A"} days</p>
            </div>
        `;
    
        if (data.all_vendors_considered.length > 1) {
            html += `<h4 style="margin-top:15px;">All Vendors Considered</h4><table><thead><tr><th>Vendor</th><th>Score</th><th>Avg Cost</th></tr></thead><tbody>`;
            data.all_vendors_considered.forEach((v) => {
                html += `<tr><td>${v.vendor_name}</td><td>${v.performance_score ?? "—"}</td><td>${v.average_unit_cost}</td></tr>`;
            });
            html += `</tbody></table>`;
        }
    
        if (data.note) html += `<p style="color:#8a94a1; font-size:13px; margin-top:8px;">${data.note}</p>`;
    
        resultEl.innerHTML = html;
    });
    
    // --- Order quantity optimizer ---
    function addOptProductRow() {
        const div = document.createElement("div");
        div.className = "po-line-row";
        div.innerHTML = `
            <input type="text" placeholder="SKU" class="opt-sku" style="width:20%">
            <input type="number" placeholder="Predicted Demand" class="opt-demand" style="width:25%">
            <input type="number" step="0.01" placeholder="Unit Cost" class="opt-cost" style="width:20%">
            <input type="number" step="0.01" placeholder="Storage/Unit" class="opt-storage-unit" value="1" style="width:20%">
            <button type="button" class="remove-line-btn">Remove</button>
        `;
        div.querySelector(".remove-line-btn").addEventListener("click", () => div.remove());
        document.getElementById("opt-products").appendChild(div);
    }
    
    document.getElementById("add-opt-product-btn").addEventListener("click", addOptProductRow);
    addOptProductRow();
    
    document.getElementById("run-optimization-btn").addEventListener("click", async () => {
        const resultEl = document.getElementById("optimization-result");
        const products = [];
    
        document.querySelectorAll("#opt-products .po-line-row").forEach((row) => {
            const sku = row.querySelector(".opt-sku").value;
            const demand = row.querySelector(".opt-demand").value;
            const cost = row.querySelector(".opt-cost").value;
            const storageUnit = row.querySelector(".opt-storage-unit").value;
            if (sku && demand && cost) {
                products.push({
                    product_sku: sku,
                    predicted_demand: parseFloat(demand),
                    unit_cost: parseFloat(cost),
                    storage_units_per_item: parseFloat(storageUnit) || 1,
                });
            }
        });
    
        const budget = parseFloat(document.getElementById("opt-budget").value);
        const storage = parseFloat(document.getElementById("opt-storage").value);
    
        if (products.length === 0 || !budget || !storage) {
            resultEl.innerHTML = "<p class='error'>Add at least one product and set budget/storage.</p>";
            return;
        }
    
        resultEl.innerHTML = "<p><em>Optimizing...</em></p>";
    
        try {
            const response = await fetch("http://127.0.0.1:8001/optimize-order-quantities", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ products, budget, storage_capacity: storage }),
            });
            const data = await response.json();
    
            if (data.error) {
                resultEl.innerHTML = `<p class="error">${data.error}</p>`;
                return;
            }
    
            let html = `
                <p><strong>Budget used:</strong> ${data.total_cost} (${data.budget_utilization_percent}%)</p>
                <p><strong>Storage used:</strong> ${data.total_storage_used} (${data.storage_utilization_percent}%)</p>
                <table><thead><tr><th>SKU</th><th>Order Qty</th><th>Demand Coverage</th><th>Cost</th></tr></thead><tbody>
            `;
            data.allocations.forEach((a) => {
                html += `<tr><td>${a.product_sku}</td><td>${a.recommended_order_quantity}</td><td>${a.demand_coverage_percent}%</td><td>${a.cost}</td></tr>`;
            });
            html += `</tbody></table>`;
            resultEl.innerHTML = html;
        } catch (err) {
            resultEl.innerHTML = "<p class='error'>Could not reach the AI Engine (port 8001).</p>";
        }
    });
    
    // --- Weekly summary ---
    document.getElementById("generate-summary-btn").addEventListener("click", async () => {
        const outputEl = document.getElementById("summary-output");
        outputEl.textContent = "Generating...";
    
        const response = await apiFetch("/products/1/forecasted-revenue/"); // trigger auth check only
        // Summary isn't a Django endpoint yet — call via a lightweight wrapper
        const summaryResponse = await apiFetch("/performance-summary/");
        if (summaryResponse && summaryResponse.ok) {
            const data = await summaryResponse.json();
            outputEl.textContent = data.summary_text;
        } else {
            outputEl.textContent = "Could not generate summary. This endpoint may not be exposed via Django yet.";
        }
    });
    
    loadDiscontinuationCandidates();