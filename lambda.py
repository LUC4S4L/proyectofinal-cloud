import json
import boto3
import uuid
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from auth_utils import validar_token

TABLE_NAME = os.environ['TABLE_NAME']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def registrar_compra(event, context):
    # Headers CORS para TODAS las respuestas
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    # Manejar OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    try:
        # Log para debugging
        print(f"Headers recibidos: {event.get('headers', {})}")
        print(f"Body recibido: {event.get('body', '')}")
        
        token = event['headers'].get('Authorization') or event['headers'].get('authorization')
        if not token:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Token de autorización requerido'})
            }

        payload = validar_token(token)
        body = json.loads(event['body'])

        tenant_id = payload['tenant_id']
        usuario_id = payload['username']
        curso_id = body.get('curso_id')
        monto_pagado = body.get('monto_pagado')

        if not curso_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'curso_id es obligatorio'})
            }

        if monto_pagado is None:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'monto_pagado es obligatorio'})
            }

        try:
            monto_pagado = Decimal(str(monto_pagado)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if monto_pagado <= 0:
                raise ValueError("El monto debe ser mayor a 0")
        except (InvalidOperation, TypeError, ValueError) as e:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': f'Monto inválido: {str(e)}'})
            }

        compra_id = str(uuid.uuid4())
        fecha_compra = datetime.utcnow().isoformat()
        nombre_curso = body.get('nombre_curso', 'Curso sin nombre')

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
        
        print(f"Compra registrada exitosamente: {compra_id}")

        return {
            'statusCode': 201,
            'headers': cors_headers,
            'body': json.dumps({
                'message': 'Compra registrada exitosamente',
                'compra_id': compra_id,
                'fecha_compra': fecha_compra
            })
        }

    except Exception as e:
        print(f"Error en registrar_compra: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f'Error interno: {str(e)}'})
        }

def listar_compras(event, context):
    # Headers CORS para TODAS las respuestas
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    # Manejar OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'OK'})
        }
    
    try:
        print(f"Headers recibidos: {event.get('headers', {})}")
        
        token = event['headers'].get('Authorization') or event['headers'].get('authorization')
        if not token:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Token de autorización requerido'})
            }

        payload = validar_token(token)
        tenant_id = payload['tenant_id']
        usuario_id = payload['username']

        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('usuario_id').eq(usuario_id)
        )

        compras = response.get('Items', [])
        print(f"Compras encontradas: {len(compras)}")

        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'compras': compras,
                'total_compras': len(compras)
            }, default=decimal_default)
        }

    except Exception as e:
        print(f"Error en listar_compras: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f'Error interno: {str(e)}'})
        }

def procesar_cambios(event, context):
    try:
        for record in event['Records']:
            evento = record['eventName']
            print(f"Evento DynamoDB: {evento}")
    except Exception as e:
        print(f"Error procesando cambios: {str(e)}")
        return
