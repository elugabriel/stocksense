document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "index.html";
    });
    
    async function loadAlerts() {
        const response = await apiFetch("/alerts/?resolved=false");
        if (!response || !response.ok) return;
        const data = await response.json();
        const list = data.results ?? data;
    
        const tbody = document.querySelector("#alerts-table tbody");
        tbody.innerHTML = "";
    
        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6">No active alerts.</td></tr>`;
            return;
        }
    
        list.forEach((a) => {
            const tr = document.createElement("tr");
            const date = new Date(a.created_at).toLocaleString();
            tr.innerHTML = `
                <td><span class="severity-badge severity-${a.severity}">${a.severity}</span></td>
                <td>${a.alert_type.replace(/_/g, " ")}</td>
                <td>${a.product_sku || "—"}</td>
                <td>${a.message}</td>
                <td>${date}</td>
                <td><button class="resolve-btn" data-id="${a.id}">Resolve</button></td>
            `;
            tbody.appendChild(tr);
        });
    
        document.querySelectorAll(".resolve-btn").forEach((btn) => {
            btn.addEventListener("click", async () => {
                await apiFetch(`/alerts/${btn.dataset.id}/resolve/`, { method: "POST" });
                loadAlerts();
            });
        });
    }
    
    document.getElementById("run-checks-btn").addEventListener("click", async () => {
        const response = await apiFetch("/alerts/run-checks/", { method: "POST" });
        if (response && response.ok) {
            const data = await response.json();
            alert(`Checks complete. ${data.total} new alert(s) created.`);
            loadAlerts();
        }
    });
    
    loadAlerts();