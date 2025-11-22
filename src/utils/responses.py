"""
Utilidad para generar respuestas HTTP estandarizadas
"""
import json


def http_response(status_code, body, additional_headers=None):
    """
    Genera una respuesta HTTP con CORS habilitado
    
    Args:
        status_code (int): Código de estado HTTP
        body (dict): Cuerpo de la respuesta
        additional_headers (dict): Headers adicionales opcionales
    
    Returns:
        dict: Respuesta formateada para API Gateway
    """
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    if additional_headers:
        headers.update(additional_headers)
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(body, ensure_ascii=False)
    }


def success_response(data, status_code=200):
    """Respuesta de éxito"""
    return http_response(status_code, data)


def error_response(message, status_code=400, error_type='Error'):
    """Respuesta de error"""
    return http_response(status_code, {
        'error': error_type,
        'message': message
    })


def unauthorized_response(message='No autorizado'):
    """Respuesta 401 Unauthorized"""
    return error_response(message, 401, 'Unauthorized')


def forbidden_response(message='Acceso denegado'):
    """Respuesta 403 Forbidden"""
    return error_response(message, 403, 'Forbidden')


def not_found_response(message='Recurso no encontrado'):
    """Respuesta 404 Not Found"""
    return error_response(message, 404, 'NotFound')


def server_error_response(message='Error interno del servidor'):
    """Respuesta 500 Internal Server Error"""
    return error_response(message, 500, 'InternalServerError')
