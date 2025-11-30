import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

sns_client = boto3.client('sns')
sqs_client = boto3.client('sqs')
ses_client = boto3.client('ses')
dynamodb = boto3.resource('dynamodb')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
QUEUE_URL = os.environ.get('NOTIFICATION_QUEUE_URL')
orders_table = dynamodb.Table(os.environ.get('ORDERS_TABLE', 'EdoOrdersTable'))


def process_notification(event, context):
    """
    Procesa notificaciones desde SQS y las envía por SNS (email)
    Se activa automáticamente cuando llegan mensajes a la cola
    """
    print(f"Processing {len(event['Records'])} notifications")
    
    for record in event['Records']:
        try:
            # Parsear mensaje
            message = json.loads(record['body'])
            
            notification_type = message.get('type')
            order_id = message.get('orderId')
            customer_email = message.get('customerEmail')
            customer_name = message.get('customerName', 'Cliente')
            status = message.get('status')
            
            print(f"Processing notification: {notification_type} for order {order_id}")
            
            # Construir email según el tipo
            subject, body = build_email_content(
                notification_type, 
                order_id, 
                customer_name, 
                status
            )
            
            # Enviar email por SNS
            # Nota: En SNS el destinatario debe estar suscrito al topic
            response = sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=subject,
                Message=body,
                MessageAttributes={
                    'email': {
                        'DataType': 'String',
                        'StringValue': customer_email
                    },
                    'orderType': {
                        'DataType': 'String',
                        'StringValue': notification_type
                    }
                }
            )
            
            print(f"✅ Notification sent to SNS. MessageId: {response['MessageId']}")
            
        except Exception as e:
            print(f"❌ Error processing notification: {str(e)}")
            # El mensaje volverá a la cola para reintento
            raise


def build_email_content(notification_type, order_id, customer_name, status=None):
    """
    Construye el contenido del email según el tipo de notificación
    """
    
    # Emojis y mensajes por tipo
    templates = {
        'ORDER_CREATED': {
            'emoji': '✅',
            'title': 'Pedido Confirmado',
            'message': f'''¡Hola {customer_name}!

Tu pedido ha sido confirmado exitosamente. 🎉

Pedido: {order_id}
Estado: Confirmado

Estamos preparando tu pedido con los ingredientes más frescos.
Te notificaremos cuando cambie de estado.

Ver seguimiento en tiempo real:
https://tu-app.vercel.app/?tracking={order_id}

---
Edo Sushi Bar 🍣
La mejor experiencia japonesa
'''
        },
        'STATUS_UPDATE': {
            'emoji': get_status_emoji(status),
            'title': get_status_title(status),
            'message': f'''¡Hola {customer_name}!

Tu pedido ha sido actualizado. {get_status_emoji(status)}

Pedido: {order_id}
Nuevo estado: {get_status_text(status)}

{get_status_message(status)}

Ver seguimiento en tiempo real:
https://tu-app.vercel.app/?tracking={order_id}

---
Edo Sushi Bar 🍣
La mejor experiencia japonesa
'''
        },
        'ORDER_READY': {
            'emoji': '✅',
            'title': 'Tu Pedido Está Listo',
            'message': f'''¡Hola {customer_name}!

¡Buenas noticias! Tu pedido está listo. ✅

Pedido: {order_id}

Tu pedido está empaquetado y listo para ser retirado o será enviado en breve.

Ver seguimiento:
https://tu-app.vercel.app/?tracking={order_id}

---
Edo Sushi Bar 🍣
La mejor experiencia japonesa
'''
        },
        'ORDER_DELIVERED': {
            'emoji': '🏠',
            'title': '¡Pedido Entregado!',
            'message': f'''¡Hola {customer_name}!

Tu pedido ha sido entregado exitosamente. 🏠

Pedido: {order_id}

¡Disfruta tu comida! Esperamos que tengas una excelente experiencia.

¿Te gustaría calificar tu pedido?
https://tu-app.vercel.app/?tracking={order_id}

---
Edo Sushi Bar 🍣
Gracias por tu preferencia
'''
        }
    }
    
    template = templates.get(notification_type, templates['STATUS_UPDATE'])
    
    subject = f"{template['emoji']} {template['title']} - {order_id}"
    body = template['message']
    
    return subject, body


def get_status_emoji(status):
    """Retorna emoji según el estado"""
    emojis = {
        'CONFIRMADO': '✅',
        'EN_PREPARACION': '👨‍🍳',
        'LISTO_PARA_RETIRAR': '✅',
        'EN_CAMINO': '🏍️',
        'ENTREGADO': '🏠'
    }
    return emojis.get(status, '📦')


def get_status_title(status):
    """Retorna título según el estado"""
    titles = {
        'CONFIRMADO': 'Pedido Confirmado',
        'EN_PREPARACION': 'Tu Pedido Está en Preparación',
        'LISTO_PARA_RETIRAR': 'Tu Pedido Está Listo',
        'EN_CAMINO': 'Tu Pedido Está en Camino',
        'ENTREGADO': '¡Pedido Entregado!'
    }
    return titles.get(status, 'Actualización de Pedido')


def get_status_text(status):
    """Retorna texto legible del estado"""
    texts = {
        'CONFIRMADO': 'Confirmado',
        'EN_PREPARACION': 'En Preparación',
        'LISTO_PARA_RETIRAR': 'Listo para Retirar',
        'EN_CAMINO': 'En Camino',
        'ENTREGADO': 'Entregado'
    }
    return texts.get(status, status)


def get_status_message(status):
    """Retorna mensaje descriptivo según el estado"""
    messages = {
        'CONFIRMADO': 'Tu pedido ha sido confirmado y está siendo procesado.',
        'EN_PREPARACION': 'Nuestros chefs están preparando tu pedido con los ingredientes más frescos.',
        'LISTO_PARA_RETIRAR': 'Tu pedido está empaquetado y listo. Puedes pasar a recogerlo o será enviado pronto.',
        'EN_CAMINO': 'Nuestro delivery está en camino a tu dirección. ¡Llegará pronto!',
        'ENTREGADO': 'Tu pedido ha sido entregado. ¡Disfruta tu comida!'
    }
    return messages.get(status, 'Tu pedido ha sido actualizado.')


def send_notification_manual(event, context):
    """
    Endpoint manual para enviar notificaciones (útil para testing)
    POST /notifications/send
    Body: {
        "type": "ORDER_CREATED",
        "orderId": "ORD-123",
        "customerEmail": "cliente@email.com",
        "customerName": "Juan Pérez",
        "status": "CONFIRMADO"
    }
    """
    try:
        data = json.loads(event['body'])
        
        # Enviar mensaje a SQS
        response = sqs_client.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(data)
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'message': 'Notification queued successfully',
                'messageId': response['MessageId']
            })
        }
        
    except Exception as e:
        print(f"Error sending manual notification: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
