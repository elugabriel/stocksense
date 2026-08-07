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
                <td>${w.stock_value}</td>
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
                <td>${b.stock_value}</td>
                <td>${b.revenue_last_30_days}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    loadWarehouseComparison();
    loadBranchComparison();