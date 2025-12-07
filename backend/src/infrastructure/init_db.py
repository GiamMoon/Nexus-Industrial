from .database import engine, Base
from sqlalchemy import text

def init_db():
    print("🔄 Inicializando Base de Datos Nexus...")
    
    with engine.connect() as conn:
        # 1. Activar Extensión PGVector (Vital para la IA)
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
        print("✅ Extensión 'vector' activada.")
    
    # 2. Crear Tablas
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente.")

if __name__ == "__main__":
    init_db()