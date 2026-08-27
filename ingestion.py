import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def procesar_mensaje_con_gemini(texto: str):
    """
    Analiza un texto o correo y devuelve un diccionario con los datos estructurados.
    """
    prompt = f"""
    Eres un asistente contable. Analiza el siguiente texto de una transacción bancaria o mensaje de gasto/ingreso en Perú (BCP, Yape, Plin, efectivo):
    "{texto}"

    Extrae la información y responde ÚNICAMENTE con un objeto JSON válido con esta estructura exacta:
    {{
        "amount": 0.0,
        "currency": "PEN",
        "category": "Alimentación | Transporte | Servicios | Ocio | Salud | Ropa | Otros",
        "transaction_type": "Gasto | Ingreso",
        "payment_method": "BCP | Yape | Plin | Efectivo | Tarjeta",
        "description": "Breve resumen de la transacción o comercio"
    }}

    Reglas:
    - "amount" debe ser un número decimal (float).
    - Si te transfirieron o te yapearon, "transaction_type" es "Ingreso". Si pagaste, compraste o enviaste dinero, es "Gasto".
    - Responde únicamente el bloque JSON, sin texto adicional ni comillas de markdown como ```json.
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        limpio = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(limpio)
    except Exception as e:
        print(f"Error procesando con Gemini: {e}")
        return None