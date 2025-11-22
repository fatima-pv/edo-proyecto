"""
Handlers de gestión de pedidos
Incluye creación, consulta y actualización de pedidos
"""
import json
import os
import uuid
import time
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

from src.utils.responses import (
    success_response, error_response, unauthorized_response,
    forbidden_response, not_found_response, server_error_response
)
from src.utils.auth_helper import get_user_from_token


# Inicializar clientes AWS
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')

users_table = dynamodb.Table(os.environ['USERS_TABLE'])
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])


def decimal_to_float(obj):
    """Convierte objetos Decimal de DynamoDB a float para JSON"""
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def create_order(event, context):
    """
    Handler para crear un nuevo pedido
    Solo accesible por usuarios con rol CLIENTE
    
    Input: { items: Array, total: number, customer_info: object, tenant_id: string }
    Output: { order_id: string, status: string, execution_arn: string }
    
    Args:
        event (dict): Evento de API Gateway
        context (object): Contexto de Lambda
    
    Returns:
        dict: Respuesta HTTP con el pedido creado
    """
    try:
        # Obtener usuario del token
        user = get_user_from_token(event)
        if not user:
            return unauthorized_response()
        
        # Parsear body
        if not event.get('body'):
            return error_response('Body requerido', 400)
        
        body = json.loads(event['body'])
        items = body.get('items', [])
        total = body.get('total')
        customer_info = body.get('customer_info', {})
        tenant_id = body.get('tenant_id', '')
        
        # Validar campos requeridos
        if not items or total is None or not tenant_id:
            return error_response('items, total y tenant_id son requeridos', 400)
        
        # Generar IDs
        order_id = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)  # Milisegundos
        
        # Crear objeto pedido
        order = {
            'tenant_id': tenant_id,
            'order_id': order_id,
            'customer_email': user['email'],
            'items': items,
            'total': Decimal(str(total)),  # DynamoDB requiere Decimal para números
            'customer_info': customer_info,
            'status': 'RECEIVED',
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Guardar en DynamoDB
        try:
            orders_table.put_item(Item=order)
        except ClientError as e:
            print(f"Error al guardar pedido en DynamoDB: {e}")
            return server_error_response('Error al crear pedido')
        
        # Preparar input para Step Function
        execution_input = {
            'order_id': order_id,
            'tenant_id': tenant_id,
            'customer_email': user['email'],
            'items': items,
            'total': float(total)
        }
        
        # Iniciar Step Function
        try:
            execution = stepfunctions.start_execution(
                stateMachineArn=os.environ['STATE_MACHINE_ARN'],
                name=f"order-{order_id}-{timestamp}",
                input=json.dumps(execution_input)
            )
            execution_arn = execution['executionArn']
        except ClientError as e:
            print(f"Error al iniciar Step Function: {e}")
            # El pedido ya fue creado, así que solo logueamos el error
            execution_arn = 'ERROR'
        
        return success_response({
            'message': 'Pedido creado exitosamente',
            'order_id': order_id,
            'status': 'RECEIVED',
            'execution_arn': execution_arn
        }, 201)
    
    except json.JSONDecodeError:
        return error_response('JSON inválido en el body', 400)
    
    except Exception as e:
        print(f"Error inesperado en create_order: {str(e)}")
        import traceback
        traceback.print_exc()
        return server_error_response(f'Error al crear pedido: {str(e)}')


def get_orders(event, context):
    """
    Handler para obtener pedidos
    
    - CLIENTE: Solo sus propios pedidos
    - STAFF: Todos los pedidos activos de su tenant_id
    
    Output: { orders: Array<Order>, role: string }
    
    Args:
        event (dict): Evento de API Gateway
        context (object): Contexto de Lambda
    
    Returns:
        dict: Respuesta HTTP con lista de pedidos
    """
    try:
        # Obtener usuario del token
        user = get_user_from_token(event)
        if not user:
            return unauthorized_response()
        
        # Obtener información completa del usuario
        try:
            user_response = users_table.get_item(Key={'email': user['email']})
        except ClientError as e:
            print(f"Error al consultar usuario: {e}")
            return server_error_response('Error al consultar usuario')
        
        if 'Item' not in user_response:
            return not_found_response('Usuario no encontrado')
        
        current_user = user_response['Item']
        role = current_user.get('role', 'CLIENTE')
        tenant_id = current_user.get('tenant_id', '')
        
        # Consultar pedidos según el rol
        try:
            if role == 'STAFF':
                # Staff: Todos los pedidos del tenant
                response = orders_table.query(
                    KeyConditionExpression='tenant_id = :tenant_id',
                    ExpressionAttributeValues={
                        ':tenant_id': tenant_id
                    }
                )
            else:
                # Cliente: Solo sus propios pedidos
                # Nota: Esto requiere scan con filtro, no es óptimo para producción
                # En producción, considerar un GSI con customer_email como PK
                response = orders_table.query(
                    KeyConditionExpression='tenant_id = :tenant_id',
                    FilterExpression='customer_email = :email',
                    ExpressionAttributeValues={
                        ':tenant_id': tenant_id,
                        ':email': user['email']
                    }
                )
            
            orders = response.get('Items', [])
            
            # Convertir Decimals a float para JSON
            orders = decimal_to_float(orders)
            
        except ClientError as e:
            print(f"Error al consultar pedidos: {e}")
            return server_error_response('Error al consultar pedidos')
        
        return success_response({
            'orders': orders,
            'role': role,
            'count': len(orders)
        })
    
    except Exception as e:
        print(f"Error inesperado en get_orders: {str(e)}")
        import traceback
        traceback.print_exc()
        return server_error_response(f'Error al obtener pedidos: {str(e)}')


def update_order_step(event, context):
    """
    Handler para avanzar el Step Function usando el callback pattern
    Solo accesible por usuarios con rol STAFF
    
    CALLBACK PATTERN:
    1. El Step Function genera un taskToken cuando llega a un estado waitForTaskToken
    2. Ese token se almacena en DynamoDB junto con el pedido
    3. El staff llama a este endpoint con el taskToken
    4. Esta función ejecuta SendTaskSuccess para desbloquear el Step Function
    
    Input: { order_id: string, tenant_id: string, task_token: string, step: string, notes?: string }
    Output: { message: string, order_id: string, new_status: string }
    
    Args:
        event (dict): Evento de API Gateway
        context (object): Contexto de Lambda
    
    Returns:
        dict: Respuesta HTTP confirmando la actualización
    """
    try:
        # Obtener usuario del token
        user = get_user_from_token(event)
        if not user:
            return unauthorized_response()
        
        # Parsear body
        if not event.get('body'):
            return error_response('Body requerido', 400)
        
        body = json.loads(event['body'])
        order_id = body.get('order_id', '')
        tenant_id = body.get('tenant_id', '')
        task_token = body.get('task_token', '')
        step = body.get('step', '')
        notes = body.get('notes', '')
        
        # Validar campos requeridos
        if not all([order_id, tenant_id, task_token, step]):
            return error_response('order_id, tenant_id, task_token y step son requeridos', 400)
        
        # Verificar que el usuario sea STAFF
        try:
            user_response = users_table.get_item(Key={'email': user['email']})
        except ClientError as e:
            print(f"Error al consultar usuario: {e}")
            return server_error_response('Error al verificar permisos')
        
        if 'Item' not in user_response:
            return not_found_response('Usuario no encontrado')
        
        current_user = user_response['Item']
        if current_user.get('role') != 'STAFF':
            return forbidden_response('Solo STAFF puede avanzar pedidos')
        
        # Actualizar pedido en DynamoDB
        timestamp = int(time.time() * 1000)
        try:
            orders_table.update_item(
                Key={
                    'tenant_id': tenant_id,
                    'order_id': order_id
                },
                UpdateExpression='SET #status = :status, updated_at = :timestamp, updated_by = :user, notes = :notes',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': step,
                    ':timestamp': timestamp,
                    ':user': user['email'],
                    ':notes': notes
                }
            )
        except ClientError as e:
            print(f"Error al actualizar pedido: {e}")
            return server_error_response('Error al actualizar pedido')
        
        # CALLBACK PATTERN: Enviar éxito al Step Function
        output = {
            'order_id': order_id,
            'step': step,
            'completed_by': user['email'],
            'completed_at': timestamp,
            'notes': notes
        }
        
        try:
            stepfunctions.send_task_success(
                taskToken=task_token,
                output=json.dumps(output)
            )
        except ClientError as e:
            print(f"Error al enviar task success: {e}")
            # El pedido ya fue actualizado, pero el Step Function puede fallar
            return error_response(f'Pedido actualizado pero error en workflow: {str(e)}', 500)
        
        return success_response({
            'message': 'Pedido avanzado exitosamente',
            'order_id': order_id,
            'new_status': step
        })
    
    except json.JSONDecodeError:
        return error_response('JSON inválido en el body', 400)
    
    except Exception as e:
        print(f"Error inesperado en update_order_step: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Si hay error, intentar enviar falla al Step Function
        if 'task_token' in locals() and task_token:
            try:
                stepfunctions.send_task_failure(
                    taskToken=task_token,
                    error='OrderUpdateError',
                    cause=str(e)
                )
            except Exception as sf_error:
                print(f"Error al enviar task failure: {sf_error}")
        
        return server_error_response(f'Error al avanzar pedido: {str(e)}')
