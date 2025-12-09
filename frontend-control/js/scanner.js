const API_URL = "http://localhost:8000";
const token = localStorage.getItem('nexus_admin_token');
let html5QrcodeScanner;
let productoActualId = null;

document.addEventListener('DOMContentLoaded', () => {
    iniciarEscaner();
});

function iniciarEscaner() {
    html5QrcodeScanner = new Html5Qrcode("reader");
    
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };
    
    html5QrcodeScanner.start(
        { facingMode: "environment" }, 
        config, 
        onScanSuccess, 
        onScanFailure
    ).catch(err => {
        console.error("Error iniciando cámara", err);
        document.getElementById('reader').innerHTML = 
            `<div class="alert alert-danger">No se pudo acceder a la cámara. Revise permisos.</div>`;
    });
}

const beep = new Audio('https://www.soundjay.com/buttons/beep-01a.mp3');

async function onScanSuccess(decodedText, decodedResult) {
    html5QrcodeScanner.pause();
    beep.play();

    try {
        const res = await fetch(`${API_URL}/api/market/productos?q=${encodeURIComponent(decodedText)}`);
        const productos = await res.json();

        if (productos.length > 0) {
            mostrarOverlay(productos[0]);
        } else {
            alert("Producto no encontrado en la base de datos.");
            setTimeout(() => html5QrcodeScanner.resume(), 2000);
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
        html5QrcodeScanner.resume();
    }
}

function onScanFailure(error) {
    // No hacer nada, sigue intentando leer
}

function mostrarOverlay(producto) {
    productoActualId = producto.id;
    
    document.getElementById('ar-nombre').innerText = producto.nombre;
    document.getElementById('ar-sku').innerText = producto.sku;
    document.getElementById('ar-stock').innerText = producto.stock_disponible;
    
    const overlay = document.getElementById('ar-overlay');
    overlay.classList.remove('d-none');
    overlay.classList.add('animate-pop');
}

async function ajustarStock(cantidad) {
    if (!productoActualId) return;

    const tipo = cantidad > 0 ? "ENTRADA" : "SALIDA";
    const valorAbsoluto = Math.abs(cantidad);

    try {
        const res = await fetch(`${API_URL}/api/admin/inventario/${productoActualId}/ajuste`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                cantidad: valorAbsoluto,
                tipo_movimiento: tipo,
                motivo: "AJUSTE_AR"
            })
        });

        if (!res.ok) throw new Error("Error actualizando stock");

        const data = await res.json();
        
        document.getElementById('ar-stock').innerText = data.nuevo_stock;
        
        const btn = event.target;
        const originalText = btn.innerText;
        btn.innerText = "✅";
        setTimeout(() => btn.innerText = originalText, 1000);

    } catch (e) {
        alert(e.message);
    }
}

function cerrarOverlay() {
    document.getElementById('ar-overlay').classList.add('d-none');
    html5QrcodeScanner.resume();
}