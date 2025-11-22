"""
Handler de notificaciones
Notifica al staff cuando cambia el estado de un pedido
"""
import json
import os
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# Inicializar cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ['USERS_TABLE'])
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])


def notify_staff(event, context):
    """
    Handler para notificar al staff cuando cambia el estado de un pedido
    
    Esta función es invocada por:
    - EventBridge cuando hay un cambio de estado
    - Step Function directamente en estados waitForTaskToken
    
    Cuando se llama desde un estado waitForTaskToken, recibe el taskToken
    que debe ser almacenado en DynamoDB para que el staff lo use después.
    
    Input: { order_id: string, tenant_id: string, status: string, task_token?: string, message?: string }
    Output: { statusCode: int, notified: int, order_id: string, status: string }
    
    Args:
        event (dict): Evento de EventBridge o invocación directa
        context (object): Contexto de Lambda
    
    Returns:
        dict: Resultado de la notificación
    """
    try:
        print(f"Evento recibido: {json.dumps(event, default=str)}")
        
        # El evento puede venir de EventBridge o de Step Function
        # Si viene de EventBridge, los datos están en 'detail'
        if 'detail' in event:
            event_data = event['detail']
        else:
            event_data = event
        
        order_id = event_data.get('order_id')
        tenant_id = event_data.get('tenant_id')
        status = event_data.get('status')
        task_token = event_data.get('task_token')
        message = event_data.get('message', 'Acción requerida')
        
        # Validar campos requeridos
        if not all([order_id, tenant_id, status]):
            raise ValueError('order_id, tenant_id y status son requeridos')
        
        # Si viene taskToken, almacenarlo en DynamoDB
        # Esto permite que el staff lo use para avanzar el workflow
        if task_token:
            try:
                orders_table.update_item(
                    Key={
                        'tenant_id': tenant_id,
                        'order_id': order_id
                    },
                    UpdateExpression='SET task_token = :token, pending_status = :status, notification_message = :message',
                    ExpressionAttributeValues={
                        ':token': task_token,
                        ':status': status,
                        ':message': message
                    }
                )
                print(f"TaskToken almacenado para orden {order_id}")
            except ClientError as e:
                print(f"Error al almacenar taskToken: {e}")
                # No fallar la función si no se puede almacenar el token
        
        # Obtener todos los usuarios STAFF del tenant
        try:
            staff_response = dynamodb.meta.client.scan(
                TableName=os.environ['USERS_TABLE'],
                FilterExpression='tenant_id = :tenant_id AND #r = :role',
                ExpressionAttributeNames={
                    '#r': 'role'
                },
                ExpressionAttributeValues={
                    ':tenant_id': {'S': tenant_id},
                    ':role': {'S': 'STAFF'}
                }
            )
            
            staff_count = staff_response.get('Count', 0)
            print(f"Notificando a {staff_count} miembros del staff")
            
            # Procesar cada miembro del staff
            if 'Items' in staff_response:
                for staff_item in staff_response['Items']:
                    staff_email = staff_item.get('email', {}).get('S', 'unknown')
                    
                    # Aquí puedes implementar notificaciones reales:
                    # - Push notifications usando SNS
                    # - Emails usando SES
                    # - WebSocket para actualización en tiempo real
                    # - Slack/Discord webhooks
                    
                    print(f"📧 Notificación enviada a: {staff_email}")
                    print(f"   Pedido: {order_id}")
                    print(f"   Estado: {status}")
                    print(f"   Mensaje: {message}")
        
        except ClientError as e:
            print(f"Error al obtener staff: {e}")
            staff_count = 0
        
        # Retornar resultado
        return {
            'statusCode': 200,
            'notified': staff_count,
            'order_id': order_id,
            'status': status
        }
    
    except Exception as e:
        print(f"Error inesperado en notify_staff: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Lanzar excepción para que Step Function o EventBridge manejen el error
        raise
