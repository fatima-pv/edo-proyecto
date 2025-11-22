import json
import boto3
import uuid
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
products_table = dynamodb.Table('EdoProductsTable')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def createProduct(event, context):
    try:
        data = json.loads(event['body'])
        
        item = {
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'price': Decimal(str(data['price'])),
            'description': data.get('description', ''),
            'category': data.get('category', 'General'),
            'imageUrl': data.get('imageUrl', ''),
            'maxSelections': int(data.get('maxSelections', 4))
        }
        
        products_table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({'message': 'Product created', 'id': item['id']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def getProducts(event, context):
    try:
        response = products_table.scan()
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
