import os
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Transaccion, Cuenta, Categoria, TipoTransaccion, MetodoPago

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finanzas.db")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def inicializar_bd():
    init_db()

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def guardar_transaccion(data):
    db = SessionLocal()
    try:
        nueva = Transaccion(
            amount=getattr(data, 'amount', data.get('amount') if isinstance(data, dict) else 0.0),
            currency=getattr(data, 'currency', data.get('currency', 'PEN') if isinstance(data, dict) else 'PEN'),
            category=getattr(data, 'category', data.get('category', 'Otros') if isinstance(data, dict) else 'Otros'),
            transaction_type=getattr(data, 'transaction_type', data.get('transaction_type', 'Gasto') if isinstance(data, dict) else 'Gasto'),
            payment_method=getattr(data, 'payment_method', data.get('payment_method', 'Efectivo') if isinstance(data, dict) else 'Efectivo'),
            description=getattr(data, 'description', data.get('description', '') if isinstance(data, dict) else '')
        )
        db.add(nueva)
        db.commit()
        db.refresh(nueva)
        return nueva
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def guardar_transaccion_segura(data):
    return guardar_transaccion(data)

# Inicializar tablas al cargar
inicializar_bd()
