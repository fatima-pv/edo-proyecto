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
        
        # Generate receipt content
        lines = [
            "=== BOLETA EDO SUSHI ===",
            f"Orden: {order_id}",
            f"Cliente: {customer.get('name', 'Cliente')}",
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "------------------------",
            "Items:"
        ]
        
        for item in items:
            product_name = item.get('product', {}).get('name', 'Producto')
            price = item.get('price', 0)
            lines.append(f"- {product_name} x1 - S/ {price}")
            
        lines.append("------------------------")
        lines.append(f"TOTAL: S/ {total:.2f}")
        lines.append("========================")
        
        receipt_content = "\n".join(lines)
        
        # Upload to S3
        file_key = f"boleta-{order_id}.txt"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=receipt_content,
            ContentType='text/plain'
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
