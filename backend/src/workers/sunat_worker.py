import sys
import os
import time
import random
# Hack para importar módulos del backend
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.infrastructure.database import SessionLocal
from src.infrastructure.models import VentaModel
from src.infrastructure.adapters.queue_adapter import QueueAdapter
from src.services.sunat.ubl_generator import UBLGenerator

def procesar_facturas():
    print("👷 SUNAT WORKER INICIADO (Esperando facturas...)")
    cola = QueueAdapter()
    db = SessionLocal()

    while True:
        try:
            task = cola.obtener_tarea()
            if not task:
                continue # Loop vacío si no hay tareas

            venta_id = task["venta_id"]
            intentos = task["attempts"]

            print(f"⚙️ Procesando Venta: {venta_id} (Intento {intentos + 1})")
            
            # 1. Obtener Venta de BD
            venta = db.query(VentaModel).get(venta_id)
            if not venta:
                print("❌ Error: Venta no existe en BD.")
                continue

            # 2. Generar XML UBL
            xml_content = UBLGenerator.generar_xml_factura(venta)
            
            # 3. Simular Envío a SUNAT (Puede fallar)
            # Simulamos latencia de red y fallo aleatorio del 20%
            time.sleep(2) 
            
            if random.random() < 0.2 and intentos < 3:
                raise TimeoutError("Servidor SUNAT no responde")

            # 4. ÉXITO
            venta.xml_generado = xml_content
            venta.cdr_sunat = f"CDR-{venta.id}-ACEPTADO"
            venta.estado = "FACTURADO_SUNAT"
            venta.hash_firma = "JKS78-SDF89-SDF78 (Firma Digital Simulada)"
            
            db.commit()
            print(f"✅ [SUNAT] Factura Aceptada. CDR Generado.")

        except TimeoutError:
            print(f"⚠️ [RETRY] Fallo de conexión. Re-encolando...")
            # Volvemos a encolar con contador de intentos incrementado
            if task["attempts"] < 5:
                task["attempts"] += 1
                # En un sistema real, usaríamos un delay (zadd en Redis)
                cola.encolar_factura(venta_id) 
            else:
                print("💀 [DEAD LETTER] Máximos intentos alcanzados. Alerta al Admin.")
        
        except Exception as e:
            print(f"❌ Error crítico en worker: {e}")
            if 'db' in locals(): db.rollback()

if __name__ == "__main__":
    procesar_facturas()