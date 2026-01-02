import pandas as pd
import io
import requests
import threading
import http.server
import socketserver
import asyncio
import sys
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURACIÓN SEGURA (Render Environment Variables) ---
TELEGRAM_TOKEN = os.getenv("8563563343:AAHwjjnrTk51on1bWbZxkYm-DfgG5MynfQ4")
SHEET_ID = os.getenv("1W3fKOl_YxE7jj-F425CbDXXvHvqXvMlZ")
SHEET_URL = f"https://docs.google.com/spreadsheets/d/1W3fKOl_YxE7jj-F425CbDXXvHvqXvMlZ/edit?gid=261125878#gid=261125878"

# --- SERVIDOR PARA EVITAR "PORT SCAN TIMEOUT" EN RENDER ---
def run_health_server():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot Zurich Online")
    
    # Render asigna el puerto en la variable PORT automáticamente
    port = int(os.environ.get("PORT", 8080))
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"Servidor de salud activo en puerto {port}", flush=True)
            httpd.serve_forever()
    except Exception as e:
        print(f"Error en servidor web: {e}", flush=True)

# --- MOTOR DE BÚSQUEDA ---
async def consultar_siniestro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    busqueda = str(update.message.text).strip().upper()
    print(f"Buscando siniestro: {busqueda}", flush=True)
    
    try:
        response = requests.get(SHEET_URL, timeout=30)
        excel_data = io.BytesIO(response.content)
        dict_hojas = pd.read_excel(excel_data, sheet_name=None, header=None)
        
        for nombre_hoja, df in dict_hojas.items():
            fila_encabezado = None
            for i, row in df.iterrows():
                if 'SINIESTRO' in row.astype(str).str.upper().values:
                    fila_encabezado = i
                    break
            
            if fila_encabezado is not None:
                df.columns = df.iloc[fila_encabezado].astype(str).str.strip().str.upper()
                df = df.iloc[fila_encabezado + 1:].reset_index(drop=True)
                
                if 'SINIESTRO' in df.columns:
                    df['SINIESTRO'] = df['SINIESTRO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper()
                    resultado = df[df['SINIESTRO'].str.contains(busqueda, na=False, regex=False)]
                    
                    if not resultado.empty:
                        f = resultado.iloc[0]
                        def get_val(claves):
                            for col in df.columns:
                                for c in claves:
                                    if c in col:
                                        val = f.get(col, "N/A")
                                        return val if pd.notna(val) and str(val).strip() != "" else "N/A"
                            return "N/A"

                        # REPORTE CON LOS 17 CAMPOS
                        res = (
                            f"✅ **SINIESTRO ENCONTRADO EN: {nombre_hoja}**\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🆔 **Siniestro:** `{f.get('SINIESTRO')}`\n"
                            f"📅 **Fecha:** {str(get_val(['FECHA'])).split(' ')[0]}\n"
                            f"⏰ **Hora Turnado:** {get_val(['HORA', 'TURNAD'])}\n"
                            f"👷 **Ajustador:** {get_val(['AJUSTA', 'AJUSTADOR'])}\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🚗 **Vehículo:** {get_val(['VEHICULO', 'VEHÍCULO'])}\n"
                            f"👤 **Asegurado:** {get_val(['ASEGURADO'])}\n"
                            f"📄 **Póliza:** {get_val(['POLIZA', 'PÓLIZA'])}\n"
                            f"🔢 **Folio Rol:** {get_val(['FOLIO ROL', 'FOLIO'])}\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"⭐ **Destacado:** {get_val(['DESTACADO'])}\n"
                            f"💰 **Recuperación:** {get_val(['RECUPERACION', 'RECUPERACIÓN'])}\n"
                            f"🗺️ **Local/Foráneo:** {get_val(['LOCAL', 'FORANEO'])}\n"
                            f"📍 **Ubicación:** {get_val(['UBICACION', 'UBICACIÓN'])}\n"
                            f"🛣️ **KM:** {get_val(['KM', 'KILOMETRAJE'])}\n"
                            f"🏗️ **Grúas:** {get_val(['GRUAS', 'GRÚAS'])}\n"
                            f"🧾 **Facturación:** {get_val(['FACTURACION', 'FACTURACIÓN'])}\n"
                            f"💻 **Novalink:** {get_val(['NOVALINK', 'CARGA'])}\n"
                            f"📝 **Observaciones:** {get_val(['OBSERVACIONES', 'NOTAS'])}\n"
                            f"━━━━━━━━━━━━━━━━━━━━"
                        )
                        await update.message.reply_text(res, parse_mode='Markdown')
                        return

        await update.message.reply_text(f"❌ No encontré `{busqueda}`.")
    except Exception as e:
        print(f"Error en búsqueda: {e}", flush=True)

# --- INICIO DEL PROGRAMA ---
async def main():
    # Iniciamos el servidor de salud para que Render vea el puerto activo
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # Iniciamos la aplicación de Telegram
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, consultar_siniestro))
    
    print("Bot Zurich Total - Iniciado correctamente.", flush=True)
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        # Bucle para mantener el proceso vivo
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
