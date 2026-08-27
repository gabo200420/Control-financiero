import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def procesar_mensaje_con_gemini(texto: str):
    prompt = f"""
    Eres un asistente contable. Analiza el siguiente texto de una transacción bancaria en Perú (BCP, Yape, Plin):
    "{texto}"

    Devuelve ÚNICAMENTE un JSON con esta estructura:
    {{
        "amount": 0.0,
        "currency": "PEN",
        "category": "Alimentación | Transporte | Servicios | Ocio | Salud | Ropa | Otros",
        "transaction_type": "Gasto | Ingreso",
        "payment_method": "BCP | Yape | Plin | Efectivo | Tarjeta",
        "description": "Breve resumen"
    }}
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        limpio = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(limpio)
    except Exception as e:
        print(f"Error procesando con Gemini: {e}")
        return None