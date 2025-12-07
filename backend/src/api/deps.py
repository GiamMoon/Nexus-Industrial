from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.infrastructure.models import UsuarioModel, ClienteModel
from src.core.security import SECRET_KEY, ALGORITHM

# FastAPI busca el token en el Header "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/control")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decodifica el token base"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type") # 'employee' o 'client'
        
        if user_id is None or user_type is None:
            raise HTTPException(status_code=401, detail="Token inválido")
            
        return {"id": user_id, "type": user_type, "role": payload.get("role")}
        
    except JWTError:
        raise HTTPException(status_code=401, detail="No se pudieron validar las credenciales")

def get_current_employee(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """GUARDIA: Solo deja pasar si el token es de tipo EMPLEADO"""
    if current_user["type"] != "employee":
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere cuenta de empleado")
    
    user = db.query(UsuarioModel).get(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

def get_current_client(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """GUARDIA: Solo deja pasar si el token es de tipo CLIENTE"""
    if current_user["type"] != "client":
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere cuenta de cliente")
    
    client = db.query(ClienteModel).get(current_user["id"])
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client