from pydantic import BaseModel, EmailStr
from uuid import UUID

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    role: str

class RegisterClienteSchema(BaseModel):
    ruc_dni: str
    razon_social: str
    email: EmailStr
    password: str
    telefono: str