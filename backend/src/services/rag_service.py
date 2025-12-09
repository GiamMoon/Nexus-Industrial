import hashlib
import random
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from pypdf import PdfReader
from io import BytesIO
from fastapi import UploadFile

from src.infrastructure.models import ProductoModel
from src.infrastructure.database import SessionLocal

class RAGService:
    def __init__(self):
        self.db: Session = SessionLocal()

    def _get_embedding(self, texto: str) -> List[float]:
        """
        SIMULACIÓN DETERMINISTA DE EMBEDDINGS (1536 dimensiones).
        Genera siempre el mismo vector para el mismo texto, permitiendo probar
        la búsqueda semántica sin pagar API de OpenAI.
        """
        if not texto: return [0.0] * 1536
        
        seed = int(hashlib.sha256(texto.encode('utf-8')).hexdigest(), 16) % 10**8
        random.seed(seed)
        
        return [random.uniform(-0.1, 0.1) for _ in range(1536)]

    async def ingestar_pdf(self, producto_id: str, archivo: UploadFile):
        """
        ETL: Extract (PDF) -> Transform (Vector) -> Load (PGVector)
        """
        try:
            content = await archivo.read()
            reader = PdfReader(BytesIO(content))
            texto_completo = ""
            for page in reader.pages:
                texto_completo += page.extract_text() + "\n"
            
            if not texto_completo.strip():
                return {"msg": "El PDF parece estar vacío o es una imagen.", "chars": 0}

            vector = self._get_embedding(texto_completo[:1000])

            producto = self.db.query(ProductoModel).get(producto_id)
            if not producto:
                raise ValueError(f"Producto {producto_id} no encontrado")
            
            producto.descripcion = f"[MANUAL TÉCNICO]\n{texto_completo[:2000]}..." 
            producto.embedding_vector = vector
            
            self.db.commit()
            
            return {
                "msg": "Manual procesado y vectorizado correctamente", 
                "chars": len(texto_completo),
                "producto": producto.nombre
            }
            
        except Exception as e:
            self.db.rollback()
            print(f" Error en ingesta PDF: {e}")
            return {"msg": f"Error procesando PDF: {str(e)}", "chars": 0}

    def consultar(self, pregunta: str) -> str:
        """
        Búsqueda Semántica: Encuentra el producto más relevante a la pregunta.
        """
        try:
            pregunta_vector = self._get_embedding(pregunta)
            
            stmt = select(ProductoModel).order_by(
                ProductoModel.embedding_vector.l2_distance(pregunta_vector)
            ).limit(1)
            
            resultado = self.db.execute(stmt).scalar_one_or_none()
            
            if not resultado or not resultado.descripcion:
                return "No encontré información técnica relevante en los manuales cargados."

            respuesta = (
                f"Basado en el manual de **{resultado.nombre}**:\n\n"
                f"ℹ{resultado.descripcion[:300]}...\n\n"
                f"*Recomendación:* Este producto es el más adecuado para tu consulta técnica."
            )
            return respuesta

        except Exception as e:
            print(f"Error en consulta RAG: {e}")
            return "Lo siento, tuve un error consultando la base de conocimientos."