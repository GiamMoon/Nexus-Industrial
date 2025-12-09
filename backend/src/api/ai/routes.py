from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.infrastructure.models import ProductoModel
from src.api.deps import get_current_employee
# Importamos los servicios (RAGService en mayúscula)
from src.services.rag_service import RAGService 
from src.services.agents import PurchasingAgent

ai_router = APIRouter(prefix="/ai", tags=["Inteligencia Artificial"])

@ai_router.post("/chat")
def chatear_con_manuales(
    pregunta: str = Form(...), 
    db: Session = Depends(get_db)
):
    """
    REQ-AI-01: Chatbot con Router Semántico.
    """
    try:
        pregunta_lower = pregunta.lower()
        
        intentos_compra = ["precio", "cuesta", "vale", "cuanto", "stock", "tienes"]
        
        if any(x in pregunta_lower for x in intentos_compra):
            palabras = [p for p in pregunta_lower.split() if len(p) > 3 and p not in intentos_compra]
            
            if not palabras:
                return {"respuesta": "🤖 Para darte precios, necesito saber el nombre del producto."}
            
            for palabra in palabras:
                producto = db.query(ProductoModel).filter(
                    ProductoModel.nombre.ilike(f"%{palabra}%")
                ).first()
                
                if producto:
                    stock_msg = "✅ En Stock" if producto.stock > 0 else "❌ Agotado"
                    return {
                        "respuesta": f"💰 El **{producto.nombre}** tiene un precio de **S/ {float(producto.precio_dinamico):.2f}**.\nEstado: {stock_msg} ({producto.stock} unds)."
                    }
            
            return {"respuesta": "🤖 No encontré ese producto exacto en el inventario."}

        rag = RAGService() 
        respuesta_rag = rag.consultar(pregunta)
        return {"respuesta": respuesta_rag}

    except Exception as e:
        print(f"❌ Error en Chat: {e}")
        return {"respuesta": "Lo siento, mis circuitos están en mantenimiento."}


@ai_router.post("/ingestar-pdf")
async def subir_manual(
    producto_id: str = Form(...),
    file: UploadFile = File(...),
    admin=Depends(get_current_employee)
):
    """Admin sube PDF -> Se vectoriza"""
    try:
        rag = RAGService()
        resultado = await rag.ingestar_pdf(producto_id, file)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ai_router.post("/agente-compras/{producto_id}")
def invocar_agente_compras(
    producto_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_employee)
):
    """REQ-AI-02: Análisis de stock"""
    try:
        agente = PurchasingAgent(db)
        return agente.ejecutar_analisis_stock(producto_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))