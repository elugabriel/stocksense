document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    const FIELDS_BY_ACTION = {
        add: ["product_id", "warehouse_id", "lot_number", "quantity", "manufacture_date", "expiry_date"],
        receive: ["product_id", "warehouse_id", "lot_number", "quantity", "vendor_reference", "manufacture_date", "expiry_date"],
        return: ["product_id", "warehouse_id", "batch_id", "quantity", "direction", "is_resellable", "reason"],
        transfer: ["product_id", "batch_id", "source_warehouse_id", "destination_warehouse_id", "quantity", "notes"],
        damage: ["product_id", "warehouse_id", "batch_id", "quantity", "reason_code", "reason_notes"],
        count: ["product_id", "warehouse_id", "batch_id", "counted_quantity", "notes"],
    };
    
    const ENDPOINT_BY_ACTION = {
        add: "/stock/add/",
        receive: "/stock/receive/",
        return: "/stock/return/",
        transfer: "/stock/transfer/",
        damage: "/stock/remove-damaged/",
        count: "/stock/physical-count/",
    };
    
    function updateVisibleFields() {
        const action = document.getElementById("action-type").value;
        const visibleFields = FIELDS_BY_ACTION[action];
    
        document.querySelectorAll(".field-group").forEach((group) => {
            const field = group.dataset.field;
            group.style.display = visibleFields.includes(field) ? "block" : "none";
        });
    }
    
    document.getElementById("action-type").addEventListener("change", updateVisibleFields);
    updateVisibleFields();
    
    document.getElementById("stock-form").addEventListener("submit", async (e) => {
        e.preventDefault();
    
        const errorEl = document.getElementById("error-message");
        const successEl = document.getElementById("success-message");
        errorEl.textContent = "";
        successEl.textContent = "";
    
        const action = document.getElementById("action-type").value;
        const fields = FIELDS_BY_ACTION[action];
        const payload = {};
    
        fields.forEach((field) => {
            const el = document.getElementById(field);
            if (!el || el.value === "") return;
    
            if (field === "is_resellable") {
                payload[field] = el.value === "true";
            } else if (["product_id", "warehouse_id", "source_warehouse_id", "destination_warehouse_id", "batch_id", "quantity", "counted_quantity"].includes(field)) {
                payload[field] = parseInt(el.value);
            } else {
                payload[field] = el.value;
            }
        });
    
        const response = await apiFetch(ENDPOINT_BY_ACTION[action], {
            method: "POST",
            body: JSON.stringify(payload),
        });
    
        if (!response) return;
    
        if (!response.ok) {
                const errorData = await response.json();
                errorEl.textContent = formatApiError(errorData);
                return;
            }
    
        const data = await response.json();
        successEl.textContent = data.message || "Action completed successfully";
        document.getElementById("stock-form").reset();
        updateVisibleFields();
    });