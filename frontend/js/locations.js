document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    async function loadWarehouses() {
        const response = await apiFetch("/warehouses/");
        if (!response || !response.ok) return;
        const data = await response.json();
        const list = data.results ?? data;
    
        const tbody = document.querySelector("#warehouses-table tbody");
        tbody.innerHTML = "";
        list.forEach((w) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${w.id}</td><td>${w.name}</td><td>${w.warehouse_type}</td><td>${w.city ?? "—"}</td><td>${w.is_active ? "Yes" : "No"}</td>`;
            tbody.appendChild(tr);
        });
    }
    
    async function loadCategories() {
        const response = await apiFetch("/categories/");
        if (!response || !response.ok) return;
        const data = await response.json();
        const list = data.results ?? data;
    
        const tbody = document.querySelector("#categories-table tbody");
        tbody.innerHTML = "";
        list.forEach((c) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td>${c.id}</td><td>${c.name}</td><td>${c.is_active ? "Yes" : "No"}</td>`;
            tbody.appendChild(tr);
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
    
    document.getElementById("add-warehouse-btn").addEventListener("click", () => {
        openModal("Add Warehouse", `
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
        `, async () => {
            const errorEl = document.getElementById("modal-error");
            const response = await apiFetch("/warehouses/", {
                method: "POST",
                body: JSON.stringify({
                    name: document.getElementById("m-name").value,
                    warehouse_type: document.getElementById("m-type").value,
                    city: document.getElementById("m-city").value,
                    is_active: true,
                }),
            });
            if (!response.ok) {
                errorEl.textContent = formatApiError(await response.json());
                return;
            }
            closeModal();
            loadWarehouses();
        });
    });
    
    document.getElementById("add-category-btn").addEventListener("click", () => {
        openModal("Add Category", `
            <label>Name</label>
            <input type="text" id="m-name" required>
        `, async () => {
            const errorEl = document.getElementById("modal-error");
            const response = await apiFetch("/categories/", {
                method: "POST",
                body: JSON.stringify({
                    name: document.getElementById("m-name").value,
                    is_active: true,
                }),
            });
            if (!response.ok) {
                errorEl.textContent = formatApiError(await response.json());
                return;
            }
            closeModal();
            loadCategories();
        });
    });
    
    loadWarehouses();
    loadCategories();