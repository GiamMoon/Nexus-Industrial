from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.infrastructure.database import get_db
from src.infrastructure.models import VentaModel, ClienteModel, DetalleVentaModel
from src.api.deps import get_current_client
from src.services.ai_catalog import AISearchService, DynamicPricingService
from src.infrastructure.adapters.queue_adapter import QueueAdapter
from .schemas import ProductoCardSchema

market_router = APIRouter(prefix="/market", tags=["Marketplace Público"])

@market_router.get("/productos", response_model=List[ProductoCardSchema])
def catalogo_inteligente(
    q: str = Query(None),
    db: Session = Depends(get_db)
):
    ai_service = AISearchService(db)
    productos = ai_service.buscar_productos_inteligentes(query=q)
    
    resultado = []
    for p in productos:
        precio_smart = DynamicPricingService.calcular_precio_final(p)
        
        dto = ProductoCardSchema(
            id=p.id,
            nombre=p.nombre,
            sku=p.sku,
            descripcion=p.descripcion,
            imagen_url=p.imagen_url,
            precio_lista=float(p.precio_base),
            precio_venta=precio_smart,
            es_oferta_ia=(precio_smart != float(p.precio_base)),
            stock_disponible=p.stock
        )
        resultado.append(dto)
        
    return resultado

@market_router.post("/checkout")
def procesar_compra(
    carrito: List[dict],
    cliente=Depends(get_current_client),
    db: Session = Depends(get_db)
):
    if not carrito:
        raise HTTPException(status_code=400, detail="Carrito vacío")

    total_venta = sum(float(item['precio']) * int(item['cantidad']) for item in carrito)

    nueva_venta = VentaModel(
        cliente_id=cliente.id,
        total=total_venta,
        estado="PENDIENTE_FACTURACION"
    )
    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)
    
    for item in carrito:
        detalle = DetalleVentaModel(
            venta_id=nueva_venta.id,
            producto_id=item['id'],
            cantidad=int(item['cantidad']),
            precio_unitario=float(item['precio']),
            subtotal=float(item['precio']) * int(item['cantidad'])
        )
        db.add(detalle)
    db.commit()

    try:
        cola = QueueAdapter()
        cola.encolar_factura(str(nueva_venta.id))
    except Exception as e:
        print(f"Redis Error: {e}")
    
    return {
        "msg": "Compra exitosa. Facturando...",
        "venta_id": str(nueva_venta.id),
        "status": "PROCESANDO",
        "total": total_venta
    }