const API_URL = "http://localhost:8000";
let carrito = JSON.parse(localStorage.getItem('nexus_cart')) || [];
let token = localStorage.getItem('nexus_client_token');

document.addEventListener('DOMContentLoaded', () => {
    cargarProductos();
    actualizarBadgeCarrito();
    verificarSesion();
});


async function cargarProductos(query = "") {
    const grid = document.getElementById('product-grid');
    grid.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-primary"></div><p class="mt-2 text-muted">Cargando catálogo inteligente...</p></div>';

    try {
        const url = query 
            ? `${API_URL}/api/market/productos?q=${encodeURIComponent(query)}`
            : `${API_URL}/api/market/productos`;

        console.log(`🔍 Consultando API: ${url}`);

        const res = await fetch(url);
        
        if (!res.ok) {
            console.error(`Error API ${res.status}:`, await res.text());
            throw new Error(`Error API: ${res.status}`);
        }
        
        const productos = await res.json();
        console.log(" Productos recibidos:", productos.length); 
        renderizarGrid(productos);

    } catch (error) {
        console.error(" Error en cargarProductos:", error);
        grid.innerHTML = `<div class="alert alert-danger text-center">No se pudo conectar con Nexus Core.<br>Verifica que Docker esté corriendo en el puerto 8000.</div>`;
    }
}

function renderizarGrid(productos) {
    const grid = document.getElementById('product-grid');
    grid.innerHTML = "";

    if (productos.length === 0) {
        grid.innerHTML = `<div class="col-12 text-center text-muted py-5"><h3>🤷‍♂️</h3><p>No encontramos productos similares a tu búsqueda.</p></div>`;
        return;
    }

    productos.forEach(p => {
        const esOferta = p.precio_venta < p.precio_lista;
        const badgeIA = p.es_oferta_ia 
            ? `<span class="badge bg-primary bg-gradient mb-2"><i class="bi bi-stars"></i> Precio IA</span>` 
            : '';

        const imgError = "this.onerror=null; this.src='https://via.placeholder.com/300x200?text=Sin+Imagen';";

        const card = `
            <div class="col-md-6 col-lg-3">
                <div class="card card-product h-100 shadow-sm border-0">
                    <div class="position-relative p-3 text-center bg-white" style="height: 200px; display:flex; align-items:center; justify-content:center;">
                        <img src="${p.imagen_url}" 
                             alt="${p.nombre}" 
                             class="img-fluid" 
                             style="max-height: 180px; object-fit: contain;"
                             onerror="${imgError}">
                        <div class="position-absolute top-0 start-0 m-2">${badgeIA}</div>
                    </div>
                    
                    <div class="card-body d-flex flex-column bg-light bg-opacity-25">
                        <h6 class="fw-bold text-dark text-truncate" title="${p.nombre}">${p.nombre}</h6>
                        <small class="text-muted mb-3 font-monospace">${p.sku}</small>
                        
                        <div class="mt-auto">
                            <div class="d-flex justify-content-between align-items-end mb-3">
                                <div>
                                    ${esOferta ? `<small class="text-decoration-line-through text-muted" style="font-size:0.8rem">S/ ${p.precio_lista.toFixed(2)}</small><br>` : ''}
                                    <span class="fs-5 fw-bold ${esOferta ? 'text-success' : 'text-dark'}">S/ ${p.precio_venta.toFixed(2)}</span>
                                </div>
                                <span class="badge ${p.stock_disponible < 10 ? 'bg-danger' : 'bg-secondary'} rounded-pill">
                                    Stock: ${p.stock_disponible}
                                </span>
                            </div>
                            <button class="btn btn-dark w-100 fw-bold" onclick="agregarAlCarrito('${p.id}', '${p.nombre}', ${p.precio_venta})">
                                <i class="bi bi-cart-plus"></i> AGREGAR
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        grid.innerHTML += card;
    });
}

const searchInput = document.getElementById('search-input');
if(searchInput) {
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') buscarProductos();
    });
}

function buscarProductos() {
    const query = document.getElementById('search-input').value;
    cargarProductos(query);
}


function agregarAlCarrito(id, nombre, precio) {
    const item = carrito.find(i => i.id === id);
    if (item) {
        item.cantidad++;
    } else {
        carrito.push({ id, nombre, precio, cantidad: 1 });
    }
    guardarCarrito();
    
    const badge = document.getElementById('cart-badge');
    badge.classList.add('bg-warning');
    setTimeout(() => badge.classList.remove('bg-warning'), 300);
}

function guardarCarrito() {
    localStorage.setItem('nexus_cart', JSON.stringify(carrito));
    actualizarBadgeCarrito();
}

function actualizarBadgeCarrito() {
    const count = carrito.reduce((acc, item) => acc + item.cantidad, 0);
    const badge = document.getElementById('cart-badge');
    if(badge) badge.innerText = count;
}

function toggleCart() {
    const tbody = document.getElementById('cart-items-body');
    const totalSpan = document.getElementById('cart-total');
    let html = "";
    let total = 0;

    if (carrito.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">Tu carrito está vacío</td></tr>`;
        totalSpan.innerText = "0.00";
    } else {
        carrito.forEach(item => {
            const subtotal = item.precio * item.cantidad;
            total += subtotal;
            html += `
                <tr>
                    <td><small class="fw-bold">${item.nombre}</small></td>
                    <td>S/ ${item.precio.toFixed(2)}</td>
                    <td><span class="badge bg-secondary rounded-pill">${item.cantidad}</span></td>
                    <td class="fw-bold text-end">S/ ${subtotal.toFixed(2)}</td>
                </tr>`;
        });
        tbody.innerHTML = html;
        totalSpan.innerText = total.toFixed(2);
    }

    const modalEl = document.getElementById('cartModal');
    if(modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

async function procesarCheckout() {
    if (carrito.length === 0) return alert("❌ El carrito está vacío.");
    if (!token) {
        const modalCartEl = document.getElementById('cartModal');
        const modalLoginEl = document.getElementById('loginModal');
        
        if(modalCartEl) {
            const modalCart = bootstrap.Modal.getInstance(modalCartEl);
            modalCart.hide();
        }
        if(modalLoginEl) {
            const modalLogin = new bootstrap.Modal(modalLoginEl);
            modalLogin.show();
        }
        return;
    }

    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Conectando con SUNAT...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_URL}/api/market/checkout`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` 
            },
            body: JSON.stringify(carrito)
        });

        if (!res.ok) throw new Error("Error en la pasarela de pagos.");

        const data = await res.json();
        
        // ÉXITO
        alert(`✅ ¡COMPRA EXITOSA!\n\n📄 ID Pedido: ${data.venta_id}\n📡 Estado: ${data.status}\n\nLa factura electrónica se ha enviado a la cola de procesamiento.`);
        
        carrito = [];
        guardarCarrito();
        location.reload();

    } catch (e) {
        alert(" Error: " + e.message);
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}


const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-pass').value;

        try {
            const res = await fetch(`${API_URL}/api/auth/login/market`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (!res.ok) throw new Error("Usuario o contraseña incorrectos.");
            
            const data = await res.json();
            
            localStorage.setItem('nexus_client_token', data.access_token);
            localStorage.setItem('nexus_client_name', data.user_name);
            
            location.reload(); 

        } catch (err) {
            alert( err.message);
        }
    });
}

const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            ruc_dni: document.getElementById('reg-ruc').value,
            razon_social: document.getElementById('reg-razon').value,
            email: document.getElementById('reg-email').value,
            telefono: document.getElementById('reg-tel').value,
            password: document.getElementById('reg-pass').value
        };

        try {
            const res = await fetch(`${API_URL}/api/auth/register/market`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const json = await res.json();

            if (!res.ok) throw new Error(json.detail || "Error al registrarse");

            alert("🎉 Cuenta creada exitosamente. Por favor, inicia sesión.");
            location.reload();

        } catch (err) {
            alert("❌ " + err.message);
        }
    });
}

// Verificar Sesión
function verificarSesion() {
    const nombre = localStorage.getItem('nexus_client_name');
    const userArea = document.getElementById('user-area');
    
    if (nombre && userArea) {
        userArea.innerHTML = `
            <div class="dropdown">
                <button class="btn btn-outline-light dropdown-toggle btn-sm" type="button" data-bs-toggle="dropdown">
                    <i class="bi bi-person-circle"></i> ${nombre.split(' ')[0]}
                </button>
                <ul class="dropdown-menu dropdown-menu-end shadow">
                    <li><h6 class="dropdown-header">Mi Cuenta</h6></li>
                    <li><a class="dropdown-item" href="#">Mis Pedidos</a></li>
                    <li><a class="dropdown-item" href="#">Facturas XML</a></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><button class="dropdown-item text-danger" onclick="logout()">Cerrar Sesión</button></li>
                </ul>
            </div>
        `;
    }
}

function logout() {
    localStorage.removeItem('nexus_client_token');
    localStorage.removeItem('nexus_client_name');
    location.reload();
}


function toggleChat() {
    const chat = document.getElementById('chat-window');
    if (chat.classList.contains('d-none')) {
        chat.classList.remove('d-none');
        document.getElementById('chat-input').focus();
    } else {
        chat.classList.add('d-none');
    }
}

async function enviarPreguntaIA() {
    const input = document.getElementById('chat-input');
    const body = document.getElementById('chat-body');
    const pregunta = input.value.trim();
    
    if (!pregunta) return;

    body.innerHTML += `
        <div class="d-flex justify-content-end mb-2">
            <div class="bg-primary text-white p-2 rounded-3" style="max-width: 80%; font-size: 0.9em;">
                ${pregunta}
            </div>
        </div>`;
    input.value = "";
    body.scrollTop = body.scrollHeight;

    try {
        const formData = new URLSearchParams();
        formData.append('pregunta', pregunta);

        const res = await fetch(`${API_URL}/api/ai/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        const data = await res.json();
        const respuesta = data.respuesta || "No encontré información relevante en los manuales.";

        body.innerHTML += `
            <div class="d-flex justify-content-start mb-2">
                <div class="bg-white border p-2 rounded-3 shadow-sm text-dark" style="max-width: 85%; font-size: 0.9em;">
                    <strong class="text-info" style="font-size: 0.8em;"><i class="bi bi-robot"></i> NEXUS:</strong><br>
                    ${respuesta}
                </div>
            </div>`;

    } catch (e) {
        body.innerHTML += `<div class="text-center text-danger small my-2">Error de conexión con el cerebro IA.</div>`;
    }
    body.scrollTop = body.scrollHeight;
}