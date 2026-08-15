document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });

    let warehouses = [];
    let categories = [];

    async function loadWarehouses() {
        const response = await apiFetch("/warehouses/");
        if (!response || !response.ok) return;
        const data = await response.json();
        warehouses = data.results ?? data;

        const tbody = document.querySelector("#warehouses-table tbody");
        tbody.innerHTML = "";
        warehouses.forEach((w) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${w.id}</td><td>${w.name}</td><td>${w.warehouse_type}</td><td>${w.city ?? "—"}</td><td>${w.is_active ? "Yes" : "No"}</td>
                <td>
                    <button class="edit-btn" data-id="${w.id}">Edit</button>
                    <button class="delete-btn" data-id="${w.id}">Delete</button>
                </td>`;
            tbody.appendChild(tr);
        });

        document.querySelectorAll("#warehouses-table .edit-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                const warehouse = warehouses.find((w) => w.id == btn.dataset.id);
                openWarehouseModal(warehouse);
            });
        });
        document.querySelectorAll("#warehouses-table .delete-btn").forEach((btn) => {
            btn.addEventListener("click", async () => {
                if (!confirm("Delete this warehouse? This cannot be undone.")) return;
                const response = await apiFetch(`/warehouses/${btn.dataset.id}/`, { method: "DELETE" });
                if (response && response.ok) {
                    loadWarehouses();
                } else {
                    alert("Failed to delete warehouse. It may still have stock or references tied to it.");
                }
            });
        });
    }

    async function loadCategories() {
        const response = await apiFetch("/categories/");
        if (!response || !response.ok) return;
        const data = await response.json();
        categories = data.results ?? data;

        const tbody = document.querySelector("#categories-table tbody");
        tbody.innerHTML = "";
        categories.forEach((c) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${c.id}</td><td>${c.name}</td><td>${c.is_active ? "Yes" : "No"}</td>
                <td>
                    <button class="edit-btn" data-id="${c.id}">Edit</button>
                    <button class="delete-btn" data-id="${c.id}">Delete</button>
                </td>`;
            tbody.appendChild(tr);
        });

        document.querySelectorAll("#categories-table .edit-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                const category = categories.find((c) => c.id == btn.dataset.id);
                openCategoryModal(category);
            });
        });
        document.querySelectorAll("#categories-table .delete-btn").forEach((btn) => {
            btn.addEventListener("click", async () => {
                if (!confirm("Delete this category? This cannot be undone.")) return;
                const response = await apiFetch(`/categories/${btn.dataset.id}/`, { method: "DELETE" });
                if (response && response.ok) {
                    loadCategories();
                } else {
                    alert("Failed to delete category. It may still be assigned to products.");
                }
            });
        });
    }

    function openModal(title, fieldsHtml, onSubmit) {
        document.getElementById("modal-title").textContent = title;
        document.getElementById("modal-form").innerHTML = fieldsHtml + `
            <button type="submit">Save</button>
            <p id="modal-error" class="error"></p>
        `;
        document.getElementById("modal-overlay").style.display = "flex";

        const form = document.getElementById("modal-form");
        form.onsubmit = async (e) => {
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

    function openWarehouseModal(warehouse) {
        const isEdit = !!warehouse;
        openModal(isEdit ? "Edit Warehouse" : "Add Warehouse", `
            <label>Name</label>
            <input type="text" id="m-name" required>
            <label>Type</label>
            <select id="m-type">
                <option value="main">Main Warehouse</option>
                <option value="branch">Branch Storage</option>
                <option value="transit">Transit/Staging</option>
                <option value="cold_storage">Cold Storage</option>
            </select>
            <label>City</label>
            <input type="text" id="m-city">
            <label><input type="checkbox" id="m-active"> Active</label>
        `, async () => {
            const errorEl = document.getElementById("modal-error");
            const response = await apiFetch(isEdit ? `/warehouses/${warehouse.id}/` : "/warehouses/", {
                method: isEdit ? "PATCH" : "POST",
                body: JSON.stringify({
                    name: document.getElementById("m-name").value,
                    warehouse_type: document.getElementById("m-type").value,
                    city: document.getElementById("m-city").value,
                    is_active: document.getElementById("m-active").checked,
                }),
            });
            if (!response.ok) {
                errorEl.textContent = formatApiError(await response.json());
                return;
            }
            closeModal();
            loadWarehouses();
        });

        document.getElementById("m-name").value = warehouse ? warehouse.name : "";
        document.getElementById("m-type").value = warehouse ? warehouse.warehouse_type : "main";
        document.getElementById("m-city").value = warehouse ? (warehouse.city ?? "") : "";
        document.getElementById("m-active").checked = warehouse ? warehouse.is_active : true;
    }

    function openCategoryModal(category) {
        const isEdit = !!category;
        openModal(isEdit ? "Edit Category" : "Add Category", `
            <label>Name</label>
            <input type="text" id="m-name" required>
            <label><input type="checkbox" id="m-active"> Active</label>
        `, async () => {
            const errorEl = document.getElementById("modal-error");
            const response = await apiFetch(isEdit ? `/categories/${category.id}/` : "/categories/", {
                method: isEdit ? "PATCH" : "POST",
                body: JSON.stringify({
                    name: document.getElementById("m-name").value,
                    is_active: document.getElementById("m-active").checked,
                }),
            });
            if (!response.ok) {
                errorEl.textContent = formatApiError(await response.json());
                return;
            }
            closeModal();
            loadCategories();
        });

        document.getElementById("m-name").value = category ? category.name : "";
        document.getElementById("m-active").checked = category ? category.is_active : true;
    }

    document.getElementById("add-warehouse-btn").addEventListener("click", () => openWarehouseModal(null));
    document.getElementById("add-category-btn").addEventListener("click", () => openCategoryModal(null));

    loadWarehouses();
    loadCategories();
