document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "index.html";
});

let cart = [];
let selectedPaymentMethod = "cash";

async function loadSales() {
    const response = await apiFetch("/sales/");
    if (!response || !response.ok) return;
    const data = await response.json();
    const list = data.results ?? data;

    const tbody = document.querySelector("#sales-table tbody");
    tbody.innerHTML = "";

    list.slice(0, 10).forEach((s) => {
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

// --- Payment method selector ---
document.querySelectorAll(".pos-payment-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".pos-payment-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        selectedPaymentMethod = btn.dataset.method;
    });
});

// --- Barcode lookup — adds item to cart ---
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

document.getElementById("clear-cart-btn").addEventListener("click", () => {
    cart = [];
    renderCart();
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
            <td>${index + 1}</td>
            <td>${item.product_name}</td>
            <td>${item.product_sku}</td>
            <td>₦${parseFloat(item.unit_price).toFixed(2)}</td>
            <td>
                <div class="qty-control">
                    <button type="button" class="qty-dec" data-index="${index}">−</button>
                    <span>${item.quantity}</span>
                    <button type="button" class="qty-inc" data-index="${index}">+</button>
                </div>
            </td>
            <td>₦${lineTotal.toFixed(2)}</td>
            <td><button type="button" class="cart-remove" data-index="${index}">✕</button></td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById("cart-count").textContent = cart.length;
    document.getElementById("summary-item-count").textContent = cart.reduce((sum, i) => sum + i.quantity, 0);
    document.getElementById("summary-subtotal").textContent = `₦${subtotal.toFixed(2)}`;
    updateTotal(subtotal);

    document.querySelectorAll(".qty-inc").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            cart[e.target.dataset.index].quantity += 1;
            renderCart();
        });
    });
    document.querySelectorAll(".qty-dec").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            const idx = e.target.dataset.index;
            if (cart[idx].quantity > 1) {
                cart[idx].quantity -= 1;
            } else {
                cart.splice(idx, 1);
            }
            renderCart();
        });
    });
    document.querySelectorAll(".cart-remove").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            cart.splice(e.target.closest("button").dataset.index, 1);
            renderCart();
        });
    });
}

function updateTotal(subtotal) {
    const discount = parseFloat(document.getElementById("sale-discount").value) || 0;
    const total = Math.max(0, subtotal - discount);
    document.getElementById("summary-total").textContent = `₦${total.toFixed(2)}`;
}

document.getElementById("sale-discount").addEventListener("input", () => {
    const subtotal = cart.reduce((sum, i) => sum + i.quantity * i.unit_price, 0);
    updateTotal(subtotal);
});

// --- Complete sale ---
document.getElementById("complete-sale-btn").addEventListener("click", async () => {
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
        payment_method: selectedPaymentMethod,
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
    cart = [];
    document.getElementById("sale-number").value = "";
    document.getElementById("sale-customer-name").value = "";
    document.getElementById("sale-customer-phone").value = "";
    document.getElementById("sale-discount").value = "0";
    renderCart();
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

// --- Reports (unchanged) ---
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

document.getElementById("view-profit-btn").addEventListener("click", async () => {
    const response = await apiFetch("/sales/profit-margin-report/?period=daily&days=30");
    if (!response || !response.ok) return;
    const data = await response.json();
    let html = `<h4>Profit Margin Report</h4><table><thead><tr><th>Date</th><th>Revenue</th><th>Cost</th><th>Profit</th><th>Margin %</th></tr></thead><tbody>`;
    data.report.forEach((row) => {
        html += `<tr><td>${row.period_start}</td><td>${row.revenue}</td><td>${row.cost}</td><td>${row.profit}</td><td>${row.gross_margin_percent}%</td></tr>`;
    });
    html += `</tbody></table>`;
    document.getElementById("report-output").innerHTML = html;
});

loadSales();