import json
import boto3
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])
BUCKET_NAME = os.environ['RECEIPTS_BUCKET']

def generate_receipt(event, context):
    """
    Genera un PDF del recibo cuando se crea una orden (vía EventBridge)
    """
    print("Generating receipt for event:", json.dumps(event))
    
    try:
        # Extraer datos del evento de EventBridge
        detail = event.get('detail', {})
        order_id = detail.get('orderId')
        
        if not order_id:
            print("No orderId found in event")
            return
            
        # Obtener datos completos de la orden (por si falta algo en el evento)
        response = orders_table.get_item(Key={'orderId': order_id})
        order = response.get('Item')
        
        if not order:
            print(f"Order {order_id} not found in DynamoDB")
            return

        # Generar PDF en memoria
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        
        # --- Diseño del Recibo ---
        
        # Header
        c.setFillColor(colors.navy)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height - 50, "Edo Sushi Bar")
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "La mejor experiencia japonesa")
        c.drawString(50, height - 85, "www.edosushibar.com")
        
        # Título
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - 120, "COMPROBANTE DE PAGO")
        
        # Info del Pedido
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 160, f"Pedido: {order_id}")
        
        c.setFont("Helvetica", 11)
        c.drawString(50, height - 180, f"Fecha: {order.get('createdAt', datetime.now().isoformat())}")
        
        # Info del Cliente
        customer = order.get('customer', {})
        c.drawString(50, height - 210, f"Cliente: {customer.get('name', 'N/A')}")
        c.drawString(50, height - 225, f"Email: {customer.get('email', 'N/A')}")
        c.drawString(50, height - 240, f"DNI: {customer.get('dni', 'N/A')}")
        
        # Línea separadora
        c.line(50, height - 260, width - 50, height - 260)
        
        # Tabla de Productos
        y = height - 290
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "CANT")
        c.drawString(100, y, "DESCRIPCIÓN")
        c.drawString(450, y, "PRECIO")
        
        y -= 20
        c.setFont("Helvetica", 10)
        
        total = 0
        for item in order.get('items', []):
            name = item.get('name', item.get('product', {}).get('name', 'Producto'))
            price = float(item.get('price', 0))
            quantity = int(item.get('quantity', 1))
            subtotal = price * quantity
            
            c.drawString(50, y, str(quantity))
            c.drawString(100, y, name)
            c.drawString(450, y, f"S/. {subtotal:.2f}")
            y -= 20
            
        # Línea separadora
        y -= 10
        c.line(50, y, width - 50, y)
        
        # Totales
        y -= 30
        c.setFont("Helvetica-Bold", 14)
        total_amount = float(order.get('total', 0))
        c.drawRightString(width - 50, y, f"TOTAL: S/. {total_amount:.2f}")
        
        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(width/2, 50, "Gracias por su preferencia - Edo Sushi Bar")
        
        c.save()
        
        # --- Subir a S3 ---
        pdf_buffer.seek(0)
        file_name = f"receipts/{order_id}.pdf"
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf',
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
            'body': json.dumps({'receiptUrl': receipt_url})
        }
        
    except Exception as e:
        print(f"Error generating receipt: {str(e)}")
        raise e
