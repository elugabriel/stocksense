document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    async function loadRoleAwareDashboard() {
        const response = await apiFetch("/dashboard/role-aware/");
        if (!response || !response.ok) return;
        const data = await response.json();
    
        const container = document.querySelector("main.dashboard");
        let html = `<h1>Welcome, ${data.role_display}</h1>`;
    
        if (data.view_type === "executive") {
            html += `
                <section>
                    <h3>Executive Overview</h3>
                    <p><strong>Revenue (30 days):</strong> ${data.revenue_last_30_days}</p>
                    <p><strong>Active Alerts:</strong> ${data.active_alerts} (${data.critical_alerts} critical)</p>
                    <p><strong>Active Vendors:</strong> ${data.active_vendors}</p>
                </section>`;
        } else if (data.view_type === "financial") {
            html += `
                <section>
                    <h3>Financial Overview</h3>
                    <p><strong>Revenue (30 days):</strong> ${data.revenue_last_30_days}</p>
                </section>`;
        } else if (data.view_type === "warehouse_operations") {
            html += `
                <section>
                    <h3>Warehouse Operations</h3>
                    <p><strong>Low Stock Alerts:</strong> ${data.low_stock_alerts}</p>
                    <p><strong>Expiry Alerts:</strong> ${data.expiry_alerts}</p>
                </section>`;
        } else if (data.view_type === "sales_floor") {
            html += `
                <section>
                    <h3>Today's Sales</h3>
                    <p><strong>Transactions:</strong> ${data.sales_today_count}</p>
                    <p><strong>Revenue Today:</strong> ${data.sales_today_revenue}</p>
                </section>`;
        } else if (data.view_type === "procurement") {
            html += `
                <section>
                    <h3>Procurement Overview</h3>
                    <p><strong>Pending Reorder Alerts:</strong> ${data.pending_reorder_alerts}</p>
                    <p><strong>Active Vendors:</strong> ${data.active_vendors}</p>
                </section>`;
        } else {
            html += `<section><p>No specialized view configured for this role yet.</p></section>`;
        }
    
        html += `
            <section>
                <h3>By Product</h3>
                <table id="by-product-table">
                    <thead><tr><th>SKU</th><th>Product</th><th>Total Quantity</th></tr></thead>
                    <tbody></tbody>
                </table>
            </section>
            <section>
                <h3>By Warehouse</h3>
                <table id="by-warehouse-table">
                    <thead><tr><th>Warehouse</th><th>Branch</th><th>Total Quantity</th></tr></thead>
                    <tbody></tbody>
                </table>
            </section>`;
    
        container.innerHTML = html;
        loadStockTables();
    }
    
    async function loadStockTables() {
        const response = await apiFetch("/dashboard/stock/");
        if (!response || !response.ok) return;
        const data = await response.json();
    
        const productBody = document.querySelector("#by-product-table tbody");
        data.by_product.forEach((row) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${row.product__sku}</td><td>${row.product__name}</td><td>${row.total_quantity}</td>`;
            productBody.appendChild(tr);
        });
    
        const warehouseBody = document.querySelector("#by-warehouse-table tbody");
        data.by_warehouse.forEach((row) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${row.warehouse__name}</td><td>${row.warehouse__branch__name ?? "—"}</td><td>${row.total_quantity}</td>`;
            warehouseBody.appendChild(tr);
        });
    }
    
    loadRoleAwareDashboard();