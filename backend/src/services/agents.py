from sqlalchemy.orm import Session
from src.infrastructure.models import ProductoModel
from .pdf_generator import PDFGenerator
import random

class PurchasingAgent:
    def __init__(self, db: Session):
        self.db = db

    def ejecutar_analisis_stock(self, producto_id: str):
        """
        REQ-AI-02: Agente de Reabastecimiento.
        1. Predice demanda (Regresión Lineal Simple).
        2. Compara con Stock.
        3. Si falta, compra.
        """
        producto = self.db.query(ProductoModel).get(producto_id)
        if not producto: return {"status": "error", "msg": "Producto no encontrado"}
        
        # 1. PREDICCIÓN DE DEMANDA (Algoritmo Simplificado)
        # En producción: Scikit-learn LinearRegression con histórico de ventas
        demanda_proyectada = random.randint(20, 100) # Mockup inteligente
        stock_seguridad = 10
        umbral_reorden = demanda_proyectada + stock_seguridad
        
        # 2. TOMA DE DECISIÓN
        if producto.stock < umbral_reorden:
            cantidad_a_comprar = umbral_reorden - producto.stock + 50 # Buffer
            
            # 3. ACCIÓN: Generar Orden de Compra
            pdf_path = PDFGenerator.generar_orden_compra(
                producto.nombre, 
                cantidad_a_comprar, 
                "Proveedores Globales S.A.C."
            )
            
            return {
                "decision": "COMPRAR",
                "razon": f"Stock ({producto.stock}) inferior a Demanda Proyectada ({demanda_proyectada})",
                "accion": "Orden de Compra Generada",
                "archivo": pdf_path
            }
        
        return {
            "decision": "MANTENER",
            "razon": f"Stock saludable. Cobertura para {producto.stock / (demanda_proyectada/30):.1f} días."
        }