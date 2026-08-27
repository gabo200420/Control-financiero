import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def procesar_mensaje_con_gemini(texto: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY no configurada.")
        return None

    client = genai.Client(api_key=api_key)

    prompt = f"""
    Eres un asistente contable. Analiza el siguiente texto de un gasto, ingreso o notificación bancaria en Perú:
    "{texto}"

    Devuelve ÚNICAMENTE un objeto JSON con este formato exacto:
    {{
        "amount": 0.0,
        "currency": "PEN",
        "category": "Alimentación",
        "transaction_type": "Gasto",
        "payment_method": "Yape",
        "description": "Detalle corto"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        if response.text:
            texto_limpio = response.text.strip().replace("```json", "").replace("```", "").strip()
            datos = json.loads(texto_limpio)
            
            monto_raw = str(datos.get("amount", "0"))
            monto_limpio = re.sub(r"[^\d.]", "", monto_raw)
            datos["amount"] = float(monto_limpio) if monto_limpio else 0.0
            
            print(f"✅ Transacción parseada con éxito: {datos}")
            return datos
    except Exception as e:
        print(f"❌ Error al consultar Gemini: {e}")
        return None

    return None
