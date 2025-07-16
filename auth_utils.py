import os
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

JWT_SECRET = os.environ.get('JWT_SECRET', 'supersecreto123')

def validar_token(token):
    """
    Valida un token JWT y retorna el payload decodificado
    """
    if not token:
        raise Exception("Token requerido")
    
    # Remover el prefijo 'Bearer ' si existe
    if token.startswith('Bearer '):
        token = token[7:]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        
        # Validar que el payload contenga los campos necesarios
        if 'tenant_id' not in payload or 'username' not in payload:
            raise Exception("Token no contiene información requerida")
            
        return payload
        
    except ExpiredSignatureError:
        raise Exception("Token expirado")
    except InvalidTokenError:
        raise Exception("Token inválido")
    except Exception as e:
        raise Exception(f"Error validando token: {str(e)}")
