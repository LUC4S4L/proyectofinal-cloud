import requests
import json

API_USUARIOS_URL = 'https://c0fmkco8rb.execute-api.us-east-1.amazonaws.com/dev'

def validar_token(token):
    if not token:
        raise Exception("Token requerido")

    response = requests.get(f"{API_USUARIOS_URL}/usuario/validar", headers={"Authorization": token})

    if response.status_code != 200:
        raise Exception("Token inválido o expirado")

    payload = json.loads(response.json().get('body', '{}')).get('payload')
    if not payload:
        raise Exception("Token inválido")

    return payload  # Contiene tenant_id y username
