import hashlib
import random
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from pypdf import PdfReader
from io import BytesIO
from fastapi import UploadFile

# Importamos el modelo de base de datos
from src.infrastructure.models import ProductoModel
from src.infrastructure.database import SessionLocal

class RAGService:
    def __init__(self):
        # Cada vez que instanciamos el servicio, abrimos sesión de BD
        self.db: Session = SessionLocal()

    def _get_embedding(self, texto: str) -> List[float]:
        """
        SIMULACIÓN DETERMINISTA DE EMBEDDINGS (1536 dimensiones).
        Genera siempre el mismo vector para el mismo texto, permitiendo probar
        la búsqueda semántica sin pagar API de OpenAI.
        """
        if not texto: return [0.0] * 1536
        
        # Semilla basada en el hash del texto
        seed = int(hashlib.sha256(texto.encode('utf-8')).hexdigest(), 16) % 10**8
        random.seed(seed)
        
        # Generar vector normalizado simulado
        return [random.uniform(-0.1, 0.1) for _ in range(1536)]

    async def ingestar_pdf(self, producto_id: str, archivo: UploadFile):
        """
        ETL: Extract (PDF) -> Transform (Vector) -> Load (PGVector)
        """
        try:
            # 1. Leer PDF en memoria
            content = await archivo.read()
            reader = PdfReader(BytesIO(content))
            texto_completo = ""
            for page in reader.pages:
                texto_completo += page.extract_text() + "\n"
            
            if not texto_completo.strip():
                return {"msg": "El PDF parece estar vacío o es una imagen.", "chars": 0}

            # 2. Vectorizar (Simulado)
            # Tomamos los primeros 1000 caracteres como 'contexto' principal
            vector = self._get_embedding(texto_completo[:1000])

            # 3. Guardar en PostgreSQL
            producto = self.db.query(ProductoModel).get(producto_id)
            if not producto:
                raise ValueError(f"Producto {producto_id} no encontrado")
            
            # Guardamos el texto para RAG y el vector para búsqueda
            # (Asumiendo que usamos el campo descripcion para guardar el texto del manual)
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
            print(f"❌ Error en ingesta PDF: {e}")
            return {"msg": f"Error procesando PDF: {str(e)}", "chars": 0}

    def consultar(self, pregunta: str) -> str:
        """
        Búsqueda Semántica: Encuentra el producto más relevante a la pregunta.
        """
        try:
            # 1. Convertir pregunta a vector
            pregunta_vector = self._get_embedding(pregunta)
            
            # 2. Búsqueda por Distancia Euclidiana (L2) en PGVector
            # Ordenamos por menor distancia (más similitud)
            stmt = select(ProductoModel).order_by(
                ProductoModel.embedding_vector.l2_distance(pregunta_vector)
            ).limit(1)
            
            resultado = self.db.execute(stmt).scalar_one_or_none()
            
            # 3. Generar Respuesta (Augmented Generation)
            if not resultado or not resultado.descripcion:
                return "No encontré información técnica relevante en los manuales cargados."

            # Respuesta formateada tipo Chatbot
            respuesta = (
                f"🤖 Basado en el manual de **{resultado.nombre}**:\n\n"
                f"ℹ️ {resultado.descripcion[:300]}...\n\n"
                f"💡 *Recomendación:* Este producto es el más adecuado para tu consulta técnica."
            )
            return respuesta

        except Exception as e:
            print(f"❌ Error en consulta RAG: {e}")
            return "Lo siento, tuve un error consultando la base de conocimientos."