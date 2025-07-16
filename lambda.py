import json
import boto3
import uuid
import os
import requests
from datetime import datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from auth_utils import validar_token

TABLE_NAME = os.environ['TABLE_NAME']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

CURSOS_API_URL = os.environ['CURSOS_API_URL']

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
        curso_id = body.get('curso_id')

        if not curso_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'curso_id es obligatorio'})
            }

        response = requests.get(
            f"{CURSOS_API_URL}/cursos/buscar/{curso_id}",
            headers={'Authorization': token}
        )

        if response.status_code != 200:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Curso no encontrado en API Cursos'})
            }

        curso_data = response.json().get('curso')
        if not curso_data or curso_data.get('tenant_id') != tenant_id:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Curso no pertenece al tenant'})
            }

        nombre_curso = curso_data.get('curso_datos', {}).get('nombre', 'Curso sin nombre')
        monto_pagado = body.get('monto_pagado')

        try:
            monto_pagado = Decimal(str(monto_pagado)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, TypeError):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Monto inválido'})
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
            'body': json.dumps({
                'message': 'Compra registrada exitosamente',
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
            KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('usuario_id').eq(usuario_id)
        )

        compras = response.get('Items', [])
        compras_completas = []

        for compra in compras:
            curso_id = compra.get('curso_id')
            try:
                curso_response = requests.get(
                    f"{CURSOS_API_URL}/cursos/buscar/{curso_id}",
                    headers={'Authorization': token}
                )
                if curso_response.status_code == 200:
                    curso_data = curso_response.json().get('curso', {})
                    compra['curso_detalle'] = curso_data.get('curso_datos', {})
                else:
                    compra['curso_detalle'] = {'error': 'No se pudo obtener el detalle del curso'}
            except Exception as e:
                compra['curso_detalle'] = {'error': str(e)}

            compras_completas.append(compra)

        return {
            'statusCode': 200,
            'body': json.dumps({'compras': compras_completas}, default=decimal_default)
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
