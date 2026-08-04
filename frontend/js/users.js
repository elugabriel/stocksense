document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    const ROLE_CHOICES = [
        ["super_admin", "Super Administrator"],
        ["org_admin", "Organization Administrator"],
        ["branch_manager", "Branch Manager"],
        ["warehouse_manager", "Warehouse Manager"],
        ["inventory_officer", "Inventory Officer"],
        ["procurement_officer", "Procurement Officer"],
        ["sales_staff", "Sales Staff (Cashier)"],
        ["accountant", "Accountant"],
        ["vendor", "Vendor (Portal)"],
        ["executive", "Executive (Read-only Dashboard)"],
    ];
    
    async function loadUsers() {
        const response = await apiFetch("/users/");
        if (!response) return;
    
        if (!response.ok) {
            const tbody = document.querySelector("#users-table tbody");
            tbody.innerHTML = `<tr><td colspan="6">You don't have permission to view users. This page is limited to Super Administrators and Organization Administrators.</td></tr>`;
            return;
        }
    
        const data = await response.json();
        const list = data.results ?? data;
    
        const tbody = document.querySelector("#users-table tbody");
        tbody.innerHTML = "";
    
        list.forEach((u) => {
            const roleLabel = ROLE_CHOICES.find((r) => r[0] === u.role)?.[1] || u.role;
            const joined = new Date(u.date_joined).toLocaleDateString();
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${u.username}</td>
                <td>${u.email || "—"}</td>
                <td>${roleLabel}</td>
                <td>${u.is_active ? "Yes" : "No"}</td>
                <td>${joined}</td>
                <td><button class="edit-btn" data-id="${u.id}">Edit</button></td>
            `;
            tbody.appendChild(tr);
        });
    
        document.querySelectorAll(".edit-btn").forEach((btn) => {
            btn.addEventListener("click", () => openEditModal(btn.dataset.id));
        });
    }
    
    function roleOptionsHtml(selected = "") {
        return ROLE_CHOICES.map(
            ([value, label]) => `<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`
        ).join("");
    }
    
    function openModal(title, formHtml, onSubmit) {
        document.getElementById("modal-title").textContent = title;
        document.getElementById("modal-form").innerHTML = formHtml + `
            <button type="submit">Save</button>
            <p id="modal-error" class="error"></p>
        `;
        document.getElementById("modal-overlay").style.display = "flex";
    
        document.getElementById("modal-form").onsubmit = async (e) => {
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
    
    document.getElementById("add-user-btn").addEventListener("click", () => {
        openModal("Add User", `
            <label>Username</label>
            <input type="text" id="m-username" required>
            <label>Email</label>
            <input type="email" id="m-email">
            <label>Password</label>
            <input type="password" id="m-password" required minlength="8">
            <label>Role</label>
            <select id="m-role">${roleOptionsHtml()}</select>
        `, async () => {
            const errorEl = document.getElementById("modal-error");
            const response = await apiFetch("/users/", {
                method: "POST",
                body: JSON.stringify({
                    username: document.getElementById("m-username").value,
                    email: document.getElementById("m-email").value,
                    password: document.getElementById("m-password").value,
                    role: document.getElementById("m-role").value,
                }),
            });
            if (!response.ok) {
                errorEl.textContent = formatApiError(await response.json());
                return;
            }
            closeModal();
            loadUsers();
        });
    });
    
    async function openEditModal(userId) {
        const response = await apiFetch(`/users/${userId}/`);
        if (!response || !response.ok) return;
        const user = await response.json();
    
        openModal("Edit User", `
            <label>Username</label>
            <input type="text" id="m-username" value="${user.username}" disabled>
            <label>Email</label>
            <input type="email" id="m-email" value="${user.email || ""}">
            <label>Role</label>
            <select id="m-role">${roleOptionsHtml(user.role)}</select>
            <label>Active</label>
            <select id="m-active">
                <option value="true" ${user.is_active ? "selected" : ""}>Yes</option>
                <option value="false" ${!user.is_active ? "selected" : ""}>No</option>
            </select>
        `, async () => {
            const errorEl = document.getElementById("modal-error");
            const response = await apiFetch(`/users/${userId}/`, {
                method: "PATCH",
                body: JSON.stringify({
                    email: document.getElementById("m-email").value,
                    role: document.getElementById("m-role").value,
                    is_active: document.getElementById("m-active").value === "true",
                }),
            });
            if (!response.ok) {
                errorEl.textContent = formatApiError(await response.json());
                return;
            }
            closeModal();
            loadUsers();
        });
    }
    
    loadUsers();