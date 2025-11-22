#!/bin/bash

# Script para crear datos de prueba en DynamoDB
# Requisito: AWS CLI configurado

# Variables
STAGE=${1:-dev}
USERS_TABLE="edo-sushi-bar-users-${STAGE}"
ORDERS_TABLE="edo-sushi-bar-orders-${STAGE}"

echo "🔧 Creando datos de prueba en el stage: ${STAGE}"
echo ""

# ===================================
# CREAR USUARIOS DE PRUEBA
# ===================================

echo "👤 Creando usuarios de prueba..."

# Usuario CLIENTE
aws dynamodb put-item \
  --table-name ${USERS_TABLE} \
  --item '{
    "email": {"S": "cliente@test.com"},
    "password": {"S": "cliente123"},
    "role": {"S": "CLIENTE"},
    "tenant_id": {"S": "sede-miraflores"}
  }'
echo "✅ Cliente creado: cliente@test.com / cliente123"

# Usuario STAFF - Cocinero
aws dynamodb put-item \
  --table-name ${USERS_TABLE} \
  --item '{
    "email": {"S": "chef@edosushi.com"},
    "password": {"S": "chef123"},
    "role": {"S": "STAFF"},
    "tenant_id": {"S": "sede-miraflores"},
    "staff_type": {"S": "COCINERO"}
  }'
echo "✅ Chef creado: chef@edosushi.com / chef123"

# Usuario STAFF - Empaquetador
aws dynamodb put-item \
  --table-name ${USERS_TABLE} \
  --item '{
    "email": {"S": "empaquetador@edosushi.com"},
    "password": {"S": "emp123"},
    "role": {"S": "STAFF"},
    "tenant_id": {"S": "sede-miraflores"},
    "staff_type": {"S": "EMPAQUETADOR"}
  }'
echo "✅ Empaquetador creado: empaquetador@edosushi.com / emp123"

# Usuario STAFF - Delivery
aws dynamodb put-item \
  --table-name ${USERS_TABLE} \
  --item '{
    "email": {"S": "delivery@edosushi.com"},
    "password": {"S": "delivery123"},
    "role": {"S": "STAFF"},
    "tenant_id": {"S": "sede-miraflores"},
    "staff_type": {"S": "MOTORIZADO"}
  }'
echo "✅ Motorizado creado: delivery@edosushi.com / delivery123"

echo ""
echo "✨ Usuarios creados exitosamente!"
echo ""
echo "📋 Resumen de credenciales:"
echo "  CLIENTE:       cliente@test.com / cliente123"
echo "  CHEF:          chef@edosushi.com / chef123"
echo "  EMPAQUETADOR:  empaquetador@edosushi.com / emp123"
echo "  MOTORIZADO:    delivery@edosushi.com / delivery123"
echo ""
echo "🎯 Sede: sede-miraflores"
