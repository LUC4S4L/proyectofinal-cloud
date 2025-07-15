import json
import requests
import os

API_CURSOS_URL = "https://vojyv84ne9.execute-api.us-east-1.amazonaws.com/dev"

def obtener_curso(curso_id, token):
    url = f"{API_CURSOS_URL}/cursos/buscar/{curso_id}"
    headers = {
        "Authorization": token
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception("No se pudo obtener información del curso")

    data = response.json()

    if 'curso' not in data:
        raise Exception("Respuesta inválida del API de cursos")

    return data['curso']
