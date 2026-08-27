import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def obtener_cliente():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY no configurada.")
        return None
    return genai.Client(api_key=api_key)

def procesar_mensaje_con_gemini(texto: str):
    client = obtener_cliente()
    if not client:
        return None

    prompt = f"""
    Eres un asistente de finanzas personales. Analiza el siguiente texto de un usuario en Perú:
    "{texto}"

    Determina si el usuario está INTENTANDO REGISTRAR un movimiento o HACIENDO UNA PREGUNTA / CONSULTA de sus finanzas.

    Devuelve ÚNICAMENTE un JSON con esta estructura:
    {{
        "intent": "registro" o "consulta",
        "amount": 0.0,
        "currency": "PEN",
        "category": "Alimentación",
        "transaction_type": "Gasto" o "Ingreso",
        "payment_method": "Yape",
        "description": "Detalle corto"
    }}

    Reglas:
    - Si el texto es una pregunta o consulta (ej: "¿cuánto gasté?", "¿en qué gasté más?", "dame un balance", "resumen"), pon "intent": "consulta".
    - Si es un registro de gasto o ingreso (ej: "gasté 20 soles en comida", "me depositaron 50"), pon "intent": "registro".
    - Si es "registro", extrae amount (número float positivo), currency ("PEN" o "USD"), category, transaction_type ("Gasto" o "Ingreso"), payment_method y description.
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
            texto_limpio = response.text.strip()
            texto_limpio = re.sub(r"^```(?:json)?", "", texto_limpio, flags=re.IGNORECASE).strip()
            texto_limpio = re.sub(r"```$", "", texto_limpio).strip()
            
            datos = json.loads(texto_limpio)
            
            # Si es consulta, retornamos directo
            if datos.get("intent") == "consulta":
                return datos
            
            # Si es registro, normalizamos el monto
            monto_raw = str(datos.get("amount", "0"))
            monto_limpio = re.sub(r"[^\d.]", "", monto_raw)
            datos["amount"] = float(monto_limpio) if monto_limpio else 0.0
            
            if not datos.get("transaction_type"):
                datos["transaction_type"] = "Ingreso" if any(w in texto.lower() for w in ["depósito", "depositaron", "pagaron", "recibí", "ingreso"]) else "Gasto"
            if not datos.get("category"):
                datos["category"] = "Depósito" if datos["transaction_type"] == "Ingreso" else "Otros"
            if not datos.get("currency"):
                datos["currency"] = "PEN"
            if not datos.get("payment_method"):
                datos["payment_method"] = "Efectivo"
            if not datos.get("description"):
                datos["description"] = texto
                
            return datos
    except Exception as e:
        print(f"❌ Error en procesar_mensaje_con_gemini: {e}")
        return None

    return None

def responder_consulta_financiera(pregunta: str, transacciones: list) -> str:
    client = obtener_cliente()
    if not client:
        return "❌ Error: API Key no disponible."

    if not transacciones:
        resumen_datos = "No hay transacciones registradas todavía en el periodo actual."
    else:
        lineas = []
        for t in transacciones:
            lineas.append(f"- {t['fecha']}: {t['tipo']} de S/ {t['monto']:.2f} en {t['categoria']} ({t['descripcion']}) via {t['medio']}")
        resumen_datos = "\n".join(lineas)

    prompt = f"""
    Eres Clever, un asesor financiero personal amigable, inteligente y conciso.
    El usuario te está haciendo una pregunta sobre sus finanzas:
    "{pregunta}"

    Aquí tienes la lista real de transacciones de su base de datos este mes:
    {resumen_datos}

    Instrucciones de respuesta:
    1. Responde directamente a la pregunta con datos exactos calculados a partir de las transacciones.
    2. Usa emojis relevantes (🍔, 🚗, 💡, 💰, 📊).
    3. Si pregunta en qué gastó más, indica el monto y porcentaje.
    4. Sé muy conciso (máximo 2 a 3 oraciones cortas), amigable y profesional.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return response.text.strip() if response.text else "No pude procesar la consulta."
    except Exception as e:
        return f"❌ Error al consultar a tu asesor: {e}"