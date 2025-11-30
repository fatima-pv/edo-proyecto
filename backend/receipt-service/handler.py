import json
import boto3
import os
from datetime import datetime

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])
BUCKET_NAME = os.environ['RECEIPTS_BUCKET']

def generate_receipt(event, context):
    """
    Genera un recibo HTML cuando se crea una orden (vía DynamoDB Streams)
    """
    print("Generating receipt for event:", json.dumps(event))
    
    try:
        # Process DynamoDB Stream records
        for record in event['Records']:
            # Only process INSERT events (new orders)
            if record['eventName'] != 'INSERT':
                continue
                
            # Extract order data from DynamoDB Stream
            new_image = record['dynamodb']['NewImage']
            order_id = new_image['orderId']['S']
            
            print(f"Processing new order: {order_id}")
            
            # Get full order details from DynamoDB
            response = orders_table.get_item(Key={'orderId': order_id})
            order = response.get('Item')
            
            if not order:
                print(f"Order {order_id} not found in DynamoDB")
                continue

            # Generar HTML del recibo
            customer = order.get('customer', {})
            items = order.get('items', [])
            total_amount = float(order.get('total', 0))
            
            html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recibo - Edo Sushi Bar</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .receipt {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #1a237e;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1a237e;
            margin: 0;
            font-size: 32px;
        }}
        .header p {{
            color: #666;
            margin: 5px 0;
        }}
        .info {{
            margin: 20px 0;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .info-label {{
            font-weight: bold;
            color: #333;
        }}
        .items {{
            margin: 30px 0;
        }}
        .items table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .items th {{
            background: #1a237e;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .items td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        .total {{
            text-align: right;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 2px solid #1a237e;
        }}
        .total-amount {{
            font-size: 24px;
            font-weight: bold;
            color: #1a237e;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="receipt">
        <div class="header">
            <h1>🍣 Edo Sushi Bar</h1>
            <p>La mejor experiencia japonesa</p>
            <p>www.edosushibar.com</p>
        </div>
        
        <h2 style="text-align: center; color: #1a237e;">COMPROBANTE DE PAGO</h2>
        
        <div class="info">
            <div class="info-row">
                <span class="info-label">Pedido:</span>
                <span>{order_id}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Fecha:</span>
                <span>{order.get('createdAt', datetime.now().isoformat())}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Cliente:</span>
                <span>{customer.get('name', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Email:</span>
                <span>{customer.get('email', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">DNI:</span>
                <span>{customer.get('dni', 'N/A')}</span>
            </div>
        </div>
        
        <div class="items">
            <table>
                <thead>
                    <tr>
                        <th>Cantidad</th>
                        <th>Descripción</th>
                        <th style="text-align: right;">Precio Unit.</th>
                        <th style="text-align: right;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for item in items:
                name = item.get('name', item.get('product', {}).get('name', 'Producto'))
                price = float(item.get('price', 0))
                quantity = int(item.get('quantity', 1))
                subtotal = price * quantity
                
                html_content += f"""
                    <tr>
                        <td>{quantity}</td>
                        <td>{name}</td>
                        <td style="text-align: right;">S/. {price:.2f}</td>
                        <td style="text-align: right;">S/. {subtotal:.2f}</td>
                    </tr>
"""
            
            html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="total">
            <p class="total-amount">TOTAL: S/. {total_amount:.2f}</p>
        </div>
        
        <div class="footer">
            <p>¡Gracias por su preferencia!</p>
            <p>Edo Sushi Bar - Sabor auténtico japonés</p>
        </div>
    </div>
</body>
</html>
"""
            
            # Subir HTML a S3
            file_name = f"receipts/{order_id}.html"
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=file_name,
                Body=html_content.encode('utf-8'),
                ContentType='text/html',
                ACL='public-read'
            )
            
            # URL Pública
            receipt_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_name}"
            print(f"Receipt generated: {receipt_url}")
            
            # Actualizar DynamoDB con la URL
            orders_table.update_item(
                Key={'orderId': order_id},
                UpdateExpression='SET receiptUrl = :url',
                ExpressionAttributeValues={':url': receipt_url}
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Receipts processed'})
        }
        
    except Exception as e:
        print(f"Error generating receipt: {str(e)}")
        raise e
