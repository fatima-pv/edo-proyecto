import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ['USERS_TABLE'])

def auth_login(event, context):
    body = json.loads(event['body'])
    email = body.get('email')
    password = body.get('password')

    # TODO: Implement actual validation against DynamoDB
    # This is a placeholder
    
    if email == 'test@example.com' and password == 'password':
        return {
            'statusCode': 200,
            'body': json.dumps({
                'token': 'fake-jwt-token',
                'role': 'CLIENTE',
                'tenant_id': 'sede-1'
            })
        }

    return {
        'statusCode': 401,
        'body': json.dumps({'message': 'Unauthorized'})
    }
