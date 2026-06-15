import os
from dotenv import load_dotenv
from openai import OpenAI

# Cargar la llave secreta
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("¡Falta la API Key en el archivo .env!")

client = OpenAI(api_key=api_key)

def configurar_vector_store():
    print("1. Creando el Vector Store para RAG...")
    vector_store = client.vector_stores.create(name="Base_Conocimiento_Macro")
    print(f"✅ Vector Store creado con ID: {vector_store.id}")

    print("2. Subiendo el archivo del BCB (Balanza de Pagos 2022-2025)...")
    ruta_pdf = "documents/BalanzaDePagos3T2025.pdf"
    
    with open(ruta_pdf, "rb") as archivo:
        # Usamos el método recomendado para subir y esperar a que se indexe
        file_batch = client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id, 
            file=archivo
        )
        
    print(f"✅ Archivo procesado y vectorizado.")
    
    print("\n" + "="*50)
    print("Guarda este VECTOR_STORE_ID. Lo necesitarás en el Dashboard:")
    print(f"👉 {vector_store.id} 👈")
    print("="*50)

if __name__ == "__main__":
    configurar_vector_store()