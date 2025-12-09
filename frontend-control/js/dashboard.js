

console.group("🚀 INICIO DEL SISTEMA DASHBOARD");

if (typeof API_URL === 'undefined') {
    window.API_URL = "http://localhost:8000";
    console.warn("⚠️ API_URL no estaba definida. Usando fallback:", window.API_URL);
} else {
    console.log("✅ API_URL detectada:", API_URL);
}

var token = localStorage.getItem('nexus_admin_token');
if (token) {
    console.log("🔑 Token encontrado:", token.substring(0, 10) + "...");
} else {
    console.error("⛔ TOKEN NO ENCONTRADO EN LOCALSTORAGE");
}

console.groupEnd();

if (!token && !window.location.href.includes('login.html')) {
    alert("No se detectó sesión. Redirigiendo al login...");
    window.location.href = "login.html";
}

document.addEventListener('DOMContentLoaded', () => {
    console.log(" DOM Cargado. Ejecutando scripts...");
    
    cargarKPIs();
    iniciarWebSocket();
    initChart();
});


async function cargarKPIs() {
    console.group("CARGA DE DATOS (KPIs)");
    
    const endpoint = `${API_URL}/api/admin/dashboard`;
    console.log("Intentando conectar a:", endpoint);

    try {
        const res = await fetch(endpoint, {
            method: 'GET',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` 
            }
        });
        
        console.log(` Estado HTTP recibido: ${res.status} ${res.statusText}`);


        if(res.status === 401) {
            console.error("ERROR 401: No autorizado. El token venció.");
            alert("Tu sesión ha expirado. Por favor inicia sesión nuevamente.");
            localStorage.removeItem('nexus_admin_token'); 
            window.location.href = "login.html";
            return;
        }
        
        if(res.status === 404) {
            console.error("ERROR 404 CRÍTICO: La ruta no existe.");
            console.warn("SOLUCIÓN: Verifica el orden de los routers en main.py. 'admin_router' debe ir ANTES que 'market_router'.");
            alert("Error 404: No se encuentra el servicio de Dashboard. Revisa la consola para ver la solución.");
            return;
        }

        if(!res.ok) {
            const errorData = await res.json().catch(() => ({})); 
            throw new Error(`Error del Servidor: ${errorData.detail || res.statusText}`);
        }

        const data = await res.json();
        console.log(" Datos recibidos correctamente:", data);

        actualizarElemento('kpi-ventas', `S/ ${data.ventas_hoy.toFixed(2)}`);
        actualizarElemento('kpi-stock', data.productos_bajo_stock);
        actualizarElemento('kpi-ticket', `S/ ${data.ticket_promedio.toFixed(2)}`);

       if (data.alerta_ia) {
            console.warn("ALERTA IA DETECTADA:", data.alerta_ia);
            const alertBox = document.getElementById('ai-alert-box');
            const alertMsg = document.getElementById('ai-msg');
            if(alertBox && alertMsg) {
                alertBox.classList.remove('d-none');
                alertMsg.innerText = data.alerta_ia;
            }
        }

    } catch (e) { 
        console.error("EXCEPCIÓN EN FETCH:", e); 
    } finally {
        console.groupEnd();
    }
}

function actualizarElemento(id, valor) {
    const el = document.getElementById(id);
    if(el) el.innerText = valor;
    else console.warn(` Elemento DOM no encontrado: #${id}`);
}


function iniciarWebSocket() {
    const wsUrl = API_URL.replace("http", "ws") + "/ws";
    console.log(`🔌 Conectando WebSocket a: ${wsUrl}`);
    
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("WebSocket: CONEXIÓN ESTABLECIDA");
        const ind = document.getElementById('live-indicator');
        if(ind) {
            ind.innerText = " EN VIVO";
            ind.classList.remove('bg-secondary');
            ind.classList.add('bg-danger', 'animate-pulse');
        }
    };

    ws.onmessage = (event) => {
        if (event.data.includes("NUEVA_VENTA")) {
            console.info("🔔 EVENTO: Nueva venta detectada. Actualizando UI...");
            notificarVentaVisual();
            cargarKPIs();     
            actualizarGrafica();
        }
    };
    
    ws.onclose = () => {
        console.warn(" WebSocket: DESCONECTADO. Reintentando en 5s...");
        const ind = document.getElementById('live-indicator');
        if(ind) {
            ind.innerText = " OFFLINE";
            ind.classList.remove('bg-danger', 'animate-pulse');
            ind.classList.add('bg-secondary');
        }
        setTimeout(iniciarWebSocket, 5000);
    };
    
    ws.onerror = (err) => {
        console.error("WebSocket Error:", err);
    };
}

function notificarVentaVisual() {
    const indicador = document.getElementById('live-indicator');
    if(indicador) {
        indicador.classList.remove('bg-danger');
        indicador.classList.add('bg-warning');
        setTimeout(() => {
            indicador.classList.remove('bg-warning');
            indicador.classList.add('bg-danger');
        }, 500);
    }
}

let chart;

function initChart() {
    const ctx = document.getElementById('liveChart');
    if(!ctx) {
        console.warn("No se encontró el canvas #liveChart. Saltando gráfica.");
        return; 
    }

    console.log("Inicializando Chart.js");
    chart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Flujo de Ventas (S/)',
                data: [],
                borderColor: '#0dcaf0',
                backgroundColor: 'rgba(13, 202, 240, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false }, 
                y: { grid: { color: '#333' }, ticks: { color: '#888' } }
            },
            animation: false
        }
    });
    
    for(let i=0; i<15; i++) actualizarGrafica(Math.random() * 50);
}

function actualizarGrafica(valorSimulado = null) {
    if(!chart) return;

    const now = new Date();
    const timeLabel = now.toLocaleTimeString();
    const valor = valorSimulado !== null ? valorSimulado : (Math.random() * 100 + 150); 
    
    const updateLabel = document.getElementById('last-update');
    if(updateLabel) updateLabel.innerText = timeLabel;

    chart.data.labels.push(timeLabel);
    chart.data.datasets[0].data.push(valor);
    
    if (chart.data.labels.length > 20) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.update();
}


async function crearProducto(e) {
    e.preventDefault();
    console.group("📦 CREAR PRODUCTO");

    const btn = e.submitter;
    const originalText = btn.innerHTML;
    btn.innerHTML = "⏳ Procesando..."; btn.disabled = true;

    const data = {
        nombre: document.getElementById('new-name').value,
        sku: document.getElementById('new-sku').value,
        descripcion_tecnica: document.getElementById('new-desc').value,
        precio_base: parseFloat(document.getElementById('new-price').value),
        stock_inicial: parseInt(document.getElementById('new-stock').value),
        imagen_url: `https://via.placeholder.com/300?text=${encodeURIComponent(document.getElementById('new-name').value)}`
    };

    console.log(" Payload a enviar:", data);

    try {
        const res = await fetch(`${API_URL}/api/admin/productos`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` 
            },
            body: JSON.stringify(data)
        });

        const json = await res.json();
        
        if (!res.ok) throw new Error(json.detail || "Error desconocido al crear");
        
        console.log("Éxito:", json);
        alert(`PRODUCTO CREADO EXITOSAMENTE\n\nID: ${json.id}\nStatus: ${json.msg}`);
        
        e.target.reset();
        
    } catch (err) {
        console.error("Error al crear producto:", err);
        alert(" Error: " + err.message);
    } finally {
        btn.innerHTML = originalText; btn.disabled = false;
        console.groupEnd();
    }
}


async function subirManual(e) {
    e.preventDefault();
    console.log("Iniciando subida de PDF...");

    const btn = e.submitter;
    btn.innerHTML = " Vectorizando..."; btn.disabled = true;

    const prodId = document.getElementById('pdf-prod-id').value.trim();
    const fileInput = document.getElementById('pdf-file');
    
    if (fileInput.files.length === 0) {
        alert(" Por favor selecciona un archivo PDF.");
        btn.innerHTML = "Procesar Vectores"; btn.disabled = false;
        return;
    }

    const formData = new FormData();
    formData.append('producto_id', prodId);
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch(`${API_URL}/api/ai/ingestar-pdf`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        const json = await res.json();
        if (!res.ok) throw new Error(json.detail);

        console.log(" PDF Procesado:", json);
        alert(`MANUAL INTEGRADO A LA IA\n\nCaracteres leídos: ${json.chars}`);
        e.target.reset();

    } catch (err) {
        console.error("Error PDF:", err);
        alert("Error: " + err.message);
    } finally {
        btn.innerHTML = "Procesar Vectores"; btn.disabled = false;
    }
}

async function activarAgente() {
    const id = prompt("Ingrese el ID (UUID) del producto a analizar:");
    if(!id) return;

    alert("Agente de Compras activado. Analizando historial y mercado...");

    try {
        const res = await fetch(`${API_URL}/api/ai/agente-compras/${id}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const json = await res.json();
        console.log(" Respuesta Agente:", json);
        
        let msg = `REPORTE DE INTELLIGENCIA:\n\nDecisión: ${json.decision}\nRazón: ${json.razon}`;
        if(json.archivo) msg += `\n\n ORDEN DE COMPRA GENERADA:\n${json.archivo}`;
        
        alert(msg);

    } catch (err) {
        console.error(" Error Agente:", err);
        alert("Fallo en el análisis: " + err.message);
    }
}