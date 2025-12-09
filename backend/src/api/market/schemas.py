from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ProductoCardSchema(BaseModel):
    id: UUID
    nombre: str
    sku: str
    descripcion: str
    imagen_url: Optional[str] = "https://via.placeholder.com/300"
    
    precio_lista: float
    precio_venta: float 
    es_oferta_ia: bool 
    
    stock_disponible: int
    
    class Config:
        from_attributes = True