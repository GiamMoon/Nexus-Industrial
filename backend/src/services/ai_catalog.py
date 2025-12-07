import math
import random
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.infrastructure.models import ProductoModel

class AISearchService:
    def __init__(self, db: Session):
        self.db = db

    def _generar_embedding_simulado(self, texto: str) -> List[float]:
        """
        MOCKUP DE OPENAI ($0 Costo para Desarrollo):
        En producción, aquí llamas a `client.embeddings.create(input=texto, model="text-embedding-ada-002")`.
        
        Para desarrollo, generamos un vector determinista basado en el hash del texto.
        Esto permite probar el flujo sin pagar API Keys todavía.
        """
        random.seed(texto) # Semilla fija para que la misma busqueda de el mismo vector
        # Generamos 1536 dimensiones (estándar OpenAI)
        return [random.uniform(-0.1, 0.1) for _ in range(1536)]

    def buscar_productos_inteligentes(self, query: str, limite: int = 10):
        """
        REQ-SHOP-01: Buscador Semántico.
        Utiliza el operador de distancia L2 (<->) de pgvector.
        """
        if not query:
            # Si no hay búsqueda, devolver los más nuevos
            return self.db.query(ProductoModel).filter(ProductoModel.stock > 0).limit(limite).all()

        # 1. Convertir texto del usuario a Vector
        query_vector = self._generar_embedding_simulado(query)

        # 2. Consulta SQL Vectorial (La magia de pgvector)
        # Ordenamos por los que tengan menor distancia (más similitud)
        stmt = select(ProductoModel).order_by(
            ProductoModel.embedding_vector.l2_distance(query_vector)
        ).limit(limite)
        
        resultados = self.db.scalars(stmt).all()
        return resultados

class DynamicPricingService:
    """
    REQ-SHOP-01: Algoritmo de Precios Dinámicos.
    """
    @staticmethod
    def calcular_precio_final(producto: ProductoModel) -> float:
        precio_base = float(producto.precio_base)
        stock = producto.stock
        
        # FACTOR DE ESCASEZ
        # Si stock < 10, subimos precio un 10% (High Demand Logic)
        if stock < 10:
            factor = 1.10
        elif stock < 50:
            factor = 1.05
        else:
            factor = 1.00 # Precio normal
            
        precio_final = round(precio_base * factor, 2)
        
        # GUARDRAIL: Actualizamos el modelo (en memoria para mostrar, no persistimos para no inflar BD)
        producto.precio_dinamico = precio_final
        return precio_final