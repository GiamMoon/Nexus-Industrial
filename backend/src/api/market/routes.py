from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from src.infrastructure.database import get_db
from src.services.ai_catalog import AISearchService, DynamicPricingService
from .schemas import ProductoCardSchema

market_router = APIRouter(prefix="/market", tags=["Marketplace Público"])

@market_router.get("/productos", response_model=List[ProductoCardSchema])
def catalogo_inteligente(
    q: str = Query(None, description="Término de búsqueda (ej: 'limpiador grasa')"),
    db: Session = Depends(get_db)
):
    """
    Endpoint híbrido: Si hay 'q', usa IA. Si no, muestra catálogo general.
    Aplica Precios Dinámicos en tiempo real.
    """
    # 1. Búsqueda (Semántica o Normal)
    ai_service = AISearchService(db)
    productos = ai_service.buscar_productos_inteligentes(query=q)
    
    # 2. Transformación con Precios Dinámicos
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