import json
import boto3
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors

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
        
        # Create PDF in memory
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Set up the PDF
        y = height - 1 * inch
        
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, y, "EDO SUSHI BAR")
        y -= 0.3 * inch
        
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, y, "BOLETA DE VENTA")
        y -= 0.5 * inch
        
        # Order details
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1 * inch, y, f"Orden: {order_id[:20]}...")
        y -= 0.25 * inch
        
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, y, f"Cliente: {customer.get('name', 'Cliente')}")
        y -= 0.2 * inch
        c.drawString(1 * inch, y, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        y -= 0.4 * inch
        
        # Line separator
        c.line(1 * inch, y, width - 1 * inch, y)
        y -= 0.3 * inch
        
        # Items header
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1 * inch, y, "Producto")
        c.drawString(width - 2 * inch, y, "Precio")
        y -= 0.25 * inch
        
        # Items
        c.setFont("Helvetica", 10)
        for item in items:
            product_name = item.get('product', {}).get('name', 'Producto')
            # Try to get price from item.price first, then from item.product.price
            price = item.get('price', item.get('product', {}).get('price', 0))
            
            c.drawString(1 * inch, y, f"{product_name}")
            c.drawString(width - 2 * inch, y, f"S/ {float(price):.2f}")
            y -= 0.2 * inch
        
        y -= 0.2 * inch
        c.line(1 * inch, y, width - 1 * inch, y)
        y -= 0.3 * inch
        
        # Total
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y, "TOTAL:")
        c.drawString(width - 2 * inch, y, f"S/ {float(total):.2f}")
        y -= 0.5 * inch
        
        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(width/2, y, "¡Gracias por su preferencia! ありがとう")
        
        # Save PDF
        c.save()
        buffer.seek(0)
        
        # Upload to S3
        file_key = f"boleta-{order_id}.pdf"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=buffer.getvalue(),
            ContentType='application/pdf'
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
