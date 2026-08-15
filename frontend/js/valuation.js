document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    async function loadValuation() {
        const method = document.getElementById("valuation-method").value;
        const response = await apiFetch(`/inventory/valuation/?method=${method}`);
        if (!response || !response.ok) return;
        const data = await response.json();
    
        document.getElementById("total-value-amount").textContent = data.total_inventory_value;
    
        const tbody = document.querySelector("#valuation-table tbody");
        tbody.innerHTML = "";
    
        if (data.products.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5">No stock to value yet.</td></tr>`;
            return;
        }
    
        data.products.forEach((p) => {
            const batchDetails = p.batch_breakdown.map(
                (b) => `Lot ${b.lot_number}: ${b.quantity} @ ${b.unit_cost}`
            ).join(" | ");
    
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${p.product_sku}</td>
                <td>${p.product_name}</td>
                <td>${p.total_quantity}</td>
                <td>${p.total_value}</td>
                <td style="font-size:12px; color:#777;">${batchDetails}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    document.getElementById("load-valuation-btn").addEventListener("click", loadValuation);
    document.getElementById("valuation-method").addEventListener("change", loadValuation);
    
    loadValuation();