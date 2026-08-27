import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Modelo oficial con alta cuota diaria gratuita
MODELO_GEMINI = "gemini-2.5-flash"

def obtener_cliente():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY no configurada.")
        return None
    return genai.Client(api_key=api_key)

def procesar_mensaje_con_gemini(texto: str):
    client = obtener_cliente()
    if not client:
        return {"error": "GEMINI_API_KEY no configurada"}

    prompt = f"""
    Eres un asistente de finanzas personales para Perú.
    El usuario envió el siguiente texto: "{texto}"

    Determina si el usuario:
    1. Quiere hacer una CONSULTA o pregunta ("intent": "consulta") como "¿cuánto gasté?", "¿en qué gasté más?", "resumen", "dame mi balance", etc.
    2. Quiere REGISTRAR un movimiento ("intent": "registro") como "gasté 20 soles en comida", "yapeé 15", "me pagaron 80".

    Devuelve ÚNICAMENTE un JSON con esta estructura exacta:
    {{
        "intent": "registro",
        "amount": 0.0,
        "currency": "PEN",
        "category": "Alimentación",
        "transaction_type": "Gasto",
        "payment_method": "Yape",
        "description": "Detalle corto"
    }}

    Reglas:
    - Si es "consulta", asigna "intent": "consulta".
    - Si es "registro", asigna "intent": "registro", amount (número float positivo), currency ("PEN" o "USD"), category, transaction_type ("Gasto" o "Ingreso"), payment_method y description.
    """

    try:
        response = client.models.generate_content(
            model=MODELO_GEMINI,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        texto_resp = response.text or ""
        texto_resp = re.sub(r"^```(?:json)?", "", texto_resp.strip(), flags=re.IGNORECASE).strip()
        texto_resp = re.sub(r"```$", "", texto_resp).strip()
        
        datos = json.loads(texto_resp)
        
        if datos.get("intent") == "consulta":
            return datos
            
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
        return {"error": str(e)}

def responder_consulta_financiera(pregunta: str, transacciones: list) -> str:
    client = obtener_cliente()
    if not client:
        return "❌ Error: API Key no configurada."

    if not transacciones:
        resumen_datos = "No hay transacciones registradas todavía en la base de datos."
    else:
        lineas = []
        for t in transacciones:
            lineas.append(f"- {t['fecha']}: {t['tipo']} de S/ {t['monto']:.2f} en {t['categoria']} ({t['descripcion']}) vía {t['medio']}")
        resumen_datos = "\n".join(lineas)

    prompt = f"""
    Eres Clever, un asesor financiero personal amigable, inteligente y muy conciso.
    El usuario te hace esta pregunta:
    "{pregunta}"

    Aquí tienes sus transacciones registradas:
    {resumen_datos}

    Instrucciones:
    1. Responde de forma muy concisa (1 a 3 líneas), directa y con datos exactos calculados.
    2. Usa emojis relevantes (🍔, 🚗, 💡, 💰, 📊).
    3. Si te pregunta en qué gastó más, suma los gastos por categoría e indícale cuál fue y cuánto sumó.
    """

    try:
        response = client.models.generate_content(
            model=MODELO_GEMINI,
            contents=prompt
        )
        return response.text.strip() if response.text else "No pude generar la respuesta a la consulta."
    except Exception as e:
        return f"❌ Error al consultar asesor: {e}"