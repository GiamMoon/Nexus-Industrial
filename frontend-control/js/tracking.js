document.addEventListener('DOMContentLoaded', () => {
    initMap();
});

function initMap() {
    // 1. Inicializar Mapa (Centrado en Lima, Perú)
    const map = L.map('map').setView([-12.0464, -77.0428], 13);

    // 2. Capa Oscura (Estilo Enterprise)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // 3. Obtener Datos (Simulación de Fetch a API Backend)
    // En producción: const res = await fetch('/api/admin/vendedores/ubicacion');
    const vendedores = generarDatosSimulados();

    // 4. Dibujar Marcadores
    vendedores.forEach(v => {
        const icono = L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color: #0dcaf0; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #0dcaf0;"></div>`,
            iconSize: [15, 15],
            iconAnchor: [7, 7]
        });

        const marker = L.marker([v.lat, v.lng], { icon: icono }).addTo(map);
        
        // Popup con info del vendedor
        marker.bindPopup(`
            <div class="text-center">
                <strong>${v.nombre}</strong><br>
                <span class="badge bg-success">En Ruta</span><br>
                <small class="text-muted">Última act: Hace 2 min</small>
            </div>
        `);
    });
}

function generarDatosSimulados() {
    // Estos datos simulan la respuesta de la API basándose en lo que el Seeder creó
    // Lat/Lon alrededor de Lima
    return [
        { nombre: "Juan Pérez", lat: -12.046, lng: -77.042 },
        { nombre: "Maria Lopez", lat: -12.050, lng: -77.030 },
        { nombre: "Carlos Ruiz", lat: -12.030, lng: -77.050 },
        { nombre: "Ana Diaz", lat: -12.060, lng: -77.020 },
        { nombre: "Pedro Gomez", lat: -12.040, lng: -77.060 },
        { nombre: "Luisa Fernandez", lat: -12.070, lng: -77.040 },
        { nombre: "Jorge Chavez", lat: -12.035, lng: -77.035 },
        { nombre: "Sofia Torres", lat: -12.055, lng: -77.045 }
    ];
}