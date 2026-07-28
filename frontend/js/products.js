document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    async function loadProducts() {
        const response = await apiFetch("/products/");
        if (!response || !response.ok) {
            alert("Failed to load products");
            return;
        }
    
        const products = await response.json();
        const tbody = document.querySelector("#products-table tbody");
        tbody.innerHTML = "";
    
        const list = products.results ?? products;
    
        list.forEach((product) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${product.sku}</td>
                <td>${product.name}</td>
                <td>${product.category ?? "—"}</td>
                <td>${product.cost_price}</td>
                <td>${product.selling_price}</td>
                <td>${product.reorder_level}</td>
                <td>${product.is_active ? "Yes" : "No"}</td>
                <td>
                    <button class="edit-btn" data-id="${product.id}">Edit</button>
                    <button class="delete-btn" data-id="${product.id}">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        document.querySelectorAll(".edit-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                window.location.href = `product-form.html?id=${btn.dataset.id}`;
            });
        });
        
        document.querySelectorAll(".delete-btn").forEach((btn) => {
            btn.addEventListener("click", async () => {
                if (!confirm("Delete this product? This cannot be undone.")) return;
                const response = await apiFetch(`/products/${btn.dataset.id}/`, { method: "DELETE" });
                if (response && response.ok) {
                    loadProducts();
                } else {
                    alert("Failed to delete product");
                }
            });
        });
    }
    
    document.getElementById("add-product-btn").addEventListener("click", () => {
        window.location.href = "product-form.html";
    });
    
    loadProducts();