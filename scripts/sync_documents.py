import os
import shutil
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# Configuración de rutas y IDs
RAW_DIR = "documents_raw"
FINAL_DIR = "documents"
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "vs_6a2f5cca5f808191ae9bf9ab632c0e9e")


def procesar_nuevos_archivos():
    # 1. Listar archivos en la carpeta de entrada
    archivos_nuevos = [f for f in os.listdir(RAW_DIR) if os.path.isfile(os.path.join(RAW_DIR, f))]
    
    if not archivos_nuevos:
        print("☕ No hay archivos nuevos para procesar en documents_raw.")
        return

    print(f"📂 Se encontraron {len(archivos_nuevos)} archivos nuevos. Iniciando subida...")

    for nombre_archivo in archivos_nuevos:
        ruta_origen = os.path.join(RAW_DIR, nombre_archivo)
        ruta_destino = os.path.join(FINAL_DIR, nombre_archivo)

        try:
            # 2. Subir e indexar en el Vector Store
            with open(ruta_origen, "rb") as file_obj:
                print(f"⬆️ Subiendo: {nombre_archivo}...")
                batch = client.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=VECTOR_STORE_ID,
                    files=[file_obj]
                )
            
            # 3. Verificar éxito y mover archivo
            if batch.status == "completed":
                # Creamos la carpeta destino si no existe
                if not os.path.exists(FINAL_DIR):
                    os.makedirs(FINAL_DIR)
                
                shutil.move(ruta_origen, ruta_destino)
                print(f"✅ {nombre_archivo} indexado y movido a /documents.")
            else:
                print(f"⚠️ Error al procesar {nombre_archivo}: {batch.status}")

        except Exception as e:
            print(f"❌ Error crítico con {nombre_archivo}: {e}")

if __name__ == "__main__":
    procesar_nuevos_archivos()