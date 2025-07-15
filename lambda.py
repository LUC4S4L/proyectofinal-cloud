import json
import boto3
import uuid
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from auth_utils import validar_token
from cursos_utils import obtener_curso

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ['TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def registrar_compra(event, context):
    try:
        token = event['headers'].get('Authorization')
        payload = validar_token(token)

        body = json.loads(event['body'])

        tenant_id = payload['tenant_id']
        usuario_id = payload['username']
        curso_id = body['curso_id']
        monto_pagado = body['monto_pagado']

        if not all([tenant_id, usuario_id, curso_id, monto_pagado]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Datos incompletos'})
            }

        curso = obtener_curso(curso_id)
        if not curso:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Curso no encontrado'})
            }

        nombre_curso = curso.get('curso_datos', {}).get('nombre', 'Nombre no disponible')

        compra_id = str(uuid.uuid4())
        fecha_compra = datetime.utcnow().isoformat()

        item = {
            'tenant_id': tenant_id,
            'usuario_id': usuario_id,
            'curso_id': curso_id,
            'nombre_curso': nombre_curso,
            'monto_pagado': Decimal(str(monto_pagado)),
            'fecha_compra': fecha_compra,
            'compra_id': compra_id
        }

        table.put_item(Item=item)

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Compra de curso registrada exitosamente',
                'compra_id': compra_id
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
def listar_compras(event, context):
    try:
        token = event['headers'].get('Authorization')
        payload = validar_token(token)

        tenant_id = payload['tenant_id']
        usuario_id = payload['username']

        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id)
        )
        compras = response.get('Items', [])

        compras_usuario = [c for c in compras if c['usuario_id'] == usuario_id]

        return {
            'statusCode': 200,
            'body': json.dumps({'compras': compras_usuario}, default=decimal_default)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def procesar_cambios(event, context):
    for record in event['Records']:
        evento = record['eventName']
        nuevo = record.get('dynamodb', {}).get('NewImage', {})
        anterior = record.get('dynamodb', {}).get('OldImage', {})

        print(f"Evento: {evento}")
        print(f"Nuevo valor: {json.dumps(nuevo, default=str)}")
        print(f"Valor anterior: {json.dumps(anterior, default=str)}")
