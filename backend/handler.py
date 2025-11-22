import json
import boto3
import uuid
from decimal import Decimal

# Helper class to convert DynamoDB Decimal types to JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
products_table = dynamodb.Table('EdoProductsTable')
orders_table = dynamodb.Table('EdoOrdersTable')

def create_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def createProduct(event, context):
    try:
        data = json.loads(event['body'])
        
        # Basic validation
        if 'name' not in data or 'price' not in data:
            return create_response(400, {'error': 'Missing name or price'})

        product_id = str(uuid.uuid4())
        
        item = {
            'id': product_id,
            'name': data['name'],
            'price': Decimal(str(data['price'])), # Store as Decimal
            'description': data.get('description', ''),
            'category': data.get('category', 'General'), # Default to 'General'
            'imageUrl': data.get('imageUrl', ''), # Optional image URL
            'maxSelections': int(data.get('maxSelections', 4)) # Default to 4 for combos
        }
        
        products_table.put_item(Item=item)
        
        return create_response(201, item)
    except Exception as e:
        print(e)
        return create_response(500, {'error': str(e)})

def getProducts(event, context):
    try:
        response = products_table.scan()
        items = response.get('Items', [])
        return create_response(200, items)
    except Exception as e:
        print(e)
        return create_response(500, {'error': str(e)})

def createOrder(event, context):
    try:
        data = json.loads(event['body'])
        
        order_id = str(uuid.uuid4())
        
        # Expecting: items (list), total, salsas (list), customerName (optional)
        item = {
            'orderId': order_id,
            'items': data.get('items', []),
            'total': Decimal(str(data.get('total', 0))),
            'salsas': data.get('salsas', []),
            'status': 'RECIBIDO',
            'customerName': data.get('customerName', 'Cliente'),
            'createdAt': str(uuid.uuid1()) # Simple timestamp using uuid1
        }
        
        orders_table.put_item(Item=item)
        
        return create_response(201, item)
    except Exception as e:
        print(e)
        return create_response(500, {'error': str(e)})

def listOrders(event, context):
    try:
        response = orders_table.scan()
        items = response.get('Items', [])
        return create_response(200, items)
    except Exception as e:
        print(e)
        return create_response(500, {'error': str(e)})
