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
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Access-Control-Allow-Credentials': 'false'
    }

def registrar_compra(event, context):
    try:
        # Manejar preflight OPTIONS request
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'OK'})
            }

        token = event['headers'].get('Authorization')
        payload = validar_token(token)

        body = json.loads(event['body'])

        tenant_id = payload['tenant_id']
        usuario_id = payload['username']
        curso_id = body.get('curso_id')

        if not curso_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'curso_id es obligatorio'})
            }

        # Usar la función de cursos_utils
        curso_data = obtener_curso(curso_id, token)
        
        if not curso_data:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Curso no encontrado en API Cursos'})
            }

        # Validar que el curso pertenece al tenant
        if not validar_curso_pertenece_tenant(curso_data, tenant_id):
            return {
                'statusCode': 403,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Curso no pertenece al tenant'})
            }

        nombre_curso = curso_data.get('curso_datos', {}).get('nombre', 'Curso sin nombre')
        monto_pagado = body.get('monto_pagado')

        if monto_pagado is None:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'monto_pagado es obligatorio'})
            }

        try:
            monto_pagado = Decimal(str(monto_pagado)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if monto_pagado <= 0:
                raise ValueError("El monto debe ser mayor a 0")
        except (InvalidOperation, TypeError, ValueError) as e:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': f'Monto inválido: {str(e)}'})
            }

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

        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
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
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Error interno del servidor: {str(e)}'})
        }

def listar_compras(event, context):
    try:
        # Manejar preflight OPTIONS request
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({'message': 'OK'})
            }

        token = event['headers'].get('Authorization')
        payload = validar_token(token)

        tenant_id = payload['tenant_id']
        usuario_id = payload['username']

        # Consulta corregida usando ambas claves
        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('usuario_id').eq(usuario_id)
        )

        compras = response.get('Items', [])
        compras_completas = []

        for compra in compras:
            curso_id = compra.get('curso_id')
            
            # Usar la función de cursos_utils para obtener detalles del curso
            curso_data = obtener_curso(curso_id, token)
            
            if curso_data:
                compra['curso_detalle'] = curso_data.get('curso_datos', {})
            else:
                compra['curso_detalle'] = {'error': 'No se pudo obtener el detalle del curso'}

            compras_completas.append(compra)

        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'compras': compras_completas,
                'total_compras': len(compras_completas)
            }, default=decimal_default)
        }

    except Exception as e:
        print(f"Error en listar_compras: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Error interno del servidor: {str(e)}'})
        }

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
            
            # Aquí puedes agregar lógica adicional para procesar los cambios
            # Por ejemplo: enviar notificaciones, actualizar caches, etc.
            
    except Exception as e:
        print(f"Error procesando cambios DynamoDB: {str(e)}")
        # No lanzar la excepción para evitar que el stream se bloquee
        return
    except Exception as e:
        print(f"Error procesando cambios DynamoDB: {str(e)}")
        # No lanzar la excepción para evitar que el stream se bloquee
        return
