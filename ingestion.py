import os
import re
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Modelo único configurado
MODELO_GEMINI = "gemini-3.6-flash"

# Mapa de categorías para detección instantánea sin gastar cuota
CATEGORIAS_MAP = {
    "Alimentación": ["comida", "almuerzo", "cena", "desayuno", "menu", "menú", "restaurante", "kfc", "bembos", "chifa", "burger", "pizza", "snack", "tacos", "pollito"],
    "Transporte": ["taxi", "uber", "pasaje", "bus", "gasolina", "combustible", "peaje", "colectivo", "viaje"],
    "Servicios": ["luz", "agua", "internet", "movistar", "claro", "entel", "luz del sur", "ensa", "enel", "sedapal", "cable"],
    "Suscripciones": ["netflix", "spotify", "chatgpt", "openai", "prime", "youtube", "disney", "apple", "icloud"],
    "Salud": ["farmacia", "medicina", "doctor", "consulta", "pastillas", "clinica", "botica", "inkafarma", "mifarma"],
    "Ocio": ["cine", "juegos", "fiesta", "tragos", "bar", "cerveza", "steam", "playstation"],
    "Hogar": ["mercado", "supermercado", "metro", "plaza vea", "tottus", "compras casa", "limpieza"]
}

def parsear_localmente(texto: str):
    """Procesa transacciones directamente en Python (0 llamadas a la API)."""
    texto_lower = texto.lower().strip()
    
    # 1. Buscar monto numérico (ej: 20, 20.50, S/ 55, 55 soles)
    match_monto = re.search(r'(?:s\/\.?\s*|\$)?(\d+(?:[\.,]\d{1,2})?)\s*(?:soles|pen|usd|dolares)?', texto_lower)
    if not match_monto:
        return None
        
    monto_str = match_monto.group(1).replace(',', '.')
    monto = float(monto_str)
    
    # 2. Identificar Ingreso o Gasto
    palabras_ingreso = ["me depositaron", "me pagaron", "deposito", "depósito", "recibi", "recibí", "ingreso", "cobro", "transferencia recibida", "sueldo"]
    es_ingreso = any(p in texto_lower for p in palabras_ingreso)
    tipo = "Ingreso" if es_ingreso else "Gasto"
    
    # 3. Identificar Categoría
    categoria = "Depósito" if es_ingreso else "Otros"
    if not es_ingreso:
        for cat, palabras in CATEGORIAS_MAP.items():
            if any(p in texto_lower for p in palabras):
                categoria = cat
                break
                
    # 4. Identificar Medio de Pago
    medio = "Efectivo"
    if "yape" in texto_lower or "yapee" in texto_lower or "yapeé" in texto_lower:
        medio = "Yape"
    elif "plin" in texto_lower:
        medio = "Plin"
    elif "bcp" in texto_lower or "transferencia" in texto_lower:
        medio = "Transferencia bancaria"
    elif "tarjeta" in texto_lower:
        medio = "Tarjeta de Débito"
        
    return {
        "intent": "registro",
        "amount": monto,
        "currency": "PEN",
        "category": categoria,
        "transaction_type": tipo,
        "payment_method": medio,
        "description": texto.strip()
    }

def obtener_cliente():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def procesar_mensaje_con_gemini(texto: str):
    texto_lower = texto.lower()
    
    # Si es una pregunta o consulta de análisis, se envía a la función de chat
    preguntas_clave = ["¿", "?", "que gaste", "qué gasté", "en que gaste", "en qué gasté", "cuanto gaste", "cuánto gasté", "cuanto tengo", "cuánto tengo", "resumen", "balance", "analisis", "análisis", "consejo"]
    if any(p in texto_lower for p in preguntas_clave):
        return {"intent": "consulta"}
    
    # Intentar registrar localmente (instantáneo y gratis)
    resultado_local = parsear_localmente(texto)
    if resultado_local and resultado_local["amount"] > 0:
        return resultado_local

    # Si es un formato no estándar, consultar a gemini-3.6-flash
    client = obtener_cliente()
    if not client:
        return {"error": "GEMINI_API_KEY no configurada"}

    prompt = f"""
    Analiza este texto financiero en Perú: "{texto}"
    Devuelve ÚNICAMENTE un JSON:
    {{
        "intent": "registro" o "consulta",
        "amount": 0.0,
        "currency": "PEN",
        "category": "Alimentación",
        "transaction_type": "Gasto" o "Ingreso",
        "payment_method": "Efectivo",
        "description": "Detalle corto"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model=MODELO_GEMINI,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        if response.text:
            texto_limpio = re.sub(r"^```(?:json)?", "", response.text.strip(), flags=re.IGNORECASE).strip()
            texto_limpio = re.sub(r"```$", "", texto_limpio).strip()
            return json.loads(texto_limpio)
    except Exception as e:
        return {"error": str(e)}

    return {"error": "No se pudo interpretar el mensaje."}

def responder_consulta_financiera(pregunta: str, transacciones: list) -> str:
    client = obtener_cliente()
    if not client:
        return "❌ Error: API Key no configurada."

    if not transacciones:
        resumen_datos = "No hay transacciones registradas este mes."
    else:
        lineas = []
        for t in transacciones:
            lineas.append(f"- {t['fecha']}: {t['tipo']} de S/ {t['monto']:.2f} en {t['categoria']} ({t['descripcion']})")
        resumen_datos = "\n".join(lineas)

    prompt = f"""
    Eres Clever, un asesor financiero personal amigable, analítico y muy conciso.
    Pregunta del usuario: "{pregunta}"

    Transacciones reales registradas en su cuenta:
    {resumen_datos}

    Instrucciones:
    - Responde de forma directa y concisa (1 a 3 líneas).
    - Incluye emojis relevantes (📊, 💰, 🍔, 🚗).
    - Calcula datos exactos de la lista (suma totales o indica la categoría con mayor gasto si te lo pide).
    """

    try:
        response = client.models.generate_content(
            model=MODELO_GEMINI,
            contents=prompt
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        return f"❌ Error al consultar asesor: {e}"

    return "❌ No se pudo procesar la respuesta."