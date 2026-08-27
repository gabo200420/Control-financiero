from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base

# Base centralizada de SQLAlchemy
Base = declarative_base()

# Enums auxiliares
class TipoTransaccion(str, Enum):
    GASTO = "Gasto"
    INGRESO = "Ingreso"

class MetodoPago(str, Enum):
    YAPE = "Yape"
    PLIN = "Plin"
    EFECTIVO = "Efectivo"
    DEBITO = "Tarjeta de Débito"
    CREDITO = "Tarjeta de Crédito"
    TRANSFERENCIA = "Transferencia"
    OTRO = "Otro"

# Tabla principal de transacciones en SQLite
class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="PEN")
    category = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)
    payment_method = Column(String, default="Efectivo")
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Tablas auxiliares
class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)

class Cuenta(Base):
    __tablename__ = "cuentas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)

TransaccionDB = Transaccion

# Esquema para estructuración con IA
class TransactionCreate(BaseModel):
    amount: float = Field(..., description="Monto numérico")
    currency: str = Field(default="PEN", description="PEN o USD")
    category: str = Field(..., description="Alimentación, Transporte, Servicios, Entretenimiento, Compras, Salud, Educación, Ingresos, Otros")
    transaction_type: str = Field(..., description="Gasto o Ingreso")
    payment_method: str = Field(default="Efectivo", description="Medio de pago")
    description: str = Field(..., description="Resumen corto")

TransaccionCreate = TransactionCreate
