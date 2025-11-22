import json
import os
import boto3
import time
import uuid

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])
stepfunctions = boto3.client('stepfunctions')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

def create_order(event, context):
    # TODO: Validate user role is CLIENTE
    body = json.loads(event['body'])
    order_id = f"order-{int(time.time())}"
    tenant_id = body.get('tenant_id')
    
    item = {
        'tenant_id': tenant_id,
        'order_id': order_id,
        'status': 'RECEIVED',
        'details': body
    }
    
    # Save to DynamoDB
    orders_table.put_item(Item=item)
    
    # Start Step Function
    try:
        stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps({
                'orderId': order_id,
                'tenantId': tenant_id,
                'details': body
            })
        )
    except Exception as e:
        print(f"Error starting Step Function: {e}")
        # Proceeding even if SF fails to start for this demo, but ideally should handle error
    
    return {
        'statusCode': 201,
        'body': json.dumps({'message': 'Order created', 'orderId': order_id})
    }

def get_orders(event, context):
    # TODO: Implement logic based on role (CLIENTE vs STAFF)
    # For now, return all orders (Scan is expensive, use Query in prod)
    response = orders_table.scan()
    items = response.get('Items', [])
    
    return {
        'statusCode': 200,
        'body': json.dumps(items)
    }
