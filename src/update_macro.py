import os
import sys
import time
import polars as pl
from openai import OpenAI
from dotenv import load_dotenv
import datetime
import re

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Almacén de vectores para RAG
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "vs_6a2f5cca5f808191ae9bf9ab632c0e9e")

def limpiar_valor_numerico(texto_valor):
    """Intenta extraer un número flotante de un texto sucio (ej: '$ 45.3 millones')."""
    if texto_valor is None or "null" in str(texto_valor).lower():
        return None
    # Busca el primer patrón de número (ej: 123.45 o -12)
    match = re.search(r'-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?', str(texto_valor))
    if match:
        # Eliminar comas de miles para que Python entienda el float
        limpio = match.group().replace(",", "")
        try:
            return float(limpio)
        except:
            return None
    return None

def consultar_lote_texto_plano(lista_lote, indice, total_lotes):
    print(f"⏳ Procesando lote {indice}/{total_lotes}...")
    
    query = f"""
    Actualiza datos para: {lista_lote}

    INSTRUCCIONES:
    1. Usa web_search para datos externos.
    2. Usa file_search para BCB/INE.
    
    FORMATO DE RESPUESTA OBLIGATORIO (TXT):
    - NO uses JSON. NO uses Markdown.
    - Escribe UNA línea por variable usando el separador "|".
    - Estructura: NOMBRE_EXACTO_VARIABLE | VALOR_NUMERICO | FUENTE_CORTA
    
    Ejemplo de salida esperada:
    Precio del Oro | 2034.50 | Banco Mundial
    PIB Crecimiento | 2.3 | INE Reporte Q3
    Variable Rara | null | No encontrado
    
    REGLAS:
    - Fuente: MÁXIMO 5 PALABRAS. PROHIBIDO poner URLs o corchetes [].
    - Valor: Solo el número (sin símbolos % o $). Si no hay dato, pon null.
    """

    try:
        response = client.responses.create(
            model="gpt-5-mini",
            input=[
                {
                    "role": "system",
                    "content": "Eres un asistente experto en macroeconomía boliviana. Tu tarea es extraer y actualizar los últimos datos económicos solicitados utilizando las herramientas de búsqueda web (web_search) y búsqueda de archivos indexados (file_search). Debes seguir estrictamente las instrucciones del formato de salida."
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
                            "www.economist.com"
                        ]
                    }
                }
            ]
        )
        
        raw_text = response.output_text
        
        # --- PARSEO MANUAL (MUCHO MÁS ROBUSTO QUE JSON) ---
        datos_parsed = {}
        
        # Dividir por líneas y procesar una por una
        lineas = raw_text.strip().split('\n')
        
        for linea in lineas:
            # Ignorar líneas vacías o de código
            if "|" not in linea or "```" in linea:
                continue
                
            partes = linea.split("|")
            if len(partes) >= 3:
                nombre = partes[0].strip()
                valor_raw = partes[1].strip()
                fuente = partes[2].strip()
                
                # Limpieza extra de la fuente (quitar URLs si se colaron)
                fuente = re.sub(r'\[.*?\]\(.*?\)', '', fuente) # Quita markdown links
                fuente = fuente.replace('"', '').strip()
                
                # Convertir valor
                val_float = limpiar_valor_numerico(valor_raw)
                
                datos_parsed[nombre] = {
                    "valor": val_float,
                    "fuente_detalle": fuente
                }
        
        return datos_parsed

    except Exception as e:
        print(f"⚠️ Error en el lote {indice}: {e}")
        return {}

def actualizar_csv():
    ruta_csv = "data/processed/top_25_macro_bolivia.csv"
    df = pl.read_csv(ruta_csv)
    todas_las_vars = df["Variable"].to_list()
    
    TAMANO_LOTE = 5
    datos_consolidados = {}
    
    # Iterar por lotes
    for i in range(0, len(todas_las_vars), TAMANO_LOTE):
        lote_actual = todas_las_vars[i : i + TAMANO_LOTE]
        numero_lote = (i // TAMANO_LOTE) + 1
        total_lotes = (len(todas_las_vars) + TAMANO_LOTE - 1) // TAMANO_LOTE
        
        datos_lote = consultar_lote_texto_plano(lote_actual, numero_lote, total_lotes)
        
        if datos_lote:
            datos_consolidados.update(datos_lote)
            print(f"   ✅ Lote {numero_lote} procesado con éxito.")
        else:
            print(f"   ⚠️ Lote {numero_lote} vacío o fallido.")
        
        time.sleep(1) 

    print(f"📊 Se recolectaron datos para {len(datos_consolidados)} variables.")

    if not datos_consolidados:
        print("❌ No hay datos para actualizar.")
        return

    # Funciones de actualización
    def update_val(struct_val):
        var = struct_val["Variable"]
        curr = struct_val["Valor_Actual"]
        # Buscamos coincidencias aproximadas o exactas
        if var in datos_consolidados:
            val = datos_consolidados[var]["valor"]
            if val is not None:
                return float(val)
        return curr

    def update_src(struct_val):
        var = struct_val["Variable"]
        curr = struct_val["Fuente"]
        if var in datos_consolidados:
            src = datos_consolidados[var]["fuente_detalle"]
            if src and src.lower() != "null":
                return str(src)
        return curr

    # Aplicar cambios
    df = df.with_columns([
        pl.struct(["Variable", "Valor_Actual"]).map_elements(update_val, return_dtype=pl.Float64).alias("Valor_Actual"),
        pl.struct(["Variable", "Fuente"]).map_elements(update_src, return_dtype=pl.String).alias("Fuente"),
        pl.lit(datetime.date.today().strftime("%Y-%m-%d")).alias("Ultima_Actualizacion")
    ])

    df.write_csv(ruta_csv)
    print(f"🎉 ¡Tabla actualizada a las {datetime.datetime.now().strftime('%H:%M:%S')}!")

if __name__ == "__main__":
    actualizar_csv()