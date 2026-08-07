document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "index.html";
});

let cart = [];

async function loadSales() {
    const response = await apiFetch("/sales/");
    if (!response || !response.ok) return;
    const data = await response.json();
    const list = data.results ?? data;

    const tbody = document.querySelector("#sales-table tbody");
    tbody.innerHTML = "";

    list.forEach((s) => {
        const date = new Date(s.created_at).toLocaleString();
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${s.sale_number}</td>
            <td>${s.customer_name || "—"}</td>
            <td>${s.payment_method}</td>
            <td>${s.total}</td>
            <td>${s.sold_by_username || "—"}</td>
            <td>${date}</td>
            <td><button class="receipt-btn" data-id="${s.id}">Receipt</button></td>
        `;
        tbody.appendChild(tr);
    });

    document.querySelectorAll(".receipt-btn").forEach((btn) => {
        btn.addEventListener("click", () => showReceiptForSale(btn.dataset.id));
    });
}

document.getElementById("new-sale-btn").addEventListener("click", () => {
    cart = [];
    renderCart();
    document.getElementById("sale-error").textContent = "";
    document.getElementById("sale-success").textContent = "";
    document.getElementById("barcode-error").textContent = "";
    document.getElementById("modal-overlay").style.display = "flex";
    document.getElementById("barcode-input").focus();
});

document.getElementById("modal-overlay").addEventListener("click", (e) => {
    if (e.target.id === "modal-overlay") document.getElementById("modal-overlay").style.display = "none";
});

// Barcode lookup — adds item to cart
async function lookupAndAddToCart() {
    const barcodeEl = document.getElementById("barcode-input");
    const barcode = barcodeEl.value.trim();
    const errorEl = document.getElementById("barcode-error");
    errorEl.textContent = "";
    if (!barcode) return;

    const response = await apiFetch(`/products/lookup/?barcode=${encodeURIComponent(barcode)}`);
    if (!response || !response.ok) {
        errorEl.textContent = "No product found with that barcode.";
        return;
    }
    const product = await response.json();

    const existing = cart.find((item) => item.product_id === product.id && !item.batch_id);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({
            product_id: product.id,
            product_name: product.name,
            product_sku: product.sku,
            batch_id: null,
            quantity: 1,
            unit_price: product.selling_price,
        });
    }

    barcodeEl.value = "";
    barcodeEl.focus();
    renderCart();
}

document.getElementById("barcode-lookup-btn").addEventListener("click", lookupAndAddToCart);
document.getElementById("barcode-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        lookupAndAddToCart();
    }
});

function renderCart() {
    const tbody = document.querySelector("#cart-table tbody");
    tbody.innerHTML = "";
    let subtotal = 0;

    cart.forEach((item, index) => {
        const lineTotal = item.quantity * item.unit_price;
        subtotal += lineTotal;
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${item.product_name} (${item.product_sku})</td>
            <td><input type="number" class="cart-batch" data-index="${index}" placeholder="optional" style="width:70px" value="${item.batch_id ?? ""}"></td>
            <td><input type="number" class="cart-qty" data-index="${index}" value="${item.quantity}" min="1" style="width:60px"></td>
            <td><input type="number" step="0.01" class="cart-price" data-index="${index}" value="${item.unit_price}" style="width:80px"></td>
            <td>${lineTotal.toFixed(2)}</td>
            <td><button type="button" class="cart-remove" data-index="${index}">✕</button></td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById("cart-total").innerHTML = `<strong>Subtotal: ${subtotal.toFixed(2)}</strong>`;

    document.querySelectorAll(".cart-qty").forEach((el) => {
        el.addEventListener("change", (e) => {
            cart[e.target.dataset.index].quantity = parseInt(e.target.value) || 1;
            renderCart();
        });
    });
    document.querySelectorAll(".cart-price").forEach((el) => {
        el.addEventListener("change", (e) => {
            cart[e.target.dataset.index].unit_price = e.target.value;
            renderCart();
        });
    });
    document.querySelectorAll(".cart-batch").forEach((el) => {
        el.addEventListener("change", (e) => {
            cart[e.target.dataset.index].batch_id = e.target.value ? parseInt(e.target.value) : null;
        });
    });
    document.querySelectorAll(".cart-remove").forEach((el) => {
        el.addEventListener("click", (e) => {
            cart.splice(e.target.dataset.index, 1);
            renderCart();
        });
    });
}

document.getElementById("sale-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById("sale-error");
    const successEl = document.getElementById("sale-success");
    errorEl.textContent = "";
    successEl.textContent = "";

    if (cart.length === 0) {
        errorEl.textContent = "Add at least one item via barcode before completing the sale.";
        return;
    }

    const lines = cart.map((item) => {
        const line = { product_id: item.product_id, quantity: item.quantity, unit_price: item.unit_price };
        if (item.batch_id) line.batch_id = item.batch_id;
        return line;
    });

    const payload = {
        sale_number: document.getElementById("sale-number").value,
        warehouse_id: parseInt(document.getElementById("sale-warehouse").value),
        customer_name: document.getElementById("sale-customer-name").value,
        customer_phone: document.getElementById("sale-customer-phone").value,
        payment_method: document.getElementById("sale-payment").value,
        discount: document.getElementById("sale-discount").value || 0,
        lines: lines,
    };

    const response = await apiFetch("/sales/record/", {
        method: "POST",
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        errorEl.textContent = formatApiError(await response.json());
        return;
    }

    const data = await response.json();
    document.getElementById("modal-overlay").style.display = "none";
    document.getElementById("sale-form").reset();
    cart = [];
    loadSales();
    showReceipt(data);
});

function showReceipt(sale) {
    const linesHtml = sale.lines.map((l) =>
        `<tr><td>${l.product_name} (${l.product_sku})</td><td>${l.quantity}</td><td>${l.unit_price}</td><td>${l.line_total}</td></tr>`
    ).join("");

    document.getElementById("receipt-content").innerHTML = `
        <h3>StockSense — Receipt</h3>
        <p><strong>Sale #:</strong> ${sale.sale_number}</p>
        <p><strong>Date:</strong> ${new Date(sale.created_at).toLocaleString()}</p>
        <p><strong>Customer:</strong> ${sale.customer_name || "Walk-in"}</p>
        <p><strong>Payment:</strong> ${sale.payment_method}</p>
        <table style="width:100%; margin-top:10px;">
            <thead><tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead>
            <tbody>${linesHtml}</tbody>
        </table>
        <hr>
        <p><strong>Subtotal:</strong> ${sale.subtotal}</p>
        <p><strong>Discount:</strong> ${sale.discount}</p>
        <p style="font-size:18px;"><strong>Total: ${sale.total}</strong></p>
        <button onclick="window.print()">Print Receipt</button>
        <button id="close-receipt-btn">Close</button>
    `;
    document.getElementById("receipt-overlay").style.display = "flex";
    document.getElementById("close-receipt-btn").addEventListener("click", () => {
        document.getElementById("receipt-overlay").style.display = "none";
    });
}

async function showReceiptForSale(saleId) {
    const response = await apiFetch(`/sales/${saleId}/`);
    if (!response || !response.ok) return;
    const sale = await response.json();
    showReceipt(sale);
}

// Reports (unchanged)
document.getElementById("view-summary-btn").addEventListener("click", async () => {
    const response = await apiFetch("/sales/summary/?period=daily&days=30");
    if (!response || !response.ok) return;
    const data = await response.json();
    let html = `<h4>Daily Sales Summary (last 30 days)</h4><table><thead><tr><th>Date</th><th>Revenue</th><th>Transactions</th></tr></thead><tbody>`;
    data.summary.forEach((row) => {
        html += `<tr><td>${row.period_start}</td><td>${row.total_revenue}</td><td>${row.transaction_count}</td></tr>`;
    });
    html += `</tbody></table>`;
    document.getElementById("report-output").innerHTML = html;
});

document.getElementById("view-revenue-btn").addEventListener("click", async () => {
    const response = await apiFetch("/sales/revenue-report/?group_by=product");
    if (!response || !response.ok) return;
    const data = await response.json();
    let html = `<h4>Revenue by Product</h4><table><thead><tr><th>Product</th><th>Revenue</th><th>Units Sold</th></tr></thead><tbody>`;
    data.report.forEach((row) => {
        html += `<tr><td>${row.product__name || "—"}</td><td>${row.revenue}</td><td>${row.quantity_sold}</td></tr>`;
    });
    html += `</tbody></table>`;
    document.getElementById("report-output").innerHTML = html;
});

document.getElementById("view-customers-btn").addEventListener("click", async () => {
    const response = await apiFetch("/sales/customer-trends/");
    if (!response || !response.ok) return;
    const data = await response.json();
    let html = `<h4>Customer Trends</h4><table><thead><tr><th>Customer</th><th>Phone</th><th>Total Spent</th><th>Orders</th></tr></thead><tbody>`;
    data.customers.forEach((row) => {
        html += `<tr><td>${row.customer_name || "—"}</td><td>${row.customer_phone || "—"}</td><td>${row.total_spent}</td><td>${row.order_count}</td></tr>`;
    });
    html += `</tbody></table>`;
    document.getElementById("report-output").innerHTML = html;
});

loadSales();