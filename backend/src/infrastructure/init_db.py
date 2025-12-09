import sys
import os

sys.path.append('/app')

from sqlalchemy import text
from src.infrastructure.database import engine, Base

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
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print(" Extensión 'vector' activada.")
        
        Base.metadata.create_all(bind=engine)
        print("Tablas creadas exitosamente.")
        
    except Exception as e:
        print(f"Error creando tablas: {e}")

if __name__ == "__main__":
    init_db()