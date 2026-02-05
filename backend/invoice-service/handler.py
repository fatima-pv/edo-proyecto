import json
import boto3
import os
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])
BUCKET_NAME = os.environ['RECEIPTS_BUCKET']

def generateReceipt(event, context):
    print("Event received:", json.dumps(event))
    
    try:
        detail = event['detail']
        order_id = detail['orderId']
        customer = detail['customer']
        items = detail['items']
        total = detail['total']
        
        # Create TXT receipt (simple and works)
        receipt_text = f"""
╔══════════════════════════════════════════════╗
║           EDO SUSHI BAR 🍣                   ║
║           BOLETA DE VENTA                    ║
╚══════════════════════════════════════════════╝

Orden: {order_id}
Cliente: {customer.get('name', 'Cliente')}
DNI: {customer.get('dni', 'N/A')}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRODUCTOS:
"""
        
        # Add items
        for item in items:
            product_name = item.get('product', {}).get('name', 'Producto')
            price = item.get('price', item.get('product', {}).get('price', 0))
            quantity = item.get('quantity', 1)
            receipt_text += f"  • {product_name} x{quantity}\n"
            receipt_text += f"    S/ {float(price):.2f}\n"
        
        receipt_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOTAL: S/ {float(total):.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¡Gracias por su preferencia!
ありがとう (Arigatou)

Dirección: {customer.get('address', 'Recojo en tienda')}
Tipo: {detail.get('deliveryType', 'DELIVERY')}
"""
        
        # Upload to S3 as TXT
        file_key = f"boleta-{order_id}.txt"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=receipt_text.encode('utf-8'),
            ContentType='text/plain; charset=utf-8'
        )
        
        # Construct URL
        receipt_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_key}"
        print(f"Receipt uploaded to: {receipt_url}")
        
        # Update DynamoDB
        orders_table.update_item(
            Key={'orderId': order_id},
            UpdateExpression="set receiptUrl = :r",
            ExpressionAttributeValues={':r': receipt_url}
        )
        
        print(f"Order {order_id} updated with receipt URL")
        return {"status": "success", "receiptUrl": receipt_url}
        
    except Exception as e:
        print(f"Error generating receipt: {str(e)}")
        raise e
