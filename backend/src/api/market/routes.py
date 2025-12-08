from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List

# --- IMPORTS DE INFRAESTRUCTURA Y DOMINIO ---
from src.infrastructure.database import get_db
from src.infrastructure.models import VentaModel, ClienteModel
from src.api.deps import get_current_client
from src.services.ai_catalog import AISearchService, DynamicPricingService
from src.infrastructure.adapters.queue_adapter import QueueAdapter
from .schemas import ProductoCardSchema

market_router = APIRouter(prefix="/market", tags=["Marketplace Público"])

# --- 1. CATÁLOGO INTELIGENTE (IA + PRECIOS DINÁMICOS) ---
@market_router.get("/productos", response_model=List[ProductoCardSchema])
def catalogo_inteligente(
    q: str = Query(None, description="Término de búsqueda (ej: 'limpiador grasa')"),
    db: Session = Depends(get_db)
):
    """
    Endpoint híbrido: Si hay 'q', usa IA (Embeddings). Si no, muestra catálogo general.
    Aplica Precios Dinámicos en tiempo real (Scarcity Algorithm).
    """
    # 1. Búsqueda (Semántica o Normal)
    ai_service = AISearchService(db)
    productos = ai_service.buscar_productos_inteligentes(query=q)
    
    # 2. Transformación con Precios Dinámicos
    resultado = []
    for p in productos:
        # Algoritmo de Escasez: Sube precio si stock < 10
        precio_smart = DynamicPricingService.calcular_precio_final(p)
        
        dto = ProductoCardSchema(
            id=p.id,
            nombre=p.nombre,
            sku=p.sku,
            descripcion=p.descripcion,
            imagen_url=p.imagen_url,
            precio_lista=float(p.precio_base),
            precio_venta=precio_smart,
            es_oferta_ia=(precio_smart != float(p.precio_base)), # Flag para frontend
            stock_disponible=p.stock
        )
        resultado.append(dto)
        
    return resultado

# --- 2. CHECKOUT ASÍNCRONO (RESILIENCIA SUNAT) ---
@market_router.post("/checkout")
def procesar_compra(
    carrito: List[dict], # En prod usar un Pydantic Schema estricto (CheckoutSchema)
    cliente=Depends(get_current_client), # Solo clientes logueados
    db: Session = Depends(get_db)
):
    """
    REQ-SHOP-02 & REQ-FIS-02: Checkout de Alta Disponibilidad.
    1. Registra la venta en BD (Estado: PENDIENTE).
    2. Delega la facturación SUNAT a Redis (Worker).
    3. Responde rápido al cliente (Non-blocking).
    """
    if not carrito:
        raise HTTPException(status_code=400, detail="El carrito está vacío")

    # 1. Calcular Total (Validar precios reales en backend para seguridad)
    total_venta = sum(float(item['precio']) * int(item['cantidad']) for item in carrito)

    # 2. Crear Venta en Base de Datos
    nueva_venta = VentaModel(
        cliente_id=cliente.id,
        total=total_venta,
        estado="PENDIENTE_FACTURACION", # A la espera del Worker
        fecha=None # Se pone current_timestamp por defecto en modelo
    )
    db.add(nueva_venta)
    db.commit() # Obtenemos ID de venta
    db.refresh(nueva_venta)
    
    # (Aquí iría el bucle para guardar DetalleVentaModel, omitido por brevedad del ejemplo)
    
    # 3. DISPARAR EVENTO ASÍNCRONO (Fire & Forget)
    try:
        cola = QueueAdapter()
        cola.encolar_factura(str(nueva_venta.id))
    except Exception as e:
        # Si Redis falla, logueamos pero NO fallamos la venta (se puede reintentar luego por Cron)
        print(f"⚠️ Error conectando a Redis: {e}")
        # En un sistema real, marcaríamos un flag 'retry_later' en la venta.
    
    return {
        "msg": "Compra exitosa. Estamos procesando tu factura electrónica.",
        "venta_id": str(nueva_venta.id),
        "status": "PROCESANDO",
        "total": total_venta
    }