import sys
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.infrastructure.models import UsuarioModel, ClienteModel
from src.core.security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/control")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decodifica el token base"""
    try:
        print("\n" + "="*40)
        print(" DEPS: Decodificando Token...")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type") 
        user_role: str = payload.get("role")

        print(f"PAYLOAD: ID={user_id} | TIPO={user_type} | ROL_TOKEN={user_role}")
        
        if user_id is None or user_type is None:
            print("ERROR: Token incompleto (falta sub o type)")
            raise HTTPException(status_code=401, detail="Token inválido")
            
        return {"id": user_id, "type": user_type, "role": user_role}
        
    except JWTError as e:
        print(f" ERROR JWT: {str(e)}")
        raise HTTPException(status_code=401, detail="No se pudieron validar las credenciales")

def get_current_employee(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """GUARDIA: Solo deja pasar si el token es de tipo EMPLEADO y existe en BD"""
    
    print(f"GUARDIA EMPLEADO: Verificando usuario {current_user['id']}...")

    if current_user["type"] != "employee":
        print(f" RECHAZADO: El token dice type='{current_user['type']}', se esperaba 'employee'")
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere cuenta de empleado")
    
    user = db.query(UsuarioModel).get(current_user["id"])
    if not user:
        print(f"RECHAZADO: El ID {current_user['id']} no existe en la tabla 'usuarios'")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    print(f" USUARIO ENCONTRADO: Email={user.email} | ROL_DB={user.rol}")
    
    roles_permitidos = ["ADMIN", "EMPLEADO", "SUPERVISOR", "ALMACENERO"]
    
    rol_usuario = str(user.rol).upper() if user.rol else "SIN_ROL"

    if rol_usuario not in roles_permitidos:
        print(f"❌ PROHIBIDO: El rol '{rol_usuario}' no está en la lista permitida {roles_permitidos}")
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes")

    print("ACCESO CONCEDIDO")
    print("="*40 + "\n")
    return user

def get_current_client(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """GUARDIA: Solo deja pasar si el token es de tipo CLIENTE"""
    
    if current_user["type"] != "client":
        print(f"RECHAZADO CLIENTE: Token type='{current_user['type']}'")
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere cuenta de cliente")
    
    client = db.query(ClienteModel).get(current_user["id"])
    if not client:
        print(f" RECHAZADO: Cliente ID {current_user['id']} no encontrado en BD")
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return client