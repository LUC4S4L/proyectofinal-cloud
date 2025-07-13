import urllib.request
import json

def validar_token(token):
    if not token:
        raise Exception("Token requerido")

    url = "https://c0fmkco8rb.execute-api.us-east-1.amazonaws.com/dev/usuario/validar"
    req = urllib.request.Request(url, headers={"Authorization": token})

    try:
        with urllib.request.urlopen(req) as response:
            body = response.read()
            data = json.loads(body)
            payload = json.loads(data["body"])["payload"]
            return payload

    except Exception as e:
        raise Exception(f"Error al validar token: {str(e)}")

