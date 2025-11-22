"""
Handler de autenticación
Gestiona login de usuarios con credenciales almacenadas en DynamoDB
"""
import json
import os
import boto3
from botocore.exceptions import ClientError

from src.utils.responses import success_response, error_response, unauthorized_response, server_error_response
from src.utils.auth_helper import generate_token, verify_password


# Inicializar cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ['USERS_TABLE'])


def login(event, context):
    """
    Handler para autenticación de usuarios
    
    Input: { email: string, password: string }
    Output: { token: string, role: string, tenant_id: string, email: string }
    
    NOTA: Implementación simplificada para desarrollo.
    En producción:
    - Usar PyJWT para generar tokens JWT reales
    - Usar bcrypt para hashear contraseñas
    - Implementar rate limiting
    - Agregar logging de intentos de login
    
    Args:
        event (dict): Evento de API Gateway
        context (object): Contexto de Lambda
    
    Returns:
        dict: Respuesta HTTP con el token o error
    """
    try:
        # Parsear body
        if not event.get('body'):
            return error_response('Body requerido', 400)
        
        body = json.loads(event['body'])
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        
        # Validar campos requeridos
        if not email or not password:
            return error_response('Email y password son requeridos', 400)
        
        # Buscar usuario en DynamoDB
        try:
            response = users_table.get_item(Key={'email': email})
        except ClientError as e:
            print(f"Error al consultar DynamoDB: {e}")
            return server_error_response('Error al consultar base de datos')
        
        # Verificar si el usuario existe
        if 'Item' not in response:
            return unauthorized_response('Credenciales inválidas')
        
        user = response['Item']
        
        # Verificar contraseña
        if not verify_password(password, user.get('password', '')):
            return unauthorized_response('Credenciales inválidas')
        
        # Generar token
        token = generate_token(email)
        
        # Respuesta exitosa
        return success_response({
            'token': token,
            'role': user.get('role', 'CLIENTE'),
            'tenant_id': user.get('tenant_id', ''),
            'email': email
        })
    
    except json.JSONDecodeError:
        return error_response('JSON inválido en el body', 400)
    
    except Exception as e:
        print(f"Error inesperado en login: {str(e)}")
        import traceback
        traceback.print_exc()
        return server_error_response(f'Error interno del servidor: {str(e)}')
