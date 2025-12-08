import sys
import os
import random
from datetime import datetime, timedelta
from faker import Faker
from decimal import Decimal

# Configuración de rutas para importar módulos del backend
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.infrastructure.database import SessionLocal, engine, Base
from src.infrastructure.models import UsuarioModel, ClienteModel, ProductoModel, VentaModel, DetalleVentaModel
from src.core.security import get_password_hash
from src.services.ai_catalog import AISearchService

# Inicializar Faker (Datos en Español)
fake = Faker(['es_ES', 'es_MX']) # Mezcla para variedad latina

def massive_seed():
    print("🚀 INICIANDO CARGA MASIVA DE DATOS (NEXUS ENTERPRISE)...")
    db = SessionLocal()
    ai_service = AISearchService(db)

    # --- 1. EMPLEADOS (Usuarios Nexus Control) ---
    print("👤 Generando Staff...")
    roles = ['ADMIN', 'VENDEDOR', 'ALMACEN']
    usuarios = []
    # Creamos 1 Super Admin fijo
    db.add(UsuarioModel(
        nombre="Admin Nexus", 
        email="admin@nexus.com", 
        password_hash=get_password_hash("admin123"), 
        rol="ADMIN"
    ))
    # 10 Empleados random
    for _ in range(10):
        u = UsuarioModel(
            nombre=fake.name(),
            email=fake.unique.company_email(),
            password_hash=get_password_hash("123456"),
            rol=random.choice(roles),
            ultima_latitud=Decimal(random.uniform(-12.0, -12.2)), # Lima aprox
            ultima_longitud=Decimal(random.uniform(-77.0, -77.1))
        )
        usuarios.append(u)
        db.add(u)
    db.commit()

    # --- 2. CLIENTES WEB (Nexus Market) ---
    print("🌍 Generando 100 Clientes B2B...")
    clientes = []
    for _ in range(100):
        c = ClienteModel(
            ruc_dni=str(random.randint(10000000000, 20999999999)),
            razon_social=fake.company(),
            email=fake.unique.email(),
            password_hash=get_password_hash("cliente123"),
            telefono_whatsapp=f"519{random.randint(10000000, 99999999)}"
        )
        clientes.append(c)
        db.add(c)
    db.commit()

    # --- 3. CATÁLOGO INTELIGENTE (Productos + Vectores) ---
    print("📦 Generando 100 Productos Industriales con IA...")
    categorias = ["Limpieza", "Seguridad", "Maquinaria", "Herramientas", "Químicos"]
    productos = []
    
    for _ in range(100):
        cat = random.choice(categorias)
        noun = fake.word().capitalize()
        adj = fake.word()
        nombre = f"{noun} Industrial {adj} {fake.color_name()}"
        desc = fake.paragraph(nb_sentences=3)
        
        # Simulación de Embedding (Vector IA)
        vector = ai_service._generar_embedding_simulado(desc)
        
        precio = round(random.uniform(10.0, 500.0), 2)
        
        p = ProductoModel(
            sku=f"SKU-{fake.unique.ean8()}",
            nombre=nombre,
            descripcion=f"Categoría: {cat}. {desc}",
            precio_base=precio,
            precio_dinamico=precio,
            stock=random.randint(0, 200), # Algunos con 0 para probar alertas
            embedding_vector=vector,
            imagen_url=f"https://placehold.co/400x300?text={nombre.split()[0]}"
        )
        productos.append(p)
        db.add(p)
    db.commit()

    # --- 4. HISTORIAL DE VENTAS (Transacciones) ---
    print("💰 Generando 150 Ventas Históricas (Dashboard)...")
    estados = ["PAGADO", "PENDIENTE_PAGO", "FACTURADO_SUNAT", "ENVIADO"]
    
    for _ in range(150):
        # Fecha aleatoria en los últimos 30 días
        fecha_venta = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        cliente = random.choice(clientes)
        vendedor = random.choice(usuarios)
        
        # Crear Venta
        venta = VentaModel(
            fecha=fecha_venta,
            cliente_id=cliente.id,
            vendedor_id=vendedor.id,
            estado=random.choice(estados),
            total=0 # Se calcula abajo
        )
        db.add(venta)
        db.flush()
        
        # Agregar Items (1 a 5 productos por venta)
        total_venta = 0
        num_items = random.randint(1, 5)
        for _ in range(num_items):
            prod = random.choice(productos)
            qty = random.randint(1, 10)
            precio = float(prod.precio_base)
            subtotal = qty * precio
            
            detalle = DetalleVentaModel(
                venta_id=venta.id,
                producto_id=prod.id,
                cantidad=qty,
                precio_unitario=precio,
                subtotal=subtotal
            )
            total_venta += subtotal
            db.add(detalle)
        
        venta.total = total_venta
        
        # Simular datos SUNAT si está facturado
        if venta.estado == "FACTURADO_SUNAT":
            venta.xml_generado = "<xml>Simulado</xml>"
            venta.cdr_sunat = f"CDR-{venta.id}"
            venta.hash_firma = fake.sha256()

    db.commit()
    print("✅ ¡SEMBRADO MASIVO COMPLETADO EXITOSAMENTE!")
    print(f"   - 11 Empleados")
    print(f"   - 100 Clientes")
    print(f"   - 100 Productos Vectorizados")
    print(f"   - 150 Ventas Transaccionales")

if __name__ == "__main__":
    massive_seed()