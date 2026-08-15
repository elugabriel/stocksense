document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });

    let purchaseOrders = [];
    let editingId = null;

    async function loadPurchaseOrders() {
        const response = await apiFetch("/purchase-orders/");
        if (!response || !response.ok) return;
        const data = await response.json();
        purchaseOrders = data.results ?? data;

        const tbody = document.querySelector("#po-table tbody");
        tbody.innerHTML = "";

        purchaseOrders.forEach((po) => {
            const linesSummary = po.lines.map((l) => `${l.product_sku} x${l.quantity_ordered}`).join(", ");
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${po.order_number}</td>
                <td>${po.vendor_name}</td>
                <td>${po.status}</td>
                <td>${po.expected_delivery_date || "—"}</td>
                <td>${po.actual_delivery_date || "—"}</td>
                <td>${linesSummary || "—"}</td>
                <td>
                    <button class="edit-btn" data-id="${po.id}">Edit</button>
                    <button class="delete-btn" data-id="${po.id}">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        document.querySelectorAll("#po-table .edit-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                const po = purchaseOrders.find((p) => p.id == btn.dataset.id);
                openEditModal(po);
            });
        });
        document.querySelectorAll("#po-table .delete-btn").forEach((btn) => {
            btn.addEventListener("click", async () => {
                if (!confirm("Delete this purchase order? This cannot be undone.")) return;
                const response = await apiFetch(`/purchase-orders/${btn.dataset.id}/`, { method: "DELETE" });
                if (response && response.ok) {
                    loadPurchaseOrders();
                } else {
                    alert("Failed to delete purchase order.");
                }
            });
        });
    }

    let lineCount = 0;

    function addLineRow() {
        lineCount++;
        const div = document.createElement("div");
        div.className = "po-line-row";
        div.innerHTML = `
            <input type="number" placeholder="Product ID" class="line-product" style="width:30%">
            <input type="number" placeholder="Qty" class="line-qty" style="width:20%">
            <input type="number" step="0.01" placeholder="Unit Cost" class="line-cost" style="width:25%">
            <button type="button" class="remove-line-btn">Remove</button>
        `;
        div.querySelector(".remove-line-btn").addEventListener("click", () => div.remove());
        document.getElementById("po-lines").appendChild(div);
    }

    document.getElementById("add-line-btn").addEventListener("click", addLineRow);

    function resetForm() {
        document.getElementById("po-form").reset();
        document.getElementById("po-lines").innerHTML = "";
        lineCount = 0;
        addLineRow();
    }

    function openAddModal() {
        editingId = null;
        document.getElementById("po-modal-title").textContent = "New Purchase Order";
        document.getElementById("po-error").textContent = "";
        resetForm();
        document.getElementById("po-lines-section").style.display = "block";
        document.getElementById("po-lines-readonly").style.display = "none";
        document.getElementById("modal-overlay").style.display = "flex";
    }

    function openEditModal(po) {
        editingId = po.id;
        document.getElementById("po-modal-title").textContent = `Edit Purchase Order — ${po.order_number}`;
        document.getElementById("po-error").textContent = "";

        document.getElementById("po-vendor").value = po.vendor;
        document.getElementById("po-number").value = po.order_number;
        document.getElementById("po-status").value = po.status;
        document.getElementById("po-expected").value = po.expected_delivery_date || "";
        document.getElementById("po-actual").value = po.actual_delivery_date || "";

        // Line items aren't editable via this form (backend doesn't support
        // updating nested lines) — show them read-only instead.
        document.getElementById("po-lines-section").style.display = "none";
        document.getElementById("po-lines-readonly").style.display = "block";
        const linesHtml = po.lines.length
            ? `<table><thead><tr><th>SKU</th><th>Qty Ordered</th><th>Qty Received</th><th>Unit Cost</th></tr></thead><tbody>${po.lines.map((l) =>
                  `<tr><td>${l.product_sku}</td><td>${l.quantity_ordered}</td><td>${l.quantity_received}</td><td>${l.unit_cost}</td></tr>`
              ).join("")}</tbody></table>`
            : "<p><em>No line items.</em></p>";
        document.getElementById("po-lines-readonly-content").innerHTML = linesHtml;

        document.getElementById("modal-overlay").style.display = "flex";
    }

    document.getElementById("add-po-btn").addEventListener("click", openAddModal);

    document.getElementById("modal-overlay").addEventListener("click", (e) => {
        if (e.target.id === "modal-overlay") document.getElementById("modal-overlay").style.display = "none";
    });

    document.getElementById("po-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const errorEl = document.getElementById("po-error");
        const isEdit = !!editingId;

        const payload = {
            vendor: parseInt(document.getElementById("po-vendor").value),
            order_number: document.getElementById("po-number").value,
            status: document.getElementById("po-status").value,
            expected_delivery_date: document.getElementById("po-expected").value || null,
            actual_delivery_date: document.getElementById("po-actual").value || null,
        };

        if (!isEdit) {
            const lines = [];
            document.querySelectorAll(".po-line-row").forEach((row) => {
                const product = row.querySelector(".line-product").value;
                const qty = row.querySelector(".line-qty").value;
                const cost = row.querySelector(".line-cost").value;
                if (product && qty && cost) {
                    lines.push({ product: parseInt(product), quantity_ordered: parseInt(qty), unit_cost: cost });
                }
            });

            if (lines.length === 0) {
                errorEl.textContent = "Add at least one line item.";
                return;
            }
            payload.lines = lines;
        }

        const response = await apiFetch(isEdit ? `/purchase-orders/${editingId}/` : "/purchase-orders/", {
            method: isEdit ? "PATCH" : "POST",
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            errorEl.textContent = formatApiError(await response.json());
            return;
        }

        document.getElementById("modal-overlay").style.display = "none";
        loadPurchaseOrders();
    });

    addLineRow(); // start with one line
    loadPurchaseOrders();
