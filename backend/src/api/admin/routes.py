from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date

from src.infrastructure.database import get_db
from src.infrastructure.models import ProductoModel, VentaModel, UsuarioModel
from src.api.deps import get_current_employee
from src.services.ai_catalog import AISearchService
from .schemas import ProductoCreateSchema, KPIDashboardSchema, StockUpdateSchema

admin_router = APIRouter(
    prefix="/admin", 
    tags=["Nexus Control (ERP)"],
    dependencies=[Depends(get_current_employee)]
)


@admin_router.get("/dashboard", response_model=KPIDashboardSchema)
def obtener_kpis_tiempo_real(db: Session = Depends(get_db)):
    """REQ-ADMIN-01: Datos para el Dashboard Vivo"""
    
    total_hoy = db.query(func.sum(VentaModel.total))\
        .filter(func.date(VentaModel.fecha) == date.today()).scalar() or 0.0
    
    bajos_stock = db.query(ProductoModel).filter(ProductoModel.stock < 10).count()
    
    avg_ticket = db.query(func.avg(VentaModel.total)).scalar() or 0.0
    
    mensaje = None
    if bajos_stock > 5:
        mensaje = "ALERTA IA: Riesgo de quiebre de stock inminente en 5 productos."

    return {
        "ventas_hoy": float(total_hoy),
        "productos_bajo_stock": bajos_stock,
        "ticket_promedio": round(float(avg_ticket), 2),
        "alerta_ia": mensaje
    }


@admin_router.post("/productos")
def crear_producto_con_ia(data: ProductoCreateSchema, db: Session = Depends(get_db)):
    if db.query(ProductoModel).filter(ProductoModel.sku == data.sku).first():
        raise HTTPException(status_code=400, detail="El SKU ya existe")

    ai_service = AISearchService(db)
    texto_para_vector = f"{data.nombre} {data.descripcion_tecnica}"
    vector = ai_service._generar_embedding_simulado(texto_para_vector)

    nuevo_prod = ProductoModel(
        nombre=data.nombre,
        sku=data.sku,
        descripcion=data.descripcion_tecnica,
        precio_base=data.precio_base,
        precio_dinamico=data.precio_base,
        stock=data.stock_inicial,
        embedding_vector=vector,
        imagen_url=data.imagen_url
    )
    
    db.add(nuevo_prod)
    db.commit()
    db.refresh(nuevo_prod)
    
    return {"msg": "Producto creado e indexado en Motor IA", "id": nuevo_prod.id}

@admin_router.patch("/inventario/{producto_id}/ajuste")
def ajustar_stock_manual(
    producto_id: str, 
    movimiento: StockUpdateSchema,
    db: Session = Depends(get_db)
):
    prod = db.query(ProductoModel).get(producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if movimiento.tipo_movimiento == "ENTRADA":
        prod.stock += movimiento.cantidad
    elif movimiento.tipo_movimiento == "SALIDA":
        if prod.stock < movimiento.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente")
        prod.stock -= movimiento.cantidad
    
    db.commit()
    return {"msg": "Stock actualizado", "nuevo_stock": prod.stock}