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

    Extrae los datos y responde ÚNICAMENTE un JSON con esta estructura exacta:
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
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-pro"
    ]

    for model_name in modelos:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            texto_limpio = response.text.strip().replace("```json", "").replace("```", "").strip()
            datos = json.loads(texto_limpio)
            print(f"✅ Procesado exitosamente con {model_name}")
            return datos
        except Exception as e:
            print(f"Aviso: Falló con {model_name} ({e}), intentando siguiente modelo...")
            continue

    print("❌ No se pudo conectar con ningún modelo de Gemini disponible.")
    return None