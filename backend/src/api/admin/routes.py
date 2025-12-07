from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date

from src.infrastructure.database import get_db
from src.infrastructure.models import ProductoModel, VentaModel, UsuarioModel
from src.api.deps import get_current_employee # <--- EL GUARDIA DE SEGURIDAD
from src.services.ai_catalog import AISearchService
from .schemas import ProductoCreateSchema, KPIDashboardSchema, StockUpdateSchema

admin_router = APIRouter(
    prefix="/admin", 
    tags=["Nexus Control (ERP)"],
    dependencies=[Depends(get_current_employee)] # Protección Global para este Router
)

# --- DASHBOARD & ANALYTICS ---

@admin_router.get("/dashboard", response_model=KPIDashboardSchema)
def obtener_kpis_tiempo_real(db: Session = Depends(get_db)):
    """REQ-ADMIN-01: Datos para el Dashboard Vivo"""
    
    # 1. Ventas de Hoy
    total_hoy = db.query(func.sum(VentaModel.total))\
        .filter(func.date(VentaModel.fecha) == date.today()).scalar() or 0.0
    
    # 2. Productos Críticos (Stock < 10)
    bajos_stock = db.query(ProductoModel).filter(ProductoModel.stock < 10).count()
    
    # 3. Ticket Promedio Histórico
    avg_ticket = db.query(func.avg(VentaModel.total)).scalar() or 0.0
    
    # 4. Mensaje IA (Simulado por ahora)
    mensaje = None
    if bajos_stock > 5:
        mensaje = "⚠️ ALERTA IA: Riesgo de quiebre de stock inminente en 5 productos."

    return {
        "ventas_hoy": float(total_hoy),
        "productos_bajo_stock": bajos_stock,
        "ticket_promedio": round(float(avg_ticket), 2),
        "alerta_ia": mensaje
    }

# --- GESTIÓN DE INVENTARIO ---

@admin_router.post("/productos")
def crear_producto_con_ia(
    data: ProductoCreateSchema, 
    db: Session = Depends(get_db)
):
    """
    REQ-ADMIN-02: Crea producto y GENERA VECTOR IA automáticamente.
    """
    # 1. Validar SKU único
    if db.query(ProductoModel).filter(ProductoModel.sku == data.sku).first():
        raise HTTPException(status_code=400, detail="El SKU ya existe")

    # 2. Generar Vector Semántico (IA)
    ai_service = AISearchService(db)
    # Concatenamos nombre y descripción para mejor búsqueda
    texto_para_vector = f"{data.nombre} {data.descripcion_tecnica}"
    vector = ai_service._generar_embedding_simulado(texto_para_vector)

    # 3. Guardar en BD
    nuevo_prod = ProductoModel(
        nombre=data.nombre,
        sku=data.sku,
        descripcion=data.descripcion_tecnica,
        precio_base=data.precio_base,
        precio_dinamico=data.precio_base, # Inicial
        stock=data.stock_inicial,
        embedding_vector=vector, # <--- CEREBRO INSERTADO
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
    db: Session = Depends(get_db),
    empleado: UsuarioModel = Depends(get_current_employee)
):
    """Movimientos de Kardex Manuales"""
    prod = db.query(ProductoModel).get(producto_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if movimiento.tipo_movimiento == "ENTRADA":
        prod.stock += movimiento.cantidad
    elif movimiento.tipo_movimiento == "SALIDA":
        if prod.stock < movimiento.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente para realizar salida")
        prod.stock -= movimiento.cantidad
    
    db.commit()
    
    # Aquí podríamos registrar en una tabla 'logs_kardex' con el ID del empleado
    # print(f"Ajuste realizado por: {empleado.email}")
    
    return {"msg": "Stock actualizado", "nuevo_stock": prod.stock}