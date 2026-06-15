import os
import sys
import json
import smtplib
import polars as pl
from openai import OpenAI
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import time

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Almacén de vectores para RAG
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "vs_6a2f5cca5f808191ae9bf9ab632c0e9e")

# ---------------------------------------------------------
# 1. MOTOR DE NOTICIAS (IA)
# ---------------------------------------------------------
def obtener_noticias_del_dia():
    print("🌍 Buscando noticias económicas relevantes (Bolivia + Mundo)...")
    
    # FECHA DE HOY
    hoy = datetime.date.today()
    
    query = f"""
    Objetivo: Generar un Briefing de Inteligencia Económica para ejecutivos.
    Fecha del reporte: {hoy}

    FUENTES PRIORITARIAS (Debes buscar activamente en estos dominios usando web_search):
    1. El Deber (site:eldeber.com.bo) -> Secciones de Economía/Dinero.
    2. Yahoo Finance (site:finance.yahoo.com) -> Commodities (Oil, Gold, Zinc) y mercados globales.
    3. Bloomberg (site:bloomberg.com) -> Mercados financieros y commodities.
    4. The Economist (site:economist.com) -> Análisis macroeconómico global.
    5. Reuters (site:reuters.com) -> Noticias internacionales de economía.

    TEMAS CRÍTICOS A MONITOREAR:
    - Bolivia: Reservas Internacionales, Bonos soberanos, Gas/Hidrocarburos, Tipo de Cambio BOB/USD.
    - Global: Precio del Petróleo (Brent/WTI), Oro, Zinc, Tasa de Interés de la Fed, tendencias macroeconómicas globales.

    INSTRUCCIONES DE BÚSQUEDA:
    1. Usa web_search con consultas específicas como "site:bloomberg.com fed interest rates", "site:economist.com world economy", "site:finance.yahoo.com oil price", "site:eldeber.com.bo economía bolivia".
    2. Filtra estrictamente noticias de las últimas 48 HORAS.
    3. Selecciona las 6 noticias más relevantes de alto impacto (2 de Bolivia y 4 Globales/Internacionales).
    
    FORMATO OBLIGATORIO DE SALIDA (Texto plano separado por tuberías):
    TITULO | RESUMEN BREVE (Max 20 palabras) | URL_EXACTA_DE_LA_NOTICIA
    """

    try:
        response = client.responses.create(
            model="gpt-5-mini",
            input=[
                {
                    "role": "system",
                    "content": "Eres un analista de inteligencia financiera. Tu objetivo es buscar y estructurar noticias económicas de alta relevancia para Bolivia y el contexto global, siguiendo el formato exacto requerido. IMPORTANTE: Bajo ninguna circunstancia debes responder con preguntas, aclaraciones o comentarios. Si encuentras algún obstáculo de búsqueda (como restricciones de robots.txt o falta de noticias en las últimas 48 horas), relaja automáticamente los criterios a la última semana o busca en fuentes alternativas, pero produce SIEMPRE el formato de salida obligatorio (TITULO | RESUMEN | URL) con las noticias que encuentres."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": [VECTOR_STORE_ID]
                },
                {
                    "type": "web_search",
                    "filters": {
                        "allowed_domains": [
                            "www.bcb.gob.bo",
                            "www.ine.gob.bo",
                            "tradingeconomics.com",
                            "finance.yahoo.com",
                            "www.bbc.com",
                            "eldeber.com.bo",
                            "www.economist.com",
                            "economist.com",
                            "bloomberg.com",
                            "www.bloomberg.com",
                            "reuters.com",
                            "www.reuters.com",
                            "ft.com",
                            "www.ft.com"
                        ]
                    }
                }
            ]
        )
        
        raw_text = response.output_text
        noticias = []
        
        # Parseo robusto
        for linea in raw_text.strip().split('\n'):
            # Limpieza básica
            linea = linea.strip()
            if "|" in linea and "http" in linea:
                partes = linea.split("|")
                if len(partes) >= 3:
                    titulo = partes[0].strip()
                    resumen = partes[1].strip()
                    link = partes[2].strip()
                    
                    # Validación extra: evitar enlaces rotos o genéricos si es posible
                    if len(titulo) > 3 and "http" in link:
                        noticias.append({
                            "titulo": titulo,
                            "resumen": resumen,
                            "link": link
                        })
        
        print(f"✅ Se encontraron {len(noticias)} noticias relevantes.")
        
        # Guardar respaldo
        if noticias:
            with open("data/processed/latest_news.json", "w", encoding="utf-8") as f:
                json.dump(noticias, f, indent=4, ensure_ascii=False)
            
        return noticias

    except Exception as e:
        print(f"⚠️ Error buscando noticias: {e}")
        return []

# ---------------------------------------------------------
# 2. GENERADOR DE CORREO (HTML)
# ---------------------------------------------------------
def generar_html_body(noticias, df_macro):
    """Genera el contenido HTML del correo una sola vez"""
    
    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; background-color: #f4f4f4; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            
            <!-- ENCABEZADO -->
            <div style="background-color: #1a202c; padding: 25px; text-align: center;">
                <h2 style="color: #ffffff; margin: 0; font-size: 24px;">📊 Monitor Macro Bolivia</h2>
                <p style="color: #a0aec0; margin: 5px 0 0; font-size: 14px;">Inteligencia Diaria: {datetime.date.today().strftime('%d/%m/%Y')}</p>
            </div>
            
            <div style="padding: 30px;">
                <!-- SECCIÓN NOTICIAS -->
                <div style="margin-bottom: 30px;">
                    <h3 style="color: #2c5282; border-bottom: 2px solid #2c5282; padding-bottom: 8px; margin-top: 0;">🗞️ Radar de Noticias</h3>
                    <ul style="padding-left: 0; list-style-type: none;">
    """
    
    if noticias:
        for n in noticias:
            html_content += f"""
                <li style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #edf2f7;">
                    <strong style="font-size: 16px; color: #2d3748; display: block; margin-bottom: 5px;">{n['titulo']}</strong>
                    <span style="color: #4a5568; font-size: 14px;">{n['resumen']}</span> <br>
                    <a href="{n['link']}" style="color: #3182ce; text-decoration: none; font-size: 13px; font-weight: 600; margin-top: 5px; display: inline-block;">Leer nota completa →</a>
                </li>
            """
    else:
        html_content += """
            <li style="color: #718096; font-style: italic;">
                No se detectaron eventos de alto impacto en las fuentes monitoreadas (El Deber, BBC, Yahoo Finance) en las últimas 24h.
            </li>
        """
    
    html_content += """
                    </ul>
                </div>
                
                <!-- SECCIÓN VARIABLES -->
                <div>
                    <h3 style="color: #276749; border-bottom: 2px solid #276749; padding-bottom: 8px;">📉 Indicadores Clave (Snapshot)</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <tr style="background-color: #f7fafc; text-align: left;">
                            <th style="padding: 10px; border-bottom: 2px solid #e2e8f0; color: #4a5568;">Variable</th>
                            <th style="padding: 10px; border-bottom: 2px solid #e2e8f0; color: #4a5568;">Valor</th>
                            <th style="padding: 10px; border-bottom: 2px solid #e2e8f0; color: #4a5568;">Unidad</th>
                        </tr>
    """
    
    # Mostramos las primeras 10 variables
    for row in df_macro.head(10).iter_rows(named=True):
        val = row['Valor_Actual']
        display_val = f"{val:,.2f}" if val is not None else "-"
        
        html_content += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #edf2f7; color: #2d3748;">{row['Variable']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #edf2f7; font-weight: bold; color: #2d3748;">{display_val}</td>
                <td style="padding: 10px; border-bottom: 1px solid #edf2f7; color: #718096; font-size: 12px;">{row['Unidad']}</td>
            </tr>
        """

    html_content += """
                    </table>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="#" style="background-color: #2b6cb0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px;">Acceder al Dashboard</a>
                </div>
            </div>
            
            <div style="background-color: #edf2f7; padding: 15px; text-align: center; font-size: 12px; color: #a0aec0;">
                Reporte generado automáticamente por Agente IA | Fuentes: BCB, INE, BM, El Deber, Yahoo Finance.
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def enviar_newsletter_masivo(noticias):
    recipients_str = os.getenv("EMAIL_TEAM_LIST")
    if not recipients_str:
        print("❌ No hay destinatarios configurados en .env")
        return

    destinatarios = [email.strip() for email in recipients_str.split(",")]
    
    # Cargar datos una sola vez
    try:
        df = pl.read_csv("data/processed/top_25_macro_bolivia.csv")
    except:
        print("⚠️ No se encontró la tabla de variables. Enviando solo noticias.")
        df = pl.DataFrame({"Variable": [], "Valor_Actual": [], "Unidad": []})

    # Generar el HTML una sola vez
    html_body = generar_html_body(noticias, df)
    
    # Configuración SMTP
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    try:
        print(f"📧 Iniciando conexión con Gmail para enviar a {len(destinatarios)} personas...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        
        # Enviar correo uno por uno
        for email in destinatarios:
            msg = MIMEMultipart("alternative")
            msg['Subject'] = f"📈 Macro Briefing: {datetime.date.today().strftime('%d-%b')}"
            msg['From'] = user
            msg['To'] = email 
            
            msg.attach(MIMEText(html_body, "html"))
            
            server.send_message(msg)
            print(f"   -> Enviado a: {email}")
            time.sleep(1) # Pausa cortés
            
        server.quit()
        print("✅ ¡Envío masivo completado!")
        
    except Exception as e:
        print(f"❌ Error crítico en el envío: {e}")

if __name__ == "__main__":
    # 1. Obtener noticias
    news = obtener_noticias_del_dia()
    
    if not news:
        # Intentar leer las noticias guardadas si la IA falló hoy
        try:
            with open("data/processed/latest_news.json", "r", encoding="utf-8") as f:
                news = json.load(f)
            print("⚠️ Usando noticias cacheadas.")
        except:
            news = []

    # 2. Enviar correo
    enviar_newsletter_masivo(news)