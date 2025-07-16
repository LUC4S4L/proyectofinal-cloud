import json
import boto3
import uuid
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from auth_utils import validar_token
from cursos_utils import obtener_curso, validar_curso_pertenece_tenant

TABLE_NAME = os.environ['TABLE_NAME']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_cors_headers():
    """Retorna los headers CORS necesarios"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    }

def create_response(status_code, body):
    """Crea una respuesta estándar con headers CORS"""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(body, default=decimal_default) if isinstance(body, dict) else body
    }

def registrar_compra(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {'message': 'OK'})
    
    try:
        token = event['headers'].get('Authorization') or event['headers'].get('authorization')
        if not token:
            return create_response(401, {'error': 'Token de autorización requerido'})

        payload = validar_token(token)
        body = json.loads(event['body'])

        tenant_id = payload['tenant_id']
        usuario_id = payload['username']
        curso_id = body.get('curso_id')

        if not curso_id:
            return create_response(400, {'error': 'curso_id es obligatorio'})

        curso_data = obtener_curso(curso_id, token)
        
        if not curso_data:
            return create_response(404, {'error': 'Curso no encontrado en API Cursos'})

        if not validar_curso_pertenece_tenant(curso_data, tenant_id):
            return create_response(403, {'error': 'Curso no pertenece al tenant'})

        nombre_curso = curso_data.get('curso_datos', {}).get('nombre', 'Curso sin nombre')
        monto_pagado = body.get('monto_pagado')

        if monto_pagado is None:
            return create_response(400, {'error': 'monto_pagado es obligatorio'})

        try:
            monto_pagado = Decimal(str(monto_pagado)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if monto_pagado <= 0:
                raise ValueError("El monto debe ser mayor a 0")
        except (InvalidOperation, TypeError, ValueError) as e:
            return create_response(400, {'error': f'Monto inválido: {str(e)}'})

        compra_id = str(uuid.uuid4())
        fecha_compra = datetime.utcnow().isoformat()

        item = {
            'tenant_id': tenant_id,
            'usuario_id': usuario_id,
            'curso_id': curso_id,
            'nombre_curso': nombre_curso,
            'monto_pagado': monto_pagado,
            'fecha_compra': fecha_compra,
            'compra_id': compra_id
        }

        table.put_item(Item=item)

        return create_response(201, {
            'message': 'Compra registrada exitosamente',
            'compra_id': compra_id,
            'fecha_compra': fecha_compra
        })

    except Exception as e:
        print(f"Error en registrar_compra: {str(e)}")
        return create_response(500, {'error': f'Error interno del servidor: {str(e)}'})

def listar_compras(event, context):
    # Manejar preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {'message': 'OK'})
    
    try:
        token = event['headers'].get('Authorization') or event['headers'].get('authorization')
        if not token:
            return create_response(401, {'error': 'Token de autorización requerido'})

        payload = validar_token(token)

        tenant_id = payload['tenant_id']
        usuario_id = payload['username']

        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('usuario_id').eq(usuario_id)
        )

        compras = response.get('Items', [])
        compras_completas = []

        for compra in compras:
            curso_id = compra.get('curso_id')
            
            curso_data = obtener_curso(curso_id, token)
            
            if curso_data:
                compra['curso_detalle'] = curso_data.get('curso_datos', {})
            else:
                compra['curso_detalle'] = {'error': 'No se pudo obtener el detalle del curso'}

            compras_completas.append(compra)

        return create_response(200, {
            'compras': compras_completas,
            'total_compras': len(compras_completas)
        })

    except Exception as e:
        print(f"Error en listar_compras: {str(e)}")
        return create_response(500, {'error': f'Error interno del servidor: {str(e)}'})

def procesar_cambios(event, context):
    """
    Función para procesar cambios en el DynamoDB Stream
    """
    try:
        for record in event['Records']:
            evento = record['eventName']
            nuevo = record.get('dynamodb', {}).get('NewImage', {})
            anterior = record.get('dynamodb', {}).get('OldImage', {})

            print(f"Evento: {evento}")
            print(f"Nuevo valor: {json.dumps(nuevo, default=str)}")
            print(f"Valor anterior: {json.dumps(anterior, default=str)}")
            
    except Exception as e:
        print(f"Error procesando cambios DynamoDB: {str(e)}")
        return
