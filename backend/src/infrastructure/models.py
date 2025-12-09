from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

from .database import Base


class UsuarioModel(Base):
    """Tablpython -m http.server 3000a para empleados (Nexus Control)"""
    __tablename__ = "usuarios_empleados"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nombre = Column(String)
    rol = Column(String, default="VENDEDOR") 
    activo = Column(Boolean, default=True)
    
    ultima_latitud = Column(Numeric(20, 15), nullable=True)
    ultima_longitud = Column(Numeric(20, 15), nullable=True)
    ultima_actualizacion_gps = Column(DateTime, nullable=True)

class ClienteModel(Base):
    """Tabla para compradores (Nexus Market)"""
    __tablename__ = "clientes_web"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ruc_dni = Column(String(20), unique=True, index=True, nullable=False)
    razon_social = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    telefono_whatsapp = Column(String, nullable=True)
    
    ventas = relationship("VentaModel", back_populates="cliente")


class ProductoModel(Base):
    __tablename__ = "productos"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String, unique=True, index=True)
    nombre = Column(String, index=True)
    descripcion = Column(Text)
    
    embedding_vector = Column(Vector(1536)) 
    
    precio_base = Column(Numeric(10, 2))
    precio_dinamico = Column(Numeric(10, 2))
    stock = Column(Integer, default=0)
    imagen_url = Column(String, nullable=True)

class VentaModel(Base):
    __tablename__ = "ventas"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fecha = Column(DateTime, default=datetime.utcnow)
    
    cliente_id = Column(PG_UUID(as_uuid=True), ForeignKey("clientes_web.id"), nullable=True)
    vendedor_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios_empleados.id"), nullable=True)
    
    cliente = relationship("ClienteModel", back_populates="ventas")
    
    estado = Column(String, default="PENDIENTE_PAGO")
    total = Column(Numeric(10, 2), default=0.0)
    
    xml_generado = Column(Text, nullable=True)
    cdr_sunat = Column(Text, nullable=True)
    hash_firma = Column(String, nullable=True)

class DetalleVentaModel(Base):
    __tablename__ = "detalle_ventas"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venta_id = Column(PG_UUID(as_uuid=True), ForeignKey("ventas.id"))
    producto_id = Column(PG_UUID(as_uuid=True), ForeignKey("productos.id"))
    
    cantidad = Column(Integer)
    precio_unitario = Column(Numeric(10, 2))
    subtotal = Column(Numeric(10, 2))


class RutaVendedorModel(Base):
    __tablename__ = "rutas_vendedores"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(PG_UUID(as_uuid=True), ForeignKey("usuarios_empleados.id"))
    latitud = Column(Numeric(20, 15))
    longitud = Column(Numeric(20, 15))
    actividad = Column(String, default="EN_RUTA")
    timestamp = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "logs_auditoria"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(PG_UUID(as_uuid=True), nullable=True)
    accion = Column(String)
    detalles = Column(Text, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)