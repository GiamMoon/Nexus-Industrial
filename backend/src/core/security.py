from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("SECRET_KEY", "CLAVE_ULTRA_SECRETA_JHIRE")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña ingresada coincide con el hash en BD."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Transforma '123456' en '$2b$12$...' irrreversible."""
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], user_type: str, role: str = None) -> str:
    """
    Genera el JWT.
    
    Payload:
    - sub: ID del usuario
    - type: 'employee' o 'client' (CRÍTICO PARA SEGURIDAD)
    - role: 'admin', 'vendedor', 'cliente_vip'
    - exp: Expiración
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "type": user_type,
        "role": role,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt