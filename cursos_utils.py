import os
import requests

CURSOS_API_URL = os.environ.get('CURSOS_API_URL', 'https://r9ttk3it54.execute-api.us-east-1.amazonaws.com/dev')

def obtener_curso(curso_id, token):
    try:
        response = requests.get(
            f"{CURSOS_API_URL}/cursos/buscar/{curso_id}",
            headers={"Authorization": token}
        )

        if response.status_code != 200:
            return None

        data = response.json()
        return data.get("curso")
    except Exception as e:
        print(f"Error al obtener curso desde API Cursos: {str(e)}")
        return None
