from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal

# --- CLASES BASE ---
class EntidadBase:
    def __init__(self, id: Optional[UUID] = None):
        self.id = id or uuid4()
        self.fecha_creacion = datetime.now()

# --- ACTORES DEL SISTEMA (Separación Market vs Control) ---

class UsuarioEmpleado(EntidadBase):
    """Accede a NEXUS CONTROL (Admin/Vendedores)"""
    def __init__(self, nombre: str, email: str, rol: str, password_hash: str, id: UUID = None):
        super().__init__(id)
        self.nombre = nombre
        self.email = email
        self.rol = rol # 'ADMIN', 'VENDEDOR', 'ALMACEN'
        self.password_hash = password_hash

class ClienteWeb(EntidadBase):
    """Accede a NEXUS MARKET (Público)"""
    def __init__(self, ruc_dni: str, razon_social: str, email: str, password_hash: str, id: UUID = None):
        super().__init__(id)
        self.ruc_dni = ruc_dni
        self.razon_social = razon_social
        self.email = email
        self.password_hash = password_hash
        self.nivel_fidelidad = "BRONCE" # Lógica de gamificación

# --- NÚCLEO COMERCIAL ---

class Producto(EntidadBase):
    def __init__(
        self, 
        nombre: str, 
        sku: str, 
        precio_base: Decimal, 
        stock: int, 
        descripcion_tecnica: str,
        id: UUID = None
    ):
        super().__init__(id)
        self.nombre = nombre
        self.sku = sku
        self.precio_base = precio_base
        self.precio_ia = precio_base # Precio dinámico inicializado
        self.stock = stock
        self.descripcion_tecnica = descripcion_tecnica
        
        # CEREBRO IA: Aquí guardaremos el vector para búsqueda semántica
        # Se llena al procesar el PDF o descripción
        self.vector_semantico: Optional[List[float]] = None 

    def ajustar_precio_por_demanda(self, factor_demanda: float):
        """REQ-SHOP-01: Lógica de Precios Dinámicos con Guardrail"""
        nuevo_precio = self.precio_base * Decimal(factor_demanda)
        limite_inferior = self.precio_base * Decimal(0.85) # Nunca bajar más del 15%
        
        if nuevo_precio < limite_inferior:
            self.precio_ia = limite_inferior
        else:
            self.precio_ia = nuevo_precio