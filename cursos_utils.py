import requests
import os

API_CURSOS_URL = os.environ.get("API_CURSOS_URL", "https://vojyv84ne9.execute-api.us-east-1.amazonaws.com/dev")

def obtener_datos_curso(curso_id, token):
    url = f"{API_CURSOS_URL}/cursos/buscar/{curso_id}"
    headers = { "Authorization": token }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data.get("curso")
        return None

    except Exception as e:
        print(f"[Error] No se pudo obtener el curso: {str(e)}")
        return None
