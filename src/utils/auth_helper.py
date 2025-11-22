"""
Utilidades de autenticación
"""
import os


def get_user_from_token(event):
    """
    Extrae información del usuario desde el token del header Authorization
    
    NOTA: Esto es una implementación simplificada.
    En producción, usar PyJWT para validar tokens JWT reales.
    
    Args:
        event (dict): Evento de Lambda con headers
    
    Returns:
        dict: Información del usuario o None si no hay token
    """
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization') or headers.get('authorization')
    
    if not auth_header:
        return None
    
    # Remover "Bearer " del token
    token = auth_header.replace('Bearer ', '')
    
    # Parsear el fake-jwt: fake-jwt-timestamp-email
    # Formato: fake-jwt-1700000000-usuario@example.com
    parts = token.split('-')
    
    if len(parts) < 4 or parts[0] != 'fake' or parts[1] != 'jwt':
        return None
    
    # El email puede contener guiones, así que unimos desde el índice 3
    email = '-'.join(parts[3:])
    
    return {
        'email': email,
        'token': token
    }


def generate_token(email):
    """
    Genera un token simple para el usuario
    
    NOTA: En producción, usar PyJWT para generar tokens JWT reales con:
    - Firma criptográfica
    - Expiración
    - Claims adicionales
    
    Args:
        email (str): Email del usuario
    
    Returns:
        str: Token generado
    """
    import time
    timestamp = int(time.time())
    return f"fake-jwt-{timestamp}-{email}"


def hash_password(password):
    """
    Hash de contraseña (simplificado)
    
    NOTA: En producción, usar bcrypt o argon2:
    ```python
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    ```
    
    Args:
        password (str): Contraseña en texto plano
    
    Returns:
        str: Hash de la contraseña
    """
    # Por ahora retornamos la contraseña tal cual (NO HACER EN PRODUCCIÓN)
    return password


def verify_password(password, hashed_password):
    """
    Verifica que la contraseña coincida con el hash
    
    NOTA: En producción, usar bcrypt:
    ```python
    import bcrypt
    return bcrypt.checkpw(password.encode(), hashed_password.encode())
    ```
    
    Args:
        password (str): Contraseña en texto plano
        hashed_password (str): Hash almacenado
    
    Returns:
        bool: True si coincide, False si no
    """
    # Por ahora comparación directa (NO HACER EN PRODUCCIÓN)
    return password == hashed_password
