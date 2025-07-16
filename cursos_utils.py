import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

CURSOS_API_URL = os.environ.get('CURSOS_API_URL')

def _get_session_with_retries():
    """
    Crea una sesión de requests con reintentos automáticos
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def obtener_curso(curso_id, token):
    """
    Obtiene la información de un curso desde la API de Cursos
    """
    if not CURSOS_API_URL:
        raise Exception("CURSOS_API_URL no está configurada")
    
    if not curso_id:
        raise Exception("curso_id es requerido")
    
    if not token:
        raise Exception("Token es requerido")
    
    # Asegurar que el token tenga el prefijo Bearer
    if not token.startswith('Bearer '):
        token = f'Bearer {token}'
    
    try:
        session = _get_session_with_retries()
        
        response = session.get(
            f"{CURSOS_API_URL}/cursos/buscar/{curso_id}",
            headers={
                "Authorization": token,
                "Content-Type": "application/json"
            },
            timeout=10  # Timeout de 10 segundos
        )
        
        if response.status_code == 404:
            return None
        
        if response.status_code != 200:
            print(f"Error en API Cursos - Status: {response.status_code}, Response: {response.text}")
            return None
        
        data = response.json()
        curso = data.get("curso")
        
        if not curso:
            print("La respuesta de la API no contiene el campo 'curso'")
            return None
            
        return curso
        
    except requests.exceptions.Timeout:
        print("Timeout al conectar con la API de Cursos")
        return None
    except requests.exceptions.ConnectionError:
        print("Error de conexión con la API de Cursos")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error en request a API Cursos: {str(e)}")
        return None
    except Exception as e:
        print(f"Error inesperado al obtener curso: {str(e)}")
        return None

def validar_curso_pertenece_tenant(curso_data, tenant_id):
    """
    Valida que un curso pertenezca al tenant especificado
    """
    if not curso_data:
        return False
    
    curso_tenant_id = curso_data.get('tenant_id')
    return curso_tenant_id == tenant_id
