import json
import boto3
import uuid
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ['TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)

def registrar_compra(event, context):
    try:
        body = json.loads(event['body'])

        tenant_id = body['tenant_id']
        usuario_id = body['usuario_id']
        curso_id = body['curso_id']
        nombre_curso = body['nombre_curso']
        monto_pagado = body['monto_pagado']

        if not all([tenant_id, usuario_id, curso_id, nombre_curso, monto_pagado]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Datos incompletos'})
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
        tenant_id = event['pathParameters']['tenant_id']
        usuario_id = event['pathParameters']['usuario_id']

        pk = f'{tenant_id}#{usuario_id}'

        response = table.query(
            KeyConditionExpression=Key('pk').eq(pk)
        )

        compras = response.get('Items', [])

        return {
            'statusCode': 200,
            'body': json.dumps({'compras': compras})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
