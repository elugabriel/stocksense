document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    let currentProduct = null;
    
    document.getElementById("load-product-btn").addEventListener("click", async () => {
        const productId = document.getElementById("product-id-input").value;
        if (!productId) return;
    
        const response = await apiFetch(`/products/${productId}/`);
        if (!response || !response.ok) {
            alert("Product not found.");
            return;
        }
        currentProduct = await response.json();
    
        document.getElementById("reorder-level-input").value = currentProduct.reorder_level;
    
        // Pull current stock from the dashboard stock endpoint
        const stockResponse = await apiFetch("/dashboard/stock/");
        if (stockResponse && stockResponse.ok) {
            const stockData = await stockResponse.json();
            const match = stockData.by_product.find((p) => p.product__sku === currentProduct.sku);
            if (match) {
                document.getElementById("reorder-current-stock").value = match.total_quantity;
            }
        }
    
        document.getElementById("reorder-section").style.display = "block";
        loadForecastAndComparison(productId);
    });
    
    async function loadForecastAndComparison(productId) {
        // Standard forecast (used for the chart/table)
        const forecastRes = await apiFetch(`/products/${productId}/forecasted-revenue/?forecast_days=30`);
        const forecastSection = document.getElementById("forecast-chart-section");
        const forecastNote = document.getElementById("forecast-model-note");
        const forecastTbody = document.querySelector("#forecast-table tbody");
        forecastTbody.innerHTML = "";
    
        if (forecastRes && forecastRes.ok) {
            const data = await forecastRes.json();
            if (data.error) {
                forecastSection.style.display = "block";
                forecastNote.textContent = data.error;
            } else {
                forecastSection.style.display = "block";
                forecastNote.textContent = `Model used: ${data.model_used} | Predicted units over 30 days: ${data.predicted_units} | Projected revenue: ${data.projected_revenue}`;
                data.daily_breakdown.forEach((row) => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `<td>${row.date}</td><td>${row.predicted_quantity}</td>`;
                    forecastTbody.appendChild(tr);
                });
            }
        }
    }
    
    document.getElementById("get-recommendation-btn").addEventListener("click", async () => {
        if (!currentProduct) return;
    
        const resultEl = document.getElementById("reorder-result");
        resultEl.innerHTML = "<p><em>Calculating recommendation...</em></p>";
    
        // Build sales history from movement/sales data via the sales history endpoint
        const historyRes = await apiFetch(`/products/${currentProduct.id}/sales-history/`);
        if (!historyRes || !historyRes.ok) {
            resultEl.innerHTML = "<p class='error'>Could not load sales history.</p>";
            return;
        }
        const historyData = await historyRes.json();
    
        if (!historyData.history || historyData.history.length < 2) {
            resultEl.innerHTML = `<p class='error'>Not enough sales history yet to generate a reorder recommendation (need at least 2 distinct sale dates).</p>`;
            return;
        }
    
        // Aggregate by date for the AI engine call — reuse the pattern the backend uses
        const historyByDate = {};
        historyData.history.forEach((h) => {
            historyByDate[h.date] = (historyByDate[h.date] || 0) + h.quantity;
        });
        const history = Object.entries(historyByDate).map(([date, quantity]) => ({ date, quantity }));
    
        const payload = {
            product_sku: currentProduct.sku,
            history: history,
            current_stock: parseInt(document.getElementById("reorder-current-stock").value),
            reorder_level: parseInt(document.getElementById("reorder-level-input").value),
            vendor_lead_time_days: parseInt(document.getElementById("reorder-lead-time").value),
            safety_stock_days: parseInt(document.getElementById("reorder-safety-days").value),
        };
    
        try {
            const aiResponse = await fetch("http://127.0.0.1:8001/recommend-reorder", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await aiResponse.json();
    
            if (data.error) {
                resultEl.innerHTML = `<p class="error">${data.error}</p>`;
                return;
            }
    
            const badgeClass = data.should_reorder_now ? "severity-critical" : "severity-info";
            const badgeText = data.should_reorder_now ? "REORDER NOW" : "STOCK OK";
    
            resultEl.innerHTML = `
                <div class="kpi-card" style="border-left-color: ${data.should_reorder_now ? '#c0392b' : '#27ae60'}">
                    <span class="severity-badge ${badgeClass}">${badgeText}</span>
                    <p style="margin-top:12px;"><strong>Recommended Order Quantity:</strong> ${data.recommended_order_quantity} units</p>
                    <p><strong>Model Used:</strong> ${data.model_used}</p>
                    <p><strong>Predicted Demand (lead time + buffer):</strong> ${data.predicted_demand_during_lead_time_and_buffer}</p>
                    <p><strong>Projected Stock at Delivery:</strong> ${data.projected_stock_at_delivery_date}</p>
                    <p style="margin-top:10px; color:#555;">${data.reasoning}</p>
                </div>
            `;
        } catch (err) {
            resultEl.innerHTML = `<p class="error">Could not reach the AI Engine. Make sure it's running on port 8001.</p>`;
        }
    });