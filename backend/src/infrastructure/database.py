import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Obtener URL desde variables de entorno (Docker)
# Formato: postgresql://usuario:password@host:port/db_name
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nexus:admin123@db:5432/nexus_db")

# Pool de conexiones optimizado para alto tráfico (Market + Control)
engine = create_engine(
    DATABASE_URL, 
    pool_size=20,       # Conexiones listas para usar
    max_overflow=10,    # Conexiones extra en picos de tráfico
    pool_pre_ping=True  # Verificar conexión antes de usar (Resiliencia)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency Injection para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()