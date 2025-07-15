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

        tenant_id = payload['tenant_id']
        usuario_id = payload['username']

        body = json.loads(event['body'])
        curso_id = body.get('curso_id')

        if not curso_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Falta curso_id'})
            }

        # Obtener curso desde API externa
        curso = obtener_curso(curso_id, token)

        if curso['tenant_id'] != tenant_id:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'El curso no pertenece a tu universidad'})
            }

        nombre_curso = curso['curso_datos']['nombre']
        monto_pagado = Decimal(str(curso['curso_datos']['precio']))

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
