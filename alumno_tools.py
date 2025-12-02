from langchain.tools import tool
import requests

BACKEND_URL = "http://localhost:3001"  # Node.js

@tool
def obtener_materias_actuales(alumno_id: str):
    """Devuelve las materias actuales del alumno con profesor, salón y horario."""
    try:
        url = f"{BACKEND_URL}/alumnos/{alumno_id}/materias-actuales"
        response = requests.get(url)

        if response.status_code != 200:
            return f"Error consultando materias: {response.text}"

        materias = response.json()

        if not materias:
            return "No tienes materias inscritas actualmente."

        texto = "Tus materias actuales son:\n\n"
        for m in materias:
            texto += (
                f"📘 {m['materia']} ({m['clave']})\n"
                f"👨‍🏫 Profesor: {m['profesor']}\n"
                f"🏫 Salón: {m['salon']}\n"
                f"⏰ Horario: {m['horario']}\n\n"
            )

        return texto

    except Exception as e:
        return f"Error interno en la herramienta obtener_materias_actuales: {str(e)}"
    

@tool
def obtener_calificaciones(alumno_id: str):
    """Devuelve la lista de materias y calificaciones del alumno."""
    try:
        url = f"{BACKEND_URL}/alumnos/{alumno_id}/calificaciones"
        response = requests.get(url)

        if response.status_code != 200:
            return f"Error consultando calificaciones: {response.text}"

        datos = response.json()

        if not datos:
            return "No tienes calificaciones registradas actualmente."

        texto = "📘 Tus calificaciones actuales:\n\n"

        for m in datos:
            texto += (
                f"- {m['materia']} ({m['clave']}): "
                f"{m['calificacion']}\n"
            )

        return texto

    except Exception as e:
        return f"Error interno en obtener_calificaciones: {str(e)}"
    

@tool
def obtener_clases_del_dia(entrada: str):
    """
    Puede recibir:
    - "<alumno_id>|<dia>"
    - "<dia>"  (y entonces usamos alumno_id fijo en FastAPI)
    """

    try:
        # 1) Si viene con '|', la separamos normalmente
        if "|" in entrada:
            alumno_id, dia = entrada.split("|")
        else:
            # 2) Si NO viene con '|', usamos alumno fijo global
            #    ⚠ FastAPI INSERTA el ID aquí antes de llamar a la tool
            from api import ultimo_alumno_id  
            alumno_id = ultimo_alumno_id
            dia = entrada.strip()

        url = f"{BACKEND_URL}/alumnos/{alumno_id}/clases-dia/{dia}"
        response = requests.get(url)

        if response.status_code != 200:
            return f"Error consultando clases del día: {response.text}"

        datos = response.json()

        if isinstance(datos, dict) and "message" in datos:
            return datos["message"]

        texto = f"📅 Clases del {dia.capitalize()}:\n\n"

        for c in datos:
            texto += (
                f"📘 {c['materia']} ({c['clave']})\n"
                f"👨‍🏫 Profesor: {c['profesor']}\n"
                f"🏫 Salón: {c['salon']}\n"
                f"⏰ Horario: {c['horario']}\n\n"
            )

        return texto

    except Exception as e:
        return f"Error interno en obtener_clases_del_dia: {str(e)}"
    
    
@tool
def obtener_creditos(alumno_id: str):
    """Devuelve créditos cursados, totales y avance porcentual del alumno."""
    try:
        url = f"{BACKEND_URL}/alumnos/{alumno_id}/creditos"
        response = requests.get(url)

        if response.status_code != 200:
            return "Error consultando créditos."

        data = response.json()

        texto = "🎓 Información de créditos:\n\n"
        texto += f"- Créditos cursados: {data['creditosCursados']}\n"

        if data["creditosTotales"]:
            texto += f"- Créditos totales: {data['creditosTotales']}\n"
            texto += f"- Avance: {data['porcentaje']}%\n"
        else:
            texto += "- No se encontró información total de créditos\n"

        return texto

    except Exception as e:
        return f"Error interno en obtener_creditos: {str(e)}"
    
@tool
def obtener_datos_alumno(alumno_id: str):
    """Devuelve datos generales del alumno: nombre, correo, carrera, etc."""
    try:
        url = f"{BACKEND_URL}/alumnos/{alumno_id}/datos"
        response = requests.get(url)

        if response.status_code != 200:
            return "Error consultando datos del alumno."

        d = response.json()

        return (
            "Datos del alumno:\n\n"
            f"Nombre: {d['nombre']}\n"
            f"Correo: {d['correo']}\n"
            f"Carrera: {d['carrera']} ({d['sigla']})\n"
            f"Créditos cursados: {d['creditosCursados']}\n"
            f"Promedio: {d['promedio']}\n"
        )

    except Exception as e:
        return f"Error interno en obtener_datos_alumno: {str(e)}"
    
@tool
def obtener_horario_completo(alumno_id: str):
    """Devuelve el horario completo del alumno."""
    try:
        url = f"{BACKEND_URL}/alumnos/{alumno_id}/horario"
        response = requests.get(url)

        if response.status_code != 200:
            return "Error consultando horario."

        horario = response.json()

        if not horario:
            return "No se encontraron materias inscritas."

        texto = "📅 Tu horario completo:\n\n"

        for h in horario:
            texto += (
                f"{h['materia']} ({h['clave']})\n"
                f"Profesor: {h['profesor']}\n"
                f"{h['dia']}\n"
                f"{h['horario']}\n"
                f"Salón: {h['salon']}\n\n"
            )

        return texto

    except Exception as e:
        return f"Error interno en obtener_horario_completo: {str(e)}"
    
    
@tool
def obtener_clases_por_profesor(entrada: str):
    """
    Entrada con formato: "<alumno_id>|<nombre_profesor>"
    """
    try:
        alumno_id, nombre_profesor = entrada.split("|")

        url = f"{BACKEND_URL}/alumnos/{alumno_id}/clases-profesor/{nombre_profesor}"
        response = requests.get(url)

        if response.status_code != 200:
            return "Error consultando clases del profesor."

        clases = response.json()

        if not clases:
            return f"No tienes clases con el profesor {nombre_profesor}."

        texto = f"📚 Clases con {nombre_profesor}:\n\n"

        for c in clases:
            texto += (
                f"{c['materia']} ({c['clave']})\n"
                f"{c['dia']}\n"
                f"{c['horario']}\n"
                f"Salón: {c['salon']}\n\n"
            )

        return texto

    except Exception as e:
        return f"Error interno en obtener_clases_por_profesor: {str(e)}"