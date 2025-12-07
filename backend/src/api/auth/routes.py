from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.infrastructure.models import UsuarioModel, ClienteModel
from src.core.security import verify_password, create_access_token, get_password_hash
from .schemas import LoginSchema, TokenSchema, RegisterClienteSchema

auth_router = APIRouter(prefix="/auth", tags=["Seguridad & Acceso"])

# --- 1. LOGIN EMPLEADOS (Nexus Control) ---
@auth_router.post("/login/control", response_model=TokenSchema)
def login_empleado(credentials: LoginSchema, db: Session = Depends(get_db)):
    """Acceso exclusivo para Staff (Admins, Vendedores, Almacén)"""
    user = db.query(UsuarioModel).filter(UsuarioModel.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de empleado incorrectas"
        )
    
    if not user.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado por Admin")

    token = create_access_token(subject=user.id, user_type="employee", role=user.rol)
    
    return {
        "access_token": token,
        "user_name": user.nombre,
        "role": user.rol
    }

# --- 2. LOGIN CLIENTES (Nexus Market) ---
@auth_router.post("/login/market", response_model=TokenSchema)
def login_cliente(credentials: LoginSchema, db: Session = Depends(get_db)):
    """Acceso público para Compradores"""
    client = db.query(ClienteModel).filter(ClienteModel.email == credentials.email).first()
    
    if not client:
        # Por seguridad, no decimos si el email existe o no, solo "credenciales inválidas"
        # Pero para desarrollo, seremos explícitos.
        raise HTTPException(status_code=401, detail="Cliente no registrado")

    # Si es un cliente migrado sin password (caso hipotético), requeriría reset.
    if not client.password_hash or not verify_password(credentials.password, client.password_hash):
         raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    token = create_access_token(subject=client.id, user_type="client", role="customer")
    
    return {
        "access_token": token,
        "user_name": client.razon_social,
        "role": "customer"
    }

# --- 3. REGISTRO PÚBLICO (Nexus Market) ---
@auth_router.post("/register/market")
def registrar_cliente(data: RegisterClienteSchema, db: Session = Depends(get_db)):
    """Self-service: El cliente se crea su propia cuenta"""
    # Validar duplicados
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