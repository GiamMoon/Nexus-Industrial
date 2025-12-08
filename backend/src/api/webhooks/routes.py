from fastapi import APIRouter, Request, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os
import json

from src.infrastructure.database import get_db
from src.infrastructure.models import ClienteModel, VentaModel

webhook_router = APIRouter(prefix="/webhooks", tags=["Integraciones Externas"])

# TOKEN DE VERIFICACIÓN (Lo configuras en el panel de Facebook Developers)
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "nexus_token_secreto_123")

# --- 1. VERIFICACIÓN (Requerido por Meta) ---
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
        print("✅ Webhook de WhatsApp Verificado Exitosamente.")
        return int(challenge) # Se debe retornar el challenge en texto plano/int
    
    raise HTTPException(status_code=403, detail="Token de verificación inválido")

# --- 2. RECEPCIÓN DE MENSAJES (El Evento) ---
@webhook_router.post("/whatsapp")
async def recibir_mensaje(request: Request, db: Session = Depends(get_db)):
    """
    Aquí llegan los mensajes de los clientes en tiempo real.
    """
    try:
        data = await request.json()
        
        # Estructura compleja de Meta: entry -> changes -> value -> messages
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        if 'messages' in value:
            mensaje_info = value['messages'][0]
            
            # 1. Extraer Datos Clave
            telefono_bruto = mensaje_info['from'] # Ej: 51999888777
            texto_mensaje = mensaje_info['text']['body'].strip().upper()
            
            # Limpiar teléfono (quitar código de país si es necesario, simple para el ejemplo)
            # Asumimos que guardamos el telefono en BD tal cual llega de WhatsApp
            
            print(f"📩 [WHATSAPP] Mensaje de {telefono_bruto}: {texto_mensaje}")
            
            # 2. Lógica de Negocio: CONFIRMACIÓN DE PEDIDO
            if "CONFIRMAR" in texto_mensaje or "ACEPTO" in texto_mensaje:
                await procesar_confirmacion(telefono_bruto, db)
                
    except KeyError:
        # Pings de estado (sent, delivered, read) que no son mensajes de texto
        pass
    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")

    # Siempre responder 200 OK a Meta, o te bloquearán el webhook
    return {"status": "ok"}

async def procesar_confirmacion(telefono: str, db: Session):
    """
    Busca al cliente por teléfono y confirma su última venta pendiente.
    """
    # 1. Buscar Cliente
    cliente = db.query(ClienteModel).filter(ClienteModel.telefono_whatsapp == telefono).first()
    
    if not cliente:
        print(f"⚠️ Teléfono {telefono} no registrado en nuestra BD.")
        return

    # 2. Buscar última venta pendiente
    venta = db.query(VentaModel).filter(
        VentaModel.cliente_id == cliente.id,
        VentaModel.estado == "PENDIENTE_PAGO" # O el estado que definimos antes
    ).order_by(desc(VentaModel.fecha)).first()
    
    if venta:
        venta.estado = "CONFIRMADO_POR_WHATSAPP"
        db.commit()
        print(f"✅ Venta {venta.id} actualizada a CONFIRMADO (Vía WhatsApp).")
        
        # AQUÍ DISPARARÍAMOS EL ENVÍO DEL PDF DE RESPUESTA
        # (Omitido para no complicar con credenciales de envío de Meta API)
    else:
        print("ℹ️ El cliente no tiene ventas pendientes por confirmar.")