import pandas as pd
import io
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8563563343:AAHwjjnrTk51on1bWbZxkYm-DfgG5MynfQ4"
SHEET_ID = "1W3fKOl_YxE7jj-F425CbDXXvHvqXvMlZ"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

async def consultar_siniestro_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    busqueda = str(update.message.text).strip().upper()
    
    try:
        response = requests.get(SHEET_URL, timeout=25)
        excel_data = io.BytesIO(response.content)
        dict_hojas = pd.read_excel(excel_data, sheet_name=None, header=None)
        
        encontrado = False

        for nombre_hoja, df in dict_hojas.items():
            fila_encabezado = None
            for i, row in df.iterrows():
                if 'SINIESTRO' in row.astype(str).str.upper().values:
                    fila_encabezado = i
                    break
            
            if fila_encabezado is not None:
                df.columns = df.iloc[fila_encabezado].astype(str).str.strip().str.upper()
                df = df.iloc[fila_encabezado + 1:].reset_index(drop=True)
                
                df['SINIESTRO'] = df['SINIESTRO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.upper()
                resultado = df[df['SINIESTRO'].str.contains(busqueda, na=False, regex=False)]

                if not resultado.empty:
                    f = resultado.iloc[0]
                    
                    def buscar_dato(palabras_clave):
                        for col in df.columns:
                            for clave in palabras_clave:
                                if clave in col:
                                    valor = f.get(col, "N/A")
                                    return valor if pd.notna(valor) and str(valor).strip() != "" else "N/A"
                        return "N/A"

                    # --- EXTRACCIÓN DETALLADA ---
                    fecha = buscar_dato(['FECHA'])
                    ajusta = buscar_dato(['AJUSTA', 'AJUSTADOR'])
                    hora = buscar_dato(['HORA', 'TURNAD'])
                    vehiculo = buscar_dato(['VEHICULO', 'VEHÍCULO'])
                    asegurado = buscar_dato(['ASEGURADO'])
                    poliza = buscar_dato(['POLIZA', 'PÓLIZA'])
                    folio = buscar_dato(['FOLIO ROL', 'FOLIO'])
                    destacado = buscar_dato(['DESTACADO'])
                    recuperacion = buscar_dato(['RECUPERACION', 'RECUPERACIÓN'])
                    localidad = buscar_dato(['LOCAL', 'FORANEO', 'FORÁNEO'])
                    ubicacion = buscar_dato(['UBICACION', 'UBICACIÓN', 'LUGAR'])
                    km = buscar_dato(['KM', 'KILOMETRAJE'])
                    observaciones = buscar_dato(['OBSERVACIONES', 'NOTAS'])
                    
                    # SEPARACIÓN DE GRÚAS Y FACTURACIÓN
                    gruas = buscar_dato(['GRUAS', 'GRÚAS'])
                    facturacion = buscar_dato(['FACTURACION', 'FACTURACIÓN', 'FACTURA'])
                    
                    novalink = buscar_dato(['NOVALINK', 'CARGA', 'NL'])

                    fecha_str = str(fecha).split(' ')[0] if fecha != "N/A" else "N/A"

                    respuesta = (
                        f"✅ **SINIESTRO ENCONTRADO EN: {nombre_hoja}**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 **Siniestro:** `{f.get('SINIESTRO')}`\n"
                        f"📅 **Fecha:** {fecha_str}\n"
                        f"⏰ **Hora Turnado:** {hora}\n"
                        f"👷 **Ajustador:** {ajusta}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🚗 **Vehículo:** {vehiculo}\n"
                        f"👤 **Asegurado:** {asegurado}\n"
                        f"📄 **Póliza:** {poliza}\n"
                        f"🔢 **Folio Rol:** {folio}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"⭐ **Destacado:** {destacado}\n"
                        f"💰 **Recuperación:** {recuperacion}\n"
                        f"🗺️ **Local/Foráneo:** {localidad}\n"
                        f"📍 **Ubicación:** {ubicacion}\n"
                        f"🛣️ **KM:** {km}\n"
                        f"🏗️ **Grúas:** {gruas}\n"
                        f"🧾 **Facturación:** {facturacion}\n"
                        f"💻 **Novalink:** {novalink}\n"
                        f"📝 **Observaciones:** {observaciones}\n"
                        f"━━━━━━━━━━━━━━━━━━━━"
                    )
                    await update.message.reply_text(respuesta, parse_mode='Markdown')
                    encontrado = True
                    break 

        if not encontrado:
            await update.message.reply_text(f"❌ No encontré el siniestro `{busqueda}`.")
            
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    print("Bot de verificacion de siniestros- Iniciado")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, consultar_siniestro_global))

    app.run_polling()
