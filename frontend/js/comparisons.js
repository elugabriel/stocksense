document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    async function loadWarehouseComparison() {
        const response = await apiFetch("/warehouses/performance/");
        if (!response || !response.ok) return;
        const data = await response.json();
    
        const tbody = document.querySelector("#warehouse-table tbody");
        tbody.innerHTML = "";
    
        data.warehouses.forEach((w) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${w.warehouse_name}</td>
                <td>${w.warehouse_type}</td>
                <td>${w.total_stock_units}</td>
                <td>${formatMoney(w.stock_value)}</td>
                <td>${w.movements_last_30_days}</td>
                <td>${w.active_alerts}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    async function loadBranchComparison() {
        const response = await apiFetch("/branches/performance/");
        if (!response || !response.ok) return;
        const data = await response.json();
    
        const tbody = document.querySelector("#branch-table tbody");
        tbody.innerHTML = "";
    
        data.branches.forEach((b) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${b.branch_name}</td>
                <td>${b.city || "—"}</td>
                <td>${b.warehouse_count}</td>
                <td>${b.total_stock_units}</td>
                <td>${formatMoney(b.stock_value)}</td>
                <td>${formatMoney(b.revenue_last_30_days)}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    async function loadProductComparison() {
        const sort = document.getElementById("product-sort").value;
        const period = document.getElementById("product-period").value;
        const params = new URLSearchParams({ sort });
        if (period) params.set("days", period);

        const response = await apiFetch(`/sales/product-comparison/?${params.toString()}`);
        if (!response || !response.ok) return;
        const data = await response.json();

        const tbody = document.querySelector("#product-table tbody");
        tbody.innerHTML = "";

        if (!data.report.length) {
            tbody.innerHTML = `<tr><td colspan="7">No sales in this period.</td></tr>`;
            return;
        }

        const maxMargin = Math.max(...data.report.map((r) => Math.abs(r.gross_margin_percent) || 0), 1);

        data.report.forEach((p) => {
            const tr = document.createElement("tr");
            const barWidth = Math.max(0, Math.min(100, (p.gross_margin_percent / maxMargin) * 100));
            tr.innerHTML = `
                <td>${p.name} <span class="muted">(${p.sku})</span></td>
                <td>${p.category || "—"}</td>
                <td>${p.units_sold}</td>
                <td>${formatMoney(p.revenue)}</td>
                <td>${formatMoney(p.cost)}</td>
                <td>${formatMoney(p.profit)}</td>
                <td>
                    <span class="bar-cell">
                        <span class="bar-fill" style="width:${barWidth}%"></span>
                        <span class="bar-label">${p.gross_margin_percent}%</span>
                    </span>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    document.getElementById("product-sort").addEventListener("change", loadProductComparison);
    document.getElementById("product-period").addEventListener("change", loadProductComparison);

    loadWarehouseComparison();
    loadBranchComparison();
    loadProductComparison();