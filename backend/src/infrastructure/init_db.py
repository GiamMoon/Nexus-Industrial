import sys
import os

# --- CORRECCIÓN DEFINITIVA DE RUTA ---
# En Docker, el código siempre está en /app. Forzamos esa ruta.
sys.path.append('/app')

from sqlalchemy import text
from src.infrastructure.database import engine, Base

# Importamos TODOS los modelos para que SQLAlchemy cree las tablas
from src.infrastructure.models import (
    UsuarioModel,
    ClienteModel,
    ProductoModel,
    VentaModel,
    DetalleVentaModel,
    RutaVendedorModel,
    AuditLog
)

def init_db():
    print("🔄 Inicializando Base de Datos Nexus...")
    try:
        with engine.connect() as conn:
            # Activar vectores para la IA
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("✅ Extensión 'vector' activada.")
        
        # Crear Tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente.")
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")

if __name__ == "__main__":
    init_db()