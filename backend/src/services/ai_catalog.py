import hashlib
import random
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from src.infrastructure.models import ProductoModel

class AISearchService:
    def __init__(self, db: Session):
        self.db = db

    def _generar_embedding_simulado(self, texto: str) -> List[float]:
        """
        Debe usar LA MISMA lógica que el seeder para que coincidan.
        """
        seed = int(hashlib.sha256(texto.encode('utf-8')).hexdigest(), 16) % 10**8
        random.seed(seed)
        return [random.uniform(-0.1, 0.1) for _ in range(1536)]

    def buscar_productos_inteligentes(self, query: str, limit: int = 10):
        """
        Estrategia Híbrida: SQL + Vectorial
        """
        if not query:
            return self.db.query(ProductoModel).filter(ProductoModel.stock > 0).limit(limit).all()

        vector_query = self._generar_embedding_simulado(query)
        stmt_vector = select(ProductoModel).order_by(
            ProductoModel.embedding_vector.l2_distance(vector_query)
        ).limit(limit)
        resultados_vector = self.db.execute(stmt_vector).scalars().all()

        stmt_sql = select(ProductoModel).filter(
            or_(
                ProductoModel.nombre.ilike(f"%{query}%"),
                ProductoModel.descripcion.ilike(f"%{query}%")
            )
        ).limit(limit)
        resultados_sql = self.db.execute(stmt_sql).scalars().all()

        finales = list(resultados_sql)
        ids_existentes = {p.id for p in finales}
        
        for p in resultados_vector:
            if p.id not in ids_existentes:
                finales.append(p)
        
        return finales[:limit]

class DynamicPricingService:
    @staticmethod
    def calcular_precio_final(producto: ProductoModel) -> float:
        precio_base = float(producto.precio_base)
        
        if producto.stock < 10:
            return round(precio_base * 1.10, 2) 
        elif producto.stock < 50:
            return round(precio_base * 1.05, 2)
        
        return round(precio_base, 2)