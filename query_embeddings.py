# query_embeddings.py
from sentence_transformers import SentenceTransformer, util
from preprocesado import lematizar
import pymongo
import numpy as np
import google.generativeai as genai

# --- Configuración ---
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'
MONGO_CONNECTION_STRING = "mongodb+srv://erick_user:SNhfMbL2ekm7FKTV@tecnoburro.wzl0haz.mongodb.net/?appName=TecnoBurro"
DATABASE_NAME = "Base_Conocimiento"
COLLECTION_NAME = "reglamentos_embeddings_v2"

# --- Configurar Gemini ---
genai.configure(api_key="AIzaSyARQkjQP9CCb76gZYPYFwtyEATcHYT_UBQ")

# --- Cargar modelo ---
print("Cargando modelo de embeddings...")
model = SentenceTransformer(MODEL_NAME)
print("Modelo cargado correctamente.\n")

# --- Conectar a MongoDB ---
client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
collection = client[DATABASE_NAME][COLLECTION_NAME]


# --- Función para buscar chunks más similares ---
def buscar_chunks(pregunta, top_k=5):
    print(f"Buscando respuesta para: {pregunta}\n")
    embedding_pregunta = model.encode(pregunta, convert_to_numpy=True).astype(np.float32)

    # Obtener embeddings de la BD
    documentos = list(collection.find({}, {"text": 1, "embedding_vector": 1, "_id": 0}))
    textos = [doc["text"] for doc in documentos]
    embeddings = np.array([doc["embedding_vector"] for doc in documentos], dtype=np.float32)

    # Calcular similitud coseno
    similitudes = util.cos_sim(embedding_pregunta, embeddings)[0].cpu().tolist()

    # Ordenar por similitud descendente
    indices_ordenados = np.argsort(similitudes)[::-1][:top_k]

    resultados = []
    for idx in indices_ordenados:
        resultados.append({
            "similaridad": similitudes[idx],
            "texto": textos[idx]
        })
    return resultados


# --- Función para generar respuesta con Gemini ---
def generar_respuesta(pregunta, chunks):
    contexto = "\n\n".join([c["texto"] for c in chunks])
    prompt = f"""
Eres un asistente experto en reglamentos académicos universitarios.
Usa la siguiente información del reglamento para responder con claridad y precisión:

Contexto:
{contexto}

Pregunta del usuario:
{pregunta}

Responde de forma breve, coherente y formal, sin inventar información.
"""
    # Este modelo (Gemini 1.0 Flash) también tiene un buen límite gratuito
    modelo = genai.GenerativeModel('models/gemini-flash-latest')
    respuesta = modelo.generate_content(prompt)
    return respuesta.text


# --- Ejecución principal ---
if __name__ == "__main__":
    print("============== Tecnoburro ==============")
    print("Escribe tu pregunta (o 'salir' para terminar)\n")

    while True:
        pregunta = input("Tu pregunta: ").strip()
        pregunta_normalizada = lematizar(pregunta)
        print(pregunta_normalizada)
        if pregunta.lower() in ["salir", "exit", "quit"]:
            print("\nSaliendo del asistente. ¡Hasta luego! ")
            break
        

        # Buscar información relevante
        top_chunks = buscar_chunks(pregunta_normalizada, top_k=3)

        print("\n===  Coincidencias más relevantes ===\n")
        for i, chunk in enumerate(top_chunks, 1):
            print(f"[{i}] (Similitud: {chunk['similaridad']:.4f})")
            print(chunk["texto"][:500])  # muestra solo parte del texto
            print("-" * 80)

        print("\nGenerando respuesta con Gemini...\n")
        respuesta = generar_respuesta(pregunta, top_chunks)

        print("\n===  Respuesta generada por la API ===\n")
        print(respuesta)
        print("\n" + "=" * 80 + "\n")
