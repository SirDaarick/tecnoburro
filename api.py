from langchain.tools import tool
from alumno_tools import (
    obtener_materias_actuales,
    obtener_calificaciones,
    obtener_clases_del_dia,
    obtener_creditos,
    obtener_datos_alumno,
    obtener_horario_completo,
    obtener_clases_por_profesor,
)
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer, util
from preprocesado import lematizar
import pymongo
import numpy as np
import google.generativeai as genai
ultimo_alumno_id = None
# --- Configuración ---
MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'
MONGO_CONNECTION_STRING = "mongodb+srv://erick_user:SNhfMbL2ekm7FKTV@tecnoburro.wzl0haz.mongodb.net/?appName=TecnoBurro"
DATABASE_NAME = "Base_Conocimiento"
COLLECTION_NAME = "reglamentos_embeddings_v3"

genai.configure(api_key="AIzaSyARQkjQP9CCb76gZYPYFwtyEATcHYT_UBQ")

# --- Cargar modelo ---
model = SentenceTransformer(MODEL_NAME)

# --- Tools ---
tools = [
    obtener_materias_actuales,
    obtener_calificaciones,
    obtener_clases_del_dia,
    obtener_creditos,
    obtener_datos_alumno,
    obtener_horario_completo,
    obtener_clases_por_profesor
]

# --- MongoDB ---
client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
collection = client[DATABASE_NAME][COLLECTION_NAME]

# --- FastAPI ---
app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schema para recibir la pregunta del frontend ---
class Pregunta(BaseModel):
    pregunta: str
    alumno_id: str   # 🔥 Necesario para tools del alumno


# ================================
# Búsqueda de chunks (RAG)
# ================================
def buscar_chunks(pregunta, top_k=3):
    embedding_pregunta = model.encode(pregunta, convert_to_numpy=True).astype(np.float32)
    documentos = list(collection.find({}, {"text": 1, "embedding_vector": 1, "_id": 0}))
    textos = [doc["text"] for doc in documentos]
    embeddings = np.array([doc["embedding_vector"] for doc in documentos], dtype=np.float32)

    similitudes = util.cos_sim(embedding_pregunta, embeddings)[0].cpu().tolist()
    indices_ordenados = np.argsort(similitudes)[::-1][:top_k]

    return [textos[idx] for idx in indices_ordenados]


# ================================
# Generar respuesta del modelo
# ================================
def generar_respuesta(pregunta, chunks):
    contexto = "\n\n".join(chunks)

    # Lista de tools disponibles
    nombres_tools = ", ".join([t.name for t in tools])

    instrucciones = f"""
Eres un asistente académico, responde de manera clara y resumida.

Puedes:
- usar el contexto para responder sobre reglamentos
- usar herramientas para responder sobre datos reales del alumno.

Tools disponibles:
{nombres_tools}

Cuando necesites usar una tool RESPONDE SOLO con este formato EXACTO:

TOOL: <nombre_tool>
ARGS: <alumno_id>

No respondas nada más fuera de ese formato.
"""

    prompt = f"""
{instrucciones}

Contexto:
{contexto}

Pregunta:
{pregunta}
"""

    modelo = genai.GenerativeModel('models/gemini-flash-latest')
    respuesta = modelo.generate_content(prompt).text.strip()

    return respuesta

# ================================
# Endpoint principal del agente
# ================================
@app.post("/preguntar")
def preguntar(data: Pregunta):
    pregunta_original = data.pregunta
    alumno_id = data.alumno_id   # Lo necesitamos para ejecutar tools

    # Normalizar pregunta para RAG
    pregunta_normalizada = lematizar(pregunta_original)

    # RAG → buscar fragmentos relevantes del reglamento
    chunks = buscar_chunks(pregunta_normalizada)

    # Generar respuesta del LLM (puede o no pedir una tool)
    respuesta = generar_respuesta(pregunta_original, chunks)

    # Si la respuesta activa una TOOL
    if respuesta.startswith("TOOL:"):
        lineas = respuesta.split("\n")
        tool_name = lineas[0].replace("TOOL:", "").strip()

        # Ejecutar tool real
        for t in tools:
            if t.name == tool_name:
                tool_result = t.run(alumno_id)
                return {"respuesta": tool_result}

    # Si no usa tool → respuesta normal con RAG
    return {
        "respuesta": respuesta,
        "chunks": chunks
    }