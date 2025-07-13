import requests
import json

def validar_token(token):
    if not token:
        raise Exception("Token requerido")

    url = "https://c0fmkco8rb.execute-api.us-east-1.amazonaws.com/dev/usuario/validar"

    try:
        response = requests.get(url, headers={"Authorization": token})

        if response.status_code != 200:
            raise Exception("Token inválido o expirado")

        body = response.json()
        payload = json.loads(body["body"])["payload"]
        return payload

    except Exception as e:
        raise Exception(f"Error al validar token: {str(e)}")
