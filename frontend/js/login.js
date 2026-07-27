document.getElementById("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
    
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        const errorEl = document.getElementById("error-message");
        errorEl.textContent = "";
    
        try {
            const response = await fetch(`${API_BASE}/auth/login/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });
    
            if (!response.ok) {
                errorEl.textContent = "Invalid username or password";
                return;
            }
    
            const data = await response.json();
            localStorage.setItem("access_token", data.access);
            localStorage.setItem("refresh_token", data.refresh);
    
            window.location.href = "dashboard.html";
        } catch (err) {
            errorEl.textContent = "Could not connect to server. Is Django running?";
        }
    });