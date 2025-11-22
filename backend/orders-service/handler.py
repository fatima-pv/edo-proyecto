import json
import boto3
import uuid
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table('EdoOrdersTable')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def createOrder(event, context):
    try:
        data = json.loads(event['body'])
        
        order = {
            'orderId': str(uuid.uuid4()),
            'customerName': data['customerName'],
            'items': data['items'],
            'total': Decimal(str(data['total'])),
            'status': 'pending'
        }
        
        orders_table.put_item(Item=order)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({'message': 'Order created', 'orderId': order['orderId']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def listOrders(event, context):
    try:
        response = orders_table.scan()
        items = response.get('Items', [])
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(items, cls=DecimalEncoder)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
