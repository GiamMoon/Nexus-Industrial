from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.admin.routes import admin_router # <--- IMPORTAR
# --- IMPORTACIÓN DE RUTAS ---
from src.api.auth.routes import auth_router
from src.api.market.routes import market_router
# from src.api.admin.routes import admin_router  <-- Lo crearemos a continuación

# Inicializamos la App
app = FastAPI(
    title="NEXUS AI ENTERPRISE v2.0",
    description="Sistema ERP + E-commerce con Inteligencia Artificial",
    version="2.0.0",
    docs_url="/docs", # Swagger UI
    redoc_url="/redoc"
)

# Configuración CORS (Vital para que los dos Frontends se conecten)
origins = [
    "http://localhost:3000", # Market (React/Vue/HTML)
    "http://localhost:4000", # Control (React/Vue/HTML)
    "https://tienda.midominio.com",
    "https://admin.midominio.com",
    "*" # Para desarrollo rápido, permite todo (Cuidado en prod)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RUTAS ---
app.include_router(auth_router)   # /auth/login/market, /auth/login/control
app.include_router(market_router) # /market/productos
app.include_router(admin_router) # Pendiente de activar en este paso

@app.get("/")
def health_check():
    return {
        "status": "online", 
        "system": "Nexus AI Core", 
        "version": "2.0.0",
        "mode": "Hybrid (Market + Control)"
    }