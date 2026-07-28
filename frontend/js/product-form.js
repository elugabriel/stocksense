document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    document.getElementById("product-form").addEventListener("submit", async (e) => {
        e.preventDefault();
    
        const errorEl = document.getElementById("error-message");
        const successEl = document.getElementById("success-message");
        errorEl.textContent = "";
        successEl.textContent = "";
    
        const categoryValue = document.getElementById("category").value;
    
        const payload = {
            sku: document.getElementById("sku").value,
            name: document.getElementById("name").value,
            description: document.getElementById("description").value,
            category: categoryValue ? parseInt(categoryValue) : null,
            unit_of_measure: document.getElementById("unit_of_measure").value,
            cost_price: document.getElementById("cost_price").value,
            selling_price: document.getElementById("selling_price").value,
            reorder_level: parseInt(document.getElementById("reorder_level").value) || 0,
            barcode: document.getElementById("barcode").value || null,
            is_active: true,
        };
    
        const response = await apiFetch("/products/", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    
        if (!response) return;
    
        if (!response.ok) {
            const errorData = await response.json();
            errorEl.textContent = JSON.stringify(errorData);
            return;
        }
    
        successEl.textContent = "Product saved successfully!";
        document.getElementById("product-form").reset();
    
        setTimeout(() => {
            window.location.href = "products.html";
        }, 1000);
    });