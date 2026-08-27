import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from models import TransactionCreate

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT_SISTEMA = """
Eres un asistente financiero experto en clasificar transacciones en Perú.
Extrae los siguientes datos en JSON estructurado:

- amount: float (monto numérico positivo)
- currency: str ("PEN" o "USD", por defecto "PEN")
- category: str (Alimentación, Transporte, Servicios, Entretenimiento, Compras, Salud, Educación, Ingresos, Otros)
- transaction_type: str ("Gasto" o "Ingreso")
- payment_method: str ("Yape", "Plin", "Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia", "Otro")
- description: str (resumen corto)

Reglas:
- Si no se especifica medio de pago, infiere el más probable o pon "Efectivo".
- Si no se especifica moneda, usa "PEN".
"""

def parse_transaction(text: str) -> TransactionCreate:
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"{PROMPT_SISTEMA}\n\nMensaje: {text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TransactionCreate,
            temperature=0.1
        )
    )
    data = json.loads(response.text)
    return TransactionCreate(**data)

def transcribe_and_parse_audio(file_path: str) -> TransactionCreate:
    audio_file = client.files.upload(file=file_path)
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            PROMPT_SISTEMA,
            "Analiza el audio y extrae la transacción financiera:",
            audio_file
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TransactionCreate,
            temperature=0.1
        )
    )
    data = json.loads(response.text)
    return TransactionCreate(**data)

def extraer_transaccion_desde_texto(text: str) -> TransactionCreate:
    return parse_transaction(text)

def extraer_transaccion_desde_audio(file_path: str) -> TransactionCreate:
    return transcribe_and_parse_audio(file_path)
    