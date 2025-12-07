import sys
import os
# Hack para importar módulos hermanos
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.infrastructure.database import SessionLocal, engine, Base
from src.infrastructure.models import ProductoModel
from src.services.ai_catalog import AISearchService
import random

def seed_products():
    print("🌱 Sembrando Catálogo Industrial...")
    db = SessionLocal()
    ai_service = AISearchService(db)
    
    productos_dummy = [
        ("Desengrasante Motor X", "Químico fuerte para grasa mecánica", 45.00),
        ("Guantes Nitrilo Pro", "Protección química industrial caja x100", 25.50),
        ("Escobilla Acero", "Para remover óxido en maquinaria pesada", 12.00),
        ("Lentes Seguridad UV", "Policarbonato resistente a impactos", 18.00),
        ("Botas Punta Acero", "Calzado de seguridad dieléctrico", 120.00),
        ("Arnés de Altura", "Línea de vida doble gancho", 250.00),
        ("Mascarilla 3M N95", "Filtrado de partículas caja x20", 85.00),
        ("Chaleco Reflectivo", "Alta visibilidad naranja con bolsillos", 35.00),
        ("Casco Ingeniero", "Protección craneal con barbiquejo", 40.00),
        ("Alcohol Isopropílico", "Limpieza de circuitos electrónicos 1L", 22.00)
    ]

    for nombre, desc, precio in productos_dummy:
        # Generar vector simulado basado en la descripción
        vector = ai_service._generar_embedding_simulado(desc)
        
        prod = ProductoModel(
            nombre=nombre,
            sku=f"SKU-{random.randint(1000,9999)}",
            descripcion=desc,
            precio_base=precio,
            precio_dinamico=precio, # Inicial igual
            stock=random.randint(5, 100), # Random para probar precios dinámicos
            embedding_vector=vector,
            imagen_url=f"https://placehold.co/600x400?text={nombre.replace(' ', '+')}"
        )
        db.add(prod)
    
    db.commit()
    print("✅ 10 Productos con Vectores IA insertados.")
    db.close()

if __name__ == "__main__":
    seed_products()