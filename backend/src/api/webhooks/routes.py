from fastapi import APIRouter, Request, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os
import json

from src.infrastructure.database import get_db
from src.infrastructure.models import ClienteModel, VentaModel

webhook_router = APIRouter(prefix="/webhooks", tags=["Integraciones Externas"])

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "nexus_token_secreto_123")

@webhook_router.get("/whatsapp")
async def verificar_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Meta llama a este endpoint para confirmar que el servidor es nuestro.
    """
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook de WhatsApp Verificado Exitosamente.")
        return int(challenge) 
    
    raise HTTPException(status_code=403, detail="Token de verificación inválido")

@webhook_router.post("/whatsapp")
async def recibir_mensaje(request: Request, db: Session = Depends(get_db)):
    """
    Aquí llegan los mensajes de los clientes en tiempo real.
    """
    try:
        data = await request.json()
        
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        if 'messages' in value:
            mensaje_info = value['messages'][0]
            
            telefono_bruto = mensaje_info['from'] 
            texto_mensaje = mensaje_info['text']['body'].strip().upper()
                        
            print(f"[WHATSAPP] Mensaje de {telefono_bruto}: {texto_mensaje}")
            
            if "CONFIRMAR" in texto_mensaje or "ACEPTO" in texto_mensaje:
                await procesar_confirmacion(telefono_bruto, db)
                
    except KeyError:
        pass
    except Exception as e:
        print(f"Error procesando webhook: {e}")

    return {"status": "ok"}

async def procesar_confirmacion(telefono: str, db: Session):
    """
    Busca al cliente por teléfono y confirma su última venta pendiente.
    """
    cliente = db.query(ClienteModel).filter(ClienteModel.telefono_whatsapp == telefono).first()
    
    if not cliente:
        print(f"Teléfono {telefono} no registrado en nuestra BD.")
        return

    venta = db.query(VentaModel).filter(
        VentaModel.cliente_id == cliente.id,
        VentaModel.estado == "PENDIENTE_PAGO"
    ).order_by(desc(VentaModel.fecha)).first()
    
    if venta:
        venta.estado = "CONFIRMADO_POR_WHATSAPP"
        db.commit()
        print(f"✅ Venta {venta.id} actualizada a CONFIRMADO (Vía WhatsApp).")
        
    else:
        print("ℹ️ El cliente no tiene ventas pendientes por confirmar.")