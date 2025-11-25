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
            'deliveryType': data.get('deliveryType', 'DELIVERY'),  # DELIVERY o PICKUP
            'status': 'CONFIRMADO',
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
        
        # Obtener datos del cliente (puede estar anidado o plano dependiendo de la versión)
        customer_data = order.get('customer', {})
        customer_name = customer_data.get('name') if isinstance(customer_data, dict) else order.get('customerName', 'Cliente')
        address = customer_data.get('address') if isinstance(customer_data, dict) else order.get('address', '')

        # Retornar información completa para el tracking
        public_data = {
            'orderId': order['orderId'],
            'status': order['status'],
            'receiptUrl': order.get('receiptUrl', ''),
            'createdAt': order.get('createdAt', ''),
            'deliveryType': order.get('deliveryType', 'RECOJO'),
            'customerName': customer_name,
            'total': order.get('total', 0),
            'items': order.get('items', []),
            'address': address
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
        valid_statuses = ['CONFIRMADO', 'EN_PREPARACION', 'LISTO_PARA_RETIRAR', 'EN_CAMINO', 'ENTREGADO']
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

def processKitchen(event, context):
    """
    Procesa el pedido en cocina y actualiza estado a EN_PREPARACION
    Puede ser llamado por:
    1. Step Functions (guarda taskToken)
    2. HTTP POST (envía task success y avanza workflow)
    """
    try:
        # Caso 1: Llamado por Step Functions (tiene taskToken)
        if 'taskToken' in event:
            order_id = event['orderId']
            task_token = event['taskToken']
            
            # Guardar taskToken en DynamoDB
            orders_table.update_item(
                Key={'orderId': order_id},
                UpdateExpression='SET taskToken = :token',
                ExpressionAttributeValues={
                    ':token': task_token
                }
            )
            
            return {'message': 'Task token saved, waiting for HTTP call'}
        
        # Caso 2: Llamado por HTTP (avanza el workflow)
        order_id = event['pathParameters']['orderId']
        
        # Obtener el taskToken guardado
        response = orders_table.get_item(Key={'orderId': order_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Pedido no encontrado'})
            }
        
        order = response['Item']
        task_token = order.get('taskToken', '')
        
        # Actualizar estado a EN_PREPARACION
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, taskToken = :empty, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'EN_PREPARACION',
                ':empty': '',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        # Si hay taskToken, enviar success al Step Functions
        if task_token:
            try:
                sfn_client.send_task_success(
                    taskToken=task_token,
                    output=json.dumps({'orderId': order_id, 'status': 'EN_PREPARACION'})
                )
            except Exception as e:
                print(f"Error sending task success: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Pedido en preparación',
                'orderId': order_id,
                'status': 'EN_PREPARACION'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def processPacking(event, context):
    """
    Marca el pedido como listo para retirar
    Puede ser llamado por Step Functions o HTTP
    """
    try:
        # Caso 1: Llamado por Step Functions
        if 'taskToken' in event:
            order_id = event['orderId']
            task_token = event['taskToken']
            
            orders_table.update_item(
                Key={'orderId': order_id},
                UpdateExpression='SET taskToken = :token',
                ExpressionAttributeValues={':token': task_token}
            )
            return {'message': 'Task token saved'}
        
        # Caso 2: Llamado por HTTP
        order_id = event['pathParameters']['orderId']
        response = orders_table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Pedido no encontrado'})
            }
        
        order = response['Item']
        task_token = order.get('taskToken', '')
        
        # Actualizar estado
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, taskToken = :empty, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'LISTO_PARA_RETIRAR',
                ':empty': '',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        # Enviar success al Step Functions
        if task_token:
            try:
                sfn_client.send_task_success(
                    taskToken=task_token,
                    output=json.dumps({'orderId': order_id, 'status': 'LISTO_PARA_RETIRAR', 'deliveryType': order.get('deliveryType', 'DELIVERY')})
                )
            except Exception as e:
                print(f"Error sending task success: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Pedido listo para retirar',
                'orderId': order_id,
                'status': 'LISTO_PARA_RETIRAR'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def processDelivery(event, context):
    """
    Marca el pedido como en camino (solo para DELIVERY)
    Puede ser llamado por Step Functions o HTTP
    """
    try:
        # Caso 1: Llamado por Step Functions
        if 'taskToken' in event:
            order_id = event['orderId']
            task_token = event['taskToken']
            
            orders_table.update_item(
                Key={'orderId': order_id},
                UpdateExpression='SET taskToken = :token',
                ExpressionAttributeValues={':token': task_token}
            )
            return {'message': 'Task token saved'}
        
        # Caso 2: Llamado por HTTP
        order_id = event['pathParameters']['orderId']
        response = orders_table.get_item(Key={'orderId': order_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Pedido no encontrado'})
            }
        
        order = response['Item']
        
        # Verificar que sea DELIVERY
        if order.get('deliveryType') != 'DELIVERY':
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Este pedido es PICKUP, no puede estar en camino'})
            }
        
        task_token = order.get('taskToken', '')
        
        # Actualizar estado
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, taskToken = :empty, updatedAt = :updated',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'EN_CAMINO',
                ':empty': '',
                ':updated': datetime.utcnow().isoformat()
            }
        )
        
        # Enviar success al Step Functions
        if task_token:
            try:
                sfn_client.send_task_success(
                    taskToken=task_token,
                    output=json.dumps({'orderId': order_id, 'status': 'EN_CAMINO'})
                )
            except Exception as e:
                print(f"Error sending task success: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Pedido en camino',
                'orderId': order_id,
                'status': 'EN_CAMINO'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
