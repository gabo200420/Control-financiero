# --- Tus imports existentes ---
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
# (el resto de tus imports...)

# --- BLOQUE NUEVO (Pégalo aquí) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# Iniciar servidor web en segundo plano
threading.Thread(target=run_health_check_server, daemon=True).start()

# --- AQUÍ CONTINÚA TODO TU CÓDIGO ANTERIOR DEL BOT ---
import os
import tempfile
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from ingestion import extraer_transaccion_desde_texto, extraer_transaccion_desde_audio
from database import guardar_transaccion_segura

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy tu asistente financiero.\n\n"
        "Puedes registrar gastos o ingresos enviándome:\n"
        "• Un mensaje de texto (ej: 'Gasté 35 soles en almuerzo con Yape')\n"
        "• Un mensaje de voz o audio explicando el movimiento.\n\n"
        "¡Pruébalo ahora!"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        tx_data = extraer_transaccion_desde_texto(user_text)
        tx = guardar_transaccion_segura(tx_data)
        
        simbolo = "S/." if tx.currency == "PEN" else "$"
        emoji_tipo = "🔴 Gasto" if tx.transaction_type == "Gasto" else "🟢 Ingreso"
        
        mensaje = (
            f"✅ *Transacción Registrada #{tx.id}*\n\n"
            f"📌 *Tipo:* {emoji_tipo}\n"
            f"💰 *Monto:* {simbolo} {tx.amount:.2f} {tx.currency}\n"
            f"🏷️ *Categoría:* {tx.category}\n"
            f"💳 *Medio:* {tx.payment_method}\n"
            f"📝 *Descripción:* {tx.description}"
        )
        await update.message.reply_text(mensaje, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error procesando texto: {e}")
        await update.message.reply_text(f"❌ Ocurrió un error al procesar tu mensaje: {str(e)}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        voice = update.message.voice or update.message.audio
        voice_file = await context.bot.get_file(voice.file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
            temp_path = temp_audio.name
            
        await voice_file.download_to_drive(custom_path=temp_path)
        
        tx_data = extraer_transaccion_desde_audio(temp_path)
        tx = guardar_transaccion_segura(tx_data)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        simbolo = "S/." if tx.currency == "PEN" else "$"
        emoji_tipo = "🔴 Gasto" if tx.transaction_type == "Gasto" else "🟢 Ingreso"
        
        mensaje = (
            f"🎙️ *Audio Procesado y Registrado #{tx.id}*\n\n"
            f"📌 *Tipo:* {emoji_tipo}\n"
            f"💰 *Monto:* {simbolo} {tx.amount:.2f} {tx.currency}\n"
            f"🏷️ *Categoría:* {tx.category}\n"
            f"💳 *Medio:* {tx.payment_method}\n"
            f"📝 *Descripción:* {tx.description}"
        )
        await update.message.reply_text(mensaje, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error procesando audio: {e}")
        await update.message.reply_text(f"❌ Ocurrió un error al procesar el audio: {str(e)}")

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("No se encontró TELEGRAM_BOT_TOKEN en el archivo .env")
        
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    
    print("🤖 Bot de finanzas iniciado y listo para recibir mensajes...")
    app.run_polling()
    