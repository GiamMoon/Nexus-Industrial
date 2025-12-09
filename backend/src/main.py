import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from src.api.auth.routes import auth_router
from src.api.market.routes import market_router
from src.api.admin.routes import admin_router
from src.api.ai.routes import ai_router
from src.api.webhooks.routes import webhook_router

app = FastAPI(
    title="NEXUS AI ENTERPRISE v2.0",
    description="Sistema ERP + E-commerce con Inteligencia Artificial",
    version="2.0.0"
)

origins = [
    "http://localhost:3000",    
    "http://localhost:4000",      
    "http://127.0.0.1:5500",      
    "*"                           
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.on_event("startup")
def startup_event():
    """
    Imprime todas las rutas registradas al iniciar para detectar errores 404.
    """
    print("\n" + "="*60, file=sys.stderr)
    print("INICIANDO NEXUS AI - MAPA DE RUTAS DETECTADO:", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    rutas = []
    for route in app.routes:
        if hasattr(route, "path"):
            rutas.append(route.path)
            if "/api/" in route.path:
                print(f"📍 {route.methods} \t {route.path}", file=sys.stderr)
            
    print("-" * 60, file=sys.stderr)

    target = "/api/admin/dashboard"
    if target in rutas:
        print(f" ÉXITO: La ruta crítica '{target}' está ACTIVA.", file=sys.stderr)
    else:
        print(f" ERROR CRÍTICO: La ruta '{target}' NO EXISTE.", file=sys.stderr)
        print("   POSIBLES CAUSAS:", file=sys.stderr)
        print("   1. En 'src/api/admin/routes.py' falta el 'prefix=\"/admin\"'.", file=sys.stderr)
        print("   2. El router de Admin no se está importando correctamente.", file=sys.stderr)
    
    print("="*60 + "\n", file=sys.stderr)

app.include_router(auth_router, prefix="/api")    
app.include_router(admin_router, prefix="/api")  
app.include_router(ai_router, prefix="/api")      
app.include_router(webhook_router, prefix="/api") 

app.include_router(market_router, prefix="/api")  

@app.get("/")
def health_check():
    return {
        "status": "online", 
        "system": "Nexus AI Core v2.0",
        "docs": "http://localhost:8000/docs"
    }

@app.on_event("startup")
def print_routes():
    print("\n" + "="*50)
    print(" LISTA DE RUTAS ACTIVAS:")
    for route in app.routes:
        if hasattr(route, "path") and "/api/" in route.path:
            print(f" {route.path}")
    print("="*50 + "\n")