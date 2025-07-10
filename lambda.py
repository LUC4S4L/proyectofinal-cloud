import json
import boto3
import uuid
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ['TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)

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
