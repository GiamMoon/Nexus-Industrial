from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.infrastructure.models import UsuarioModel, ClienteModel
from src.core.security import verify_password, create_access_token, get_password_hash
from .schemas import LoginSchema, TokenSchema, RegisterClienteSchema

auth_router = APIRouter(prefix="/auth", tags=["Seguridad & Acceso"])

@auth_router.post("/login/control", response_model=TokenSchema)
def login_empleado(credentials: LoginSchema, db: Session = Depends(get_db)):
    """
    Acceso exclusivo para Staff. 
    NOTA: Espera JSON Body: {"email": "...", "password": "..."}
    """
    print(f"INTENTO LOGIN CONTROL")
    print(f"📨 Recibido Email: '{credentials.email}'")
    print(f"Recibido Pass: '{credentials.password}' (Longitud: {len(credentials.password)})")

    user = db.query(UsuarioModel).filter(UsuarioModel.email == credentials.email).first()
    
    if not user:
        print(f"FALLO: Usuario '{credentials.email}' NO existe en BD.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de empleado incorrectas (Email no encontrado)"
        )
    
    es_valido = verify_password(credentials.password, user.password_hash)
    
    if not es_valido:
        print(f"FALLO: Password incorrecta para '{credentials.email}'.")
        print(f"   Hash DB: {user.password_hash[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de empleado incorrectas (Password erróneo)"
        )
    
    if not user.activo:
        print(f"FALLO: Usuario inactivo.")
        raise HTTPException(status_code=403, detail="Usuario desactivado por Admin")

    rol_token = str(user.rol).upper() if user.rol else "EMPLEADO"
    print(f"LOGIN OK. Generando token con ROL: {rol_token}")

    token = create_access_token(
        subject=str(user.id),  
        user_type="employee", 
        role=rol_token
    )
    
    return {
        "access_token": token,
        "user_name": user.nombre,
        "role": rol_token
    }

@auth_router.post("/login/market", response_model=TokenSchema)
def login_cliente(credentials: LoginSchema, db: Session = Depends(get_db)):
    """Acceso público para Compradores"""
    print(f"\n🛒 INTENTO LOGIN MARKET: {credentials.email}")
    
    client = db.query(ClienteModel).filter(ClienteModel.email == credentials.email).first()
    
    if not client:
        print("Cliente no encontrado.")
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not client.password_hash or not verify_password(credentials.password, client.password_hash):
         print("Password cliente incorrecta.")
         raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    print("LOGIN MARKET OK")
    token = create_access_token(subject=str(client.id), user_type="client", role="CUSTOMER")
    
    return {
        "access_token": token,
        "user_name": client.razon_social,
        "role": "customer"
    }

@auth_router.post("/register/market")
def registrar_cliente(data: RegisterClienteSchema, db: Session = Depends(get_db)):
    if db.query(ClienteModel).filter(ClienteModel.email == data.email).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    if db.query(ClienteModel).filter(ClienteModel.ruc_dni == data.ruc_dni).first():
        raise HTTPException(status_code=400, detail="El RUC/DNI ya está registrado")

    new_client = ClienteModel(
        ruc_dni=data.ruc_dni,
        razon_social=data.razon_social,
        email=data.email,
        telefono_whatsapp=data.telefono,
        password_hash=get_password_hash(data.password)
    )
    
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    
    return {"msg": "Cuenta creada exitosamente. Ahora inicie sesión."}