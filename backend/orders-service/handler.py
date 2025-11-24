import json
import boto3
import uuid
import os
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])
events_client = boto3.client('events')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def createOrder(event, context):
    """
    Crea un pedido, lo guarda en DynamoDB y emite evento a EventBridge
    """
    try:
        data = json.loads(event['body'])
        
        # Generar orderId único
        order_id = str(uuid.uuid4())
        
        # Construir objeto de pedido completo
        order = {
            'orderId': order_id,
            'customer': {
                'name': data.get('customerName', ''),
                'dni': data.get('dni', ''),
                'email': data.get('email', ''),
                'address': data.get('address', '')
            },
            'items': data['items'],
            'total': Decimal(str(data['total'])),
            'deliveryType': data.get('deliveryType', 'RECOJO'),  # DELIVERY o RECOJO
            'status': 'RECIBIDO',
            'receiptUrl': '',  # Se llenará después por receipt-service
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # Guardar en DynamoDB
        orders_table.put_item(Item=order)
        
        # Emitir evento a EventBridge
        try:
            events_client.put_events(
                Entries=[
                    {
                        'Source': 'edo.orders',
                        'DetailType': 'OrderCreated',
                        'Detail': json.dumps({
                            'orderId': order_id,
                            'customer': order['customer'],
                            'total': float(order['total']),
                            'deliveryType': order['deliveryType'],
                            'items': data['items']
                        }),
                        'EventBusName': os.environ['ORDER_BUS_NAME']
                    }
                ]
            )
        except Exception as e:
            print(f"Error emitting event: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'message': 'Pedido creado exitosamente',
                'orderId': order_id
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def listOrders(event, context):
    """
    Lista todos los pedidos (para cocina)
    """
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

def getOrder(event, context):
    """
    Obtiene un pedido específico por orderId (para tracking público)
    GET /orders/{orderId}
    """
    try:
        order_id = event['pathParameters']['orderId']
        
        response = orders_table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Pedido no encontrado'})
            }
        
        order = response['Item']
        
        # Retornar solo información pública
        public_data = {
            'orderId': order['orderId'],
            'status': order['status'],
            'receiptUrl': order.get('receiptUrl', ''),
            'createdAt': order.get('createdAt', ''),
            'deliveryType': order.get('deliveryType', 'RECOJO')
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps(public_data, cls=DecimalEncoder)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def updateOrderStatus(event, context):
    """
    Actualiza el estado del pedido (para cocina)
    PUT /orders/{orderId}/status
    Body: { "status": "EN_COCINA" }
    """
    try:
        order_id = event['pathParameters']['orderId']
        data = json.loads(event['body'])
        new_status = data['status']
        
        # Validar estados permitidos
        valid_statuses = ['RECIBIDO', 'EN_COCINA', 'EMPACANDO', 'EN_DELIVERY', 'COMPLETADO']
        if new_status not in valid_statuses:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'Estado inválido. Debe ser uno de: {valid_statuses}'})
            }
        
        # Actualizar estado en DynamoDB
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': new_status,
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,PUT'
            },
            'body': json.dumps({
                'message': 'Estado actualizado',
                'orderId': order_id,
                'newStatus': new_status
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
