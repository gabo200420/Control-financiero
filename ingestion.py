import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def procesar_mensaje_con_gemini(texto: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY no encontrada.")
        return None

    client = genai.Client(api_key=api_key)

    prompt = f"""
    Eres un asistente contable. Analiza el siguiente texto de un gasto, ingreso o notificación bancaria en Perú:
    "{texto}"

    Devuelve ÚNICAMENTE un objeto JSON con este formato:
    {{
        "amount": 0.0,
        "currency": "PEN",
        "category": "Alimentación | Transporte | Servicios | Ocio | Salud | Ropa | Otros",
        "transaction_type": "Gasto | Ingreso",
        "payment_method": "BCP | Yape | Plin | Efectivo | Tarjeta",
        "description": "Breve resumen"
    }}
    """

    modelos = [
        "gemini-3.6-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash"
    ]

    for m in modelos:
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            if response.text:
                texto_limpio = response.text.strip().replace("```json", "").replace("```", "").strip()
                datos = json.loads(texto_limpio)
                print(f"✅ Transacción procesada con {m}: {datos}")
                return datos
        except Exception as e:
            print(f"Aviso: Falló con {m} ({e}), probando siguiente...")
            continue

    print("❌ No se pudo conectar con los modelos de Gemini.")
    return None