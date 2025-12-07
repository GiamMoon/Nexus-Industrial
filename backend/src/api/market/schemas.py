from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ProductoCardSchema(BaseModel):
    id: UUID
    nombre: str
    sku: str
    descripcion: str
    imagen_url: Optional[str] = "https://via.placeholder.com/300"
    
    # Precios
    precio_lista: float # Precio tachado (Base)
    precio_venta: float # Precio IA (Dinámico)
    es_oferta_ia: bool  # Para poner etiqueta "⚡ Precio Smart"
    
    stock_disponible: int
    
    class Config:
        from_attributes = True