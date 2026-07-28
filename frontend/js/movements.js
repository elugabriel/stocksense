document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    const TYPE_LABELS = {
        received: "Received",
        sale: "Sale",
        transfer_out: "Transfer Out",
        transfer_in: "Transfer In",
        adjustment: "Adjustment",
        return: "Return",
        damage: "Damage",
    };
    
    async function loadMovements() {
        const response = await apiFetch("/movements/");
        if (!response || !response.ok) return;
        const data = await response.json();
        const list = data.results ?? data;
    
        const tbody = document.querySelector("#movements-table tbody");
        tbody.innerHTML = "";
    
        list.forEach((m) => {
            const tr = document.createElement("tr");
            const date = new Date(m.timestamp).toLocaleString();
            const qtyClass = m.quantity < 0 ? "qty-negative" : "qty-positive";
    
            tr.innerHTML = `
                <td>${date}</td>
                <td>${m.product_sku}</td>
                <td>${m.warehouse_name}</td>
                <td>${TYPE_LABELS[m.movement_type] || m.movement_type}</td>
                <td class="${qtyClass}">${m.quantity > 0 ? "+" : ""}${m.quantity}</td>
                <td>${m.performed_by_username || "—"}</td>
                <td>${m.notes || "—"}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    loadMovements();