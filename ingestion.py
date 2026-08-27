import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def procesar_mensaje_con_gemini(texto: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY no encontrada en las variables de entorno.")
        return None

    genai.configure(api_key=api_key)

    prompt = f"""
    Eres un asistente contable. Analiza el siguiente texto de un gasto, ingreso o notificación bancaria en Perú (BCP, Yape, Plin, efectivo):
    "{texto}"

    Extrae la información y responde ÚNICAMENTE con un objeto JSON válido con esta estructura:
    {{
        "amount": 0.0,
        "currency": "PEN",
        "category": "Alimentación",
        "transaction_type": "Gasto",
        "payment_method": "Yape",
        "description": "Gaseosa"
    }}

    Reglas:
    - "amount": número decimal o entero (float).
    - "category": Alimentación, Transporte, Servicios, Ocio, Salud, Ropa, u Otros.
    - "transaction_type": "Gasto" o "Ingreso".
    - "payment_method": BCP, Yape, Plin, Efectivo, o Tarjeta.
    - "description": descripción breve de la transacción.
    """

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        print(f"Respuesta cruda Gemini: {response.text}")
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"❌ Error al consultar Gemini: {e}")
        return None
    