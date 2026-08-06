document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    async function loadPurchaseOrders() {
        const response = await apiFetch("/purchase-orders/");
        if (!response || !response.ok) return;
        const data = await response.json();
        const list = data.results ?? data;
    
        const tbody = document.querySelector("#po-table tbody");
        tbody.innerHTML = "";
    
        list.forEach((po) => {
            const linesSummary = po.lines.map((l) => `${l.product_sku} x${l.quantity_ordered}`).join(", ");
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${po.order_number}</td>
                <td>${po.vendor_name}</td>
                <td>${po.status}</td>
                <td>${po.expected_delivery_date || "—"}</td>
                <td>${po.actual_delivery_date || "—"}</td>
                <td>${linesSummary || "—"}</td>
            `;
            tbody.appendChild(tr);
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
    addLineRow(); // start with one line
    
    document.getElementById("add-po-btn").addEventListener("click", () => {
        document.getElementById("modal-overlay").style.display = "flex";
    });
    
    document.getElementById("modal-overlay").addEventListener("click", (e) => {
        if (e.target.id === "modal-overlay") document.getElementById("modal-overlay").style.display = "none";
    });
    
    document.getElementById("po-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const errorEl = document.getElementById("po-error");
    
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
    
        const response = await apiFetch("/purchase-orders/", {
            method: "POST",
            body: JSON.stringify({
                vendor: parseInt(document.getElementById("po-vendor").value),
                order_number: document.getElementById("po-number").value,
                status: document.getElementById("po-status").value,
                expected_delivery_date: document.getElementById("po-expected").value || null,
                actual_delivery_date: document.getElementById("po-actual").value || null,
                lines: lines,
            }),
        });
    
        if (!response.ok) {
            errorEl.textContent = formatApiError(await response.json());
            return;
        }
    
        document.getElementById("modal-overlay").style.display = "none";
        document.getElementById("po-form").reset();
        loadPurchaseOrders();
    });
    
    loadPurchaseOrders();