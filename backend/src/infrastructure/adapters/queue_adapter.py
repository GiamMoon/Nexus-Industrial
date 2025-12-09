import redis
import json
import os

class QueueAdapter:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=6379,
            db=0,
            decode_responses=True
        )
        self.QUEUE_NAME = "sunat_invoices_queue"

    def encolar_factura(self, venta_id: str):
        """Producer: Agrega una tarea a la cola"""
        payload = json.dumps({"venta_id": str(venta_id), "attempts": 0})
        self.client.rpush(self.QUEUE_NAME, payload)
        print(f"📥 [REDIS] Factura {venta_id} encolada para procesamiento.")

    def obtener_tarea(self):
        """Consumer: Saca una tarea de la cola (Bloqueante)"""
        tarea = self.client.blpop(self.QUEUE_NAME, timeout=5)
        if tarea:
            return json.loads(tarea[1])
        return None