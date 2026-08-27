import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from database import SessionLocal
from models import Transaccion
from ingestion import procesar_mensaje_con_gemini

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- SERVIDOR WEB CON REUTILIZACIÓN DE PUERTO ---
class CustomHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        """Responde a las verificaciones de salud de Render"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

    def do_GET(self):
        """Responde a cron-job.org para mantener Render despierto"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"Bot activo")

    def do_POST(self):
        """Recibe notificaciones de BCP / Yape desde Apps Script"""
        if self.path == '/webhook/bcp':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                texto_correo = data.get('text', '')

                if texto_correo:
                    datos = procesar_mensaje_con_gemini(f"Notificación bancaria: {texto_correo}")

                    if datos and "amount" in datos:
                        db = SessionLocal()
                        try:
                            nueva = Transaccion(
                                amount=datos["amount"],
                                currency=datos.get("currency", "PEN"),
                                category=datos.get("category", "Otros"),
                                transaction_type=datos.get("transaction_type", "Gasto"),
                                payment_method=datos.get("payment_method", "BCP"),
                                description=datos.get("description", "Notificación bancaria")
                            )
                            db.add(nueva)
                            db.commit()
                            print(f"✅ Gasto bancario registrado: S/. {datos['amount']}")
                        finally:
                            db.close()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            except Exception as e:
                print(f"Error procesando webhook: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"status": "error"}')
        else:
            self.send_response(404)
            self.end_headers()

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server = ReusableHTTPServer(("0.0.0.0", port), CustomHandler)
    server.serve_forever()

# --- BOT DE TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Envíame un mensaje de texto o audio para registrar tus finanzas.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text
    await update.message.reply_chat_action("typing")
    
    try:
        datos = procesar_mensaje_con_gemini(texto_usuario)
        
        if datos and "amount" in datos:
            db = SessionLocal()
            try:
                nueva = Transaccion(
                    amount=datos["amount"],
                    currency=datos.get("currency", "PEN"),
                    category=datos.get("category", "Otros"),
                    transaction_type=datos.get("transaction_type", "Gasto"),
                    payment_method=datos.get("payment_method", "Efectivo"),
                    description=datos.get("description", texto_usuario)
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
            await update.message.reply_text("❌ No pude entender los datos de la transacción. Intenta detallar el monto y la categoría.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error procesando el mensaje: {e}")

def main():
    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot y Webhook iniciados con éxito...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    