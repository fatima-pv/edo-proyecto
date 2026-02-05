import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ['USERS_TABLE'])

def registerUser(event, context):
    """
    Registra un nuevo usuario del staff
    POST /auth/register
    Body: { email, password, name, role }
    """
    try:
        data = json.loads(event['body'])
        
        # Validar campos requeridos
        required_fields = ['email', 'password', 'name', 'role']
        for field in required_fields:
            if field not in data:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': f'Campo requerido: {field}'})
                }
        
        # Validar rol
        valid_roles = ['ADMIN', 'COCINERO', 'DESPACHADOR', 'REPARTIDOR']
        if data['role'] not in valid_roles:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'Rol inválido. Debe ser uno de: {valid_roles}'})
            }
        
        # Verificar si el usuario ya existe
        existing_user = users_table.get_item(Key={'email': data['email']})
        if 'Item' in existing_user:
            return {
                'statusCode': 409,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'El usuario ya existe'})
            }
        
        # Guardar usuario en DynamoDB
        user = {
            'email': data['email'],
            'password': data['password'],  # En producción, hashear la contraseña
            'name': data['name'],
            'role': data['role']
        }
        
        users_table.put_item(Item=user)
        
        return {
            'statusCode': 201,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Usuario registrado exitosamente',
                'user': {
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def loginUser(event, context):
    """
    Autentica un usuario del staff
    POST /auth/login
    Body: { email, password }
    """
    try:
        data = json.loads(event['body'])
        
        # Validar campos requeridos
        if 'email' not in data or 'password' not in data:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Email y password son requeridos'})
            }
        
        # Buscar usuario en DynamoDB
        response = users_table.get_item(Key={'email': data['email']})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Usuario no encontrado'})
            }
        
        user = response['Item']
        
        # Verificar contraseña (comparación simple)
        if user['password'] != data['password']:
            return {
                'statusCode': 401,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Contraseña incorrecta'})
            }
        
        # Login exitoso - devolver información del usuario con ROL
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'message': 'Login OK',
                'user': {
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
