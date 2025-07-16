import os
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

JWT_SECRET = os.environ.get('JWT_SECRET', 'supersecreto123')

def validar_token(token):
    if not token:
        raise Exception("Token requerido")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except ExpiredSignatureError:
        raise Exception("Token expirado")
    except InvalidTokenError:
        raise Exception("Token inválido")
