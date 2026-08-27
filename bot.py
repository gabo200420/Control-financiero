import os
import asyncio
from datetime import datetime
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from database import SessionLocal
from models import Transaccion
from ingestion import procesar_mensaje_con_gemini, responder_consulta_financiera

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saludo = (
        "👋 **¡Hola! Soy Clever, tu asesor financiero personal.**\n\n"
        "Puedes usarme de dos formas:\n"
        "1. **Registrar movimientos:** Escríbeme algo como _'Gasté 20 soles en taxi'_ o _'Me pagaron 50 soles'_.\n"
        "2. **Hacerme preguntas:** Pregúntame cosas como _'¿En qué gasté más este mes?'_, _'¿Cuánto he gastado?'_ o _'Dame un resumen'_."
    )
    await update.message.reply_text(saludo, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text
    if not texto_usuario:
        return
        
    await update.message.reply_chat_action("typing")
    
    try:
        analisis = procesar_mensaje_con_gemini(texto_usuario)
        
        if not analisis:
            await update.message.reply_text("❌ No pude conectar con el servicio de IA.")
            return

        # CASO 1: EL USUARIO HACE UNA PREGUNTA SOBRE SUS GASTOS
        if analisis.get("intent") == "consulta":
            db = SessionLocal()
            try:
                # Obtener las transacciones del mes en curso
                ahora = datetime.now()
                registros = db.query(Transaccion).order_by(Transaccion.created_at.desc()).limit(50).all()
                
                lista_tx = [{
                    "fecha": r.created_at.strftime("%d/%m/%Y"),
                    "monto": float(r.amount),
                    "tipo": r.transaction_type,
                    "categoria": r.category,
                    "descripcion": r.description,
                    "medio": r.payment_method
                } for r in registros]
                
                respuesta_ia = responder_consulta_financiera(texto_usuario, lista_tx)
                await update.message.reply_text(respuesta_ia)
            finally:
                db.close()
            return

        # CASO 2: EL USUARIO ESTÁ REGISTRANDO UN GASTO O INGRESO
        if "amount" in analisis and analisis["amount"] > 0:
            db = SessionLocal()
            try:
                nueva = Transaccion(
                    amount=analisis["amount"],
                    currency=analisis.get("currency", "PEN"),
                    category=analisis.get("category", "Otros"),
                    transaction_type=analisis.get("transaction_type", "Gasto"),
                    payment_method=analisis.get("payment_method", "Efectivo"),
                    description=analisis.get("description", texto_usuario)
                )
                db.add(nueva)
                db.commit()
                db.refresh(nueva)
                
                icono = "🔴" if nueva.transaction_type == "Gasto" else "🟢"
                respuesta = (
                    f"✅ **Transacción Registrada #{nueva.id}**\n\n"
                    f"📌 **Tipo:** {icono} {nueva.transaction_type}\n"
                    f"💰 **Monto:** S/. {nueva.amount:.2f} {nueva.currency}\n"
                    f"🏷️ **Categoría:** {nueva.category}\n"
                    f"💳 **Medio:** {nueva.payment_method}\n"
                    f"📝 **Descripción:** {nueva.description}"
                )
                await update.message.reply_text(respuesta, parse_mode="Markdown")
            finally:
                db.close()
        else:
            await update.message.reply_text("❌ No detecté un monto válido para registrar.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error al procesar: {e}")

# Webhook para correos BCP/Yape y Keep-Alive
async def handle_ping(request):
    return web.Response(text="Bot activo y saludable 🚀")

async def handle_webhook_correo(request):
    try:
        data = await request.json()
        texto_correo = data.get("mensaje", "")
        if texto_correo:
            analisis = procesar_mensaje_con_gemini(texto_correo)
            if analisis and analisis.get("amount", 0) > 0:
                db = SessionLocal()
                try:
                    nueva = Transaccion(
                        amount=analisis["amount"],
                        currency=analisis.get("currency", "PEN"),
                        category=analisis.get("category", "Otros"),
                        transaction_type=analisis.get("transaction_type", "Gasto"),
                        payment_method=analisis.get("payment_method", "Yape"),
                        description=analisis.get("description", "Notificación bancaria")
                    )
                    db.add(nueva)
                    db.commit()
                    return web.json_response({"status": "ok", "id": nueva.id})
                finally:
                    db.close()
        return web.json_response({"status": "ignorado"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def main():
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN no configurado.")
        return

    # Iniciar bot de Telegram
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    print("Bot de Telegram iniciado con éxito...")

    # Iniciar servidor Web para Render
    server = web.Application()
    server.router.add_get("/", handle_ping)
    server.router.add_post("/webhook", handle_webhook_correo)
    
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Servidor web escuchando en puerto {PORT}...")

    # Mantener el proceso vivo
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())