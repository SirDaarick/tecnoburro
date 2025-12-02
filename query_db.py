import pymongo
from bson import ObjectId
import unicodedata

# --- CONEXIÓN ---
# [NOTA]: Asegúrate de que esta URI sea la correcta y tengas acceso
usuario_id = "690eacdab43948f952b92459"
URI = "mongodb+srv://daarick:93204809Di.@cluster0.w0mxylp.mongodb.net/"
client = pymongo.MongoClient(URI)
db = client["test"] 

# --- UTILERÍA ---
def normalizar_texto(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn').lower()

def obtener_id_carrera(usuario_id_str):
    print(f"\n🔍 Buscando usuario con ID: {usuario_id_str}")
    try:
        oid = ObjectId(usuario_id_str)
        usuario = db["usuarios"].find_one({"_id": oid})
        
        # --- DEBUG: IMPRIMIR DATOS DEL ALUMNO ---
        if usuario:
            print(f"Usuario encontrado: {usuario.get('nombre', 'Sin Nombre')}")
            print(f"Datos completos del usuario:\n{usuario}")
            
            if "dataAlumno" in usuario:
                id_carrera = usuario["dataAlumno"].get("idCarrera")
                print(f"🎓 Carrera detectada (ID): {id_carrera}")
                return id_carrera
            else:
                print("❌ El usuario existe pero no tiene el campo 'dataAlumno'.")
        else:
            print("❌ No se encontró ningún usuario con ese ID en la colección 'usuarios'.")
            
    except Exception as e:
        print(f"❌ Error obteniendo carrera: {e}")
    return None

def obtener_materias_por_carrera(carrera_id):
    print(f"\n📚 Buscando materias para la carrera ID: {carrera_id}")
    catalogo = {}
    
    # Filtramos en MongoDB usando el campo 'idCarrera'
    cursor = db["materias"].find({"idCarrera": carrera_id})
    lista_materias = list(cursor) # Convertimos a lista para poder contar
    
    print(f"🔢 Se encontraron {len(lista_materias)} documentos en la colección 'materias' con ese idCarrera.")

    for doc in lista_materias:
        nombre_limpio = normalizar_texto(doc.get("nombre", ""))
        if nombre_limpio:
            catalogo[nombre_limpio] = {
                "nombre": doc.get("nombre"),
                "creditos": doc.get("creditos")
            }
    return catalogo

# --- BLOQUE PRINCIPAL CORREGIDO ---
if __name__ == "__main__":
    print("=== INICIANDO PRUEBA DE CONEXIÓN ===")
    
    # PASO 1: Obtener el ID de la carrera primero
    id_carrera_encontrado = obtener_id_carrera(usuario_id)
    
    if id_carrera_encontrado:
        # PASO 2: Usar ese ID de carrera para buscar las materias
        resultado = obtener_materias_por_carrera(id_carrera_encontrado)
        
        print(f"\n✅ Total materias procesadas en el catálogo: {len(resultado)}")
        
        if resultado:
            primera_llave = list(resultado.keys())[0]
            print(f"Ejemplo: {primera_llave} -> {resultado[primera_llave]['nombre']}")
    else:
        print("\n⛔ No se puede buscar materias porque no se encontró la carrera del alumno.")