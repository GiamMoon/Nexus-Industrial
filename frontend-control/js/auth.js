const API_URL = "http://localhost:8000";

// --- LOGIN LOGIC ---
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const res = await fetch(`${API_URL}/api/auth/login/control`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (!res.ok) throw new Error("Acceso Denegado");
            const data = await res.json();
            
            localStorage.setItem('nexus_admin_token', data.access_token);
            window.location.href = "index.html";
        } catch (err) {
            alert(err.message);
        }
    });
}

function checkAuth() {
    const token = localStorage.getItem('nexus_admin_token');
    if (!token && !window.location.href.includes('login.html')) {
        window.location.href = "login.html";
    }
}

function logout() {
    localStorage.removeItem('nexus_admin_token');
    window.location.href = "login.html";
}

checkAuth();