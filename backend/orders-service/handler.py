import json
import boto3
import uuid
import os
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])
events_client = boto3.client('events')
sfn_client = boto3.client('stepfunctions')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def createOrder(event, context):
    """
    Crea un pedido, lo guarda en DynamoDB, emite evento a EventBridge e inicia Step Function
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
            'taskToken': '',  # Se llenará en el workflow
            'receiptUrl': '',  # Se llenará después
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
                            'deliveryType': order['deliveryType']
                        }),
                        'EventBusName': os.environ['ORDER_BUS_NAME']
                    }
                ]
            )
        except Exception as e:
            print(f"Error emitting event: {str(e)}")
        
        # Iniciar Step Function
        try:
            state_machine_arn = os.environ['STATE_MACHINE_ARN']
            sfn_client.start_execution(
                stateMachineArn=state_machine_arn,
                input=json.dumps({'orderId': order_id})
            )
        except Exception as e:
            print(f"Error starting workflow: {str(e)}")
        
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

def advanceOrder(event, context):
    """
    Avanza el estado del pedido en el workflow
    POST /orders/advance
    Body: { "orderId": "..." }
    """
    try:
        data = json.loads(event['body'])
        order_id = data['orderId']
        
        # Obtener el pedido
        response = orders_table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Pedido no encontrado'})
            }
        
        order = response['Item']
        task_token = order.get('taskToken', '')
        
        if not task_token:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No hay task token disponible'})
            }
        
        # Enviar success al Step Function
        sfn_client.send_task_success(
            taskToken=task_token,
            output=json.dumps({'orderId': order_id})
        )
        
        # Actualizar estado en DynamoDB
        current_status = order['status']
        next_status = {
            'RECIBIDO': 'EN_COCINA',
            'EN_COCINA': 'EMPACANDO',
            'EMPACANDO': 'EN_DELIVERY',
            'EN_DELIVERY': 'COMPLETADO'
        }.get(current_status, 'COMPLETADO')
        
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, taskToken = :empty, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': next_status,
                ':empty': '',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Pedido avanzado',
                'newStatus': next_status
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

# Funciones para Step Functions (waitForTaskToken)

def waitForKitchen(event, context):
    """
    Guarda el taskToken y espera a que cocina avance el pedido
    """
    try:
        order_id = event['orderId']
        task_token = event['taskToken']
        
        # Guardar taskToken en DynamoDB
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET taskToken = :token, #status = :status, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':token': task_token,
                ':status': 'EN_COCINA',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        # No retornamos nada, el workflow queda pausado hasta que se llame advanceOrder
        return {'message': 'Waiting for kitchen'}
    except Exception as e:
        print(f"Error in waitForKitchen: {str(e)}")
        raise

def waitForPacking(event, context):
    """
    Guarda el taskToken y espera a que empaque avance el pedido
    """
    try:
        order_id = event['orderId']
        task_token = event['taskToken']
        
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET taskToken = :token, #status = :status, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':token': task_token,
                ':status': 'EMPACANDO',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        return {'message': 'Waiting for packing'}
    except Exception as e:
        print(f"Error in waitForPacking: {str(e)}")
        raise

def waitForDelivery(event, context):
    """
    Guarda el taskToken y espera a que delivery avance el pedido
    """
    try:
        order_id = event['orderId']
        task_token = event['taskToken']
        
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET taskToken = :token, #status = :status, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':token': task_token,
                ':status': 'EN_DELIVERY',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        return {'message': 'Waiting for delivery'}
    except Exception as e:
        print(f"Error in waitForDelivery: {str(e)}")
        raise
