document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "index.html";
});

const params = new URLSearchParams(window.location.search);
const productId = params.get("id");
const isEditMode = !!productId;

if (isEditMode) {
    document.querySelector("h1").textContent = "Edit Product";
    document.querySelector("button[type='submit']").textContent = "Update Product";
    loadExistingProduct();
}

async function loadExistingProduct() {
    const response = await apiFetch(`/products/${productId}/`);
    if (!response || !response.ok) {
        alert("Failed to load product");
        return;
    }
    const product = await response.json();

    document.getElementById("sku").value = product.sku;
    document.getElementById("name").value = product.name;
    document.getElementById("description").value = product.description || "";
    document.getElementById("category").value = product.category || "";
    document.getElementById("unit_of_measure").value = product.unit_of_measure;
    document.getElementById("cost_price").value = product.cost_price;
    document.getElementById("selling_price").value = product.selling_price;
    document.getElementById("reorder_level").value = product.reorder_level;
    document.getElementById("barcode").value = product.barcode || "";
}

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

    const endpoint = isEditMode ? `/products/${productId}/` : "/products/";
    const method = isEditMode ? "PATCH" : "POST";

    const response = await apiFetch(endpoint, {
        method: method,
        body: JSON.stringify(payload),
    });

    if (!response) return;

    if (!response.ok) {
        const errorData = await response.json();
        errorEl.textContent = formatApiError(errorData);
        return;
    }

    successEl.textContent = isEditMode ? "Product updated successfully!" : "Product saved successfully!";
    if (!isEditMode) document.getElementById("product-form").reset();

    setTimeout(() => {
        window.location.href = "products.html";
    }, 1000);
});