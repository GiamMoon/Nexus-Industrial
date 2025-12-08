from pydantic import BaseModel
from typing import Optional

class ProductoCreateSchema(BaseModel):
    nombre: str
    sku: str
    descripcion_tecnica: str # Vital para el RAG y Buscador
    precio_base: float
    stock_inicial: int
    imagen_url: Optional[str] = None

class StockUpdateSchema(BaseModel):
    cantidad: int
    tipo_movimiento: str # 'ENTRADA' o 'SALIDA'
    motivo: str = "AJUSTE_MANUAL"

class KPIDashboardSchema(BaseModel):
    ventas_hoy: float
    productos_bajo_stock: int
    ticket_promedio: float
    alerta_ia: Optional[str] = None