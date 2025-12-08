import sys
import os
sys.path.append('/app') # Ruta Docker

from src.infrastructure.database import SessionLocal, engine, Base
from src.infrastructure.models import ProductoModel, ClienteModel, VentaModel, DetalleVentaModel, UsuarioModel
from src.core.security import get_password_hash
from sqlalchemy import text
import random
from datetime import datetime, timedelta

def seed_real_data():
    print("🧹 LIMPIANDO BASE DE DATOS...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    # 1. USUARIOS STAFF
    print("👤 Creando Staff...")
    admin = UsuarioModel(nombre="Admin Gerente", email="admin@nexus.com", password_hash=get_password_hash("admin123"), rol="ADMIN")
    vendedor = UsuarioModel(nombre="Juan Vendedor", email="ventas@nexus.com", password_hash=get_password_hash("ventas123"), rol="VENDEDOR")
    db.add_all([admin, vendedor])

    # 2. PRODUCTOS INDUSTRIALES (Datos Reales para Demo)
    print("📦 Creando Catálogo Industrial...")
    productos_data = [
        {"nombre": "Taladro Percutor Industrial 800W", "sku": "TOOL-001", "cat": "Herramientas", "precio": 450.00, "stock": 15, "desc": "Taladro de alto rendimiento para concreto y metal. Velocidad variable."},
        {"nombre": "Botas de Seguridad Dielectricas T42", "sku": "EPP-001", "cat": "Seguridad", "precio": 120.00, "stock": 50, "desc": "Calzado con punta de acero y suela resistente a hidrocarburos."},
        {"nombre": "Desengrasante Motor Heavy Duty 1GL", "sku": "CHEM-001", "cat": "Químicos", "precio": 85.00, "stock": 5, "desc": "Líquido concentrado para remover grasa pesada en motores diesel."},
        {"nombre": "Guantes de Nitrilo Anticorte Nivel 5", "sku": "EPP-002", "cat": "Seguridad", "precio": 25.00, "stock": 200, "desc": "Protección manual para manipulación de vidrios y metales afilados."},
        {"nombre": "Multímetro Digital True RMS", "sku": "ELEC-001", "cat": "Electrónica", "precio": 320.00, "stock": 8, "desc": "Medición precisa de voltaje, corriente y resistencia. Pantalla retroiluminada."},
        {"nombre": "Juego de Llaves Mixtas 6-32mm", "sku": "TOOL-002", "cat": "Herramientas", "precio": 280.00, "stock": 12, "desc": "Acero cromo vanadio. Estuche organizador resistente."},
        {"nombre": "Casco de Seguridad Tipo Jockey Blanco", "sku": "EPP-003", "cat": "Seguridad", "precio": 35.00, "stock": 150, "desc": "Suspensión de 4 puntos. Norma ANSI Z89.1."},
        {"nombre": "Disco de Corte para Metal 4.5 pulg", "sku": "ABR-001", "cat": "Abrasivos", "precio": 8.50, "stock": 500, "desc": "Corte rápido y preciso en acero inoxidable y fierro negro."},
        {"nombre": "Esmeril Angular 4.5 pulg 1200W", "sku": "TOOL-003", "cat": "Herramientas", "precio": 380.00, "stock": 20, "desc": "Potente motor para trabajos de desbaste y corte continuo."},
        {"nombre": "Cinta de Señalización Peligro 500m", "sku": "SIG-001", "cat": "Seguridad", "precio": 45.00, "stock": 30, "desc": "Cinta amarilla/negra de alta visibilidad para delimitar zonas."}
    ]

    prod_objs = []
    # Usamos un vector dummy [0.1, ...] para no depender de OpenAI en el seed
    dummy_vector = [0.1] * 1536 

    for p in productos_data:
        # Generar imagen placeholder bonita con el nombre
        img = f"https://via.placeholder.com/400x300/0f2027/ffffff?text={p['nombre'].replace(' ', '+')}"
        prod = ProductoModel(
            nombre=p['nombre'], sku=p['sku'], descripcion=p['desc'],
            precio_base=p['precio'], precio_dinamico=p['precio'], stock=p['stock'],
            imagen_url=img, embedding_vector=dummy_vector
        )
        prod_objs.append(prod)
        db.add(prod)
    
    db.commit()

    # 3. VENTAS HISTÓRICAS (Para las gráficas)
    print("📈 Generando Historial de Ventas...")
    clientes = [ClienteModel(ruc_dni=f"100000000{i}", razon_social=f"Empresa {i} SAC", email=f"cliente{i}@mail.com") for i in range(5)]
    db.add_all(clientes)
    db.flush()

    for _ in range(50): # 50 ventas pasadas
        fecha = datetime.now() - timedelta(days=random.randint(0, 30))
        prod = random.choice(prod_objs)
        qty = random.randint(1, 5)
        total = float(prod.precio_base) * qty
        
        venta = VentaModel(fecha=fecha, cliente_id=random.choice(clientes).id, total=total, estado="FACTURADO_SUNAT")
        db.add(venta)
        db.flush()
        
        detalle = DetalleVentaModel(venta_id=venta.id, producto_id=prod.id, cantidad=qty, precio_unitario=prod.precio_base, subtotal=total)
        db.add(detalle)

    db.commit()
    print("✅ DATOS PROFESIONALES CARGADOS.")

if __name__ == "__main__":
    seed_real_data()