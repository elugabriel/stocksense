document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    async function loadDashboard() {
        const response = await apiFetch("/dashboard/stock/");
        if (!response || !response.ok) {
            alert("Failed to load dashboard data");
            return;
        }
    
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
    
    loadDashboard();