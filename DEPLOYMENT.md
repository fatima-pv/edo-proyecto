# Guía de Despliegue - Edo Sushi Bar

Esta guía te ayudará a desplegar el proyecto paso a paso.

## 📋 Prerrequisitos

### 1. AWS CLI
```bash
# Instalar AWS CLI
brew install awscli  # macOS
# o descarga desde: https://aws.amazon.com/cli/

# Configurar credenciales
aws configure
# AWS Access Key ID: [tu-access-key]
# AWS Secret Access Key: [tu-secret-key]
# Default region: us-east-1
# Default output format: json
```

### 2. Python 3.11
```bash
# Verificar versión
python3 --version  # Debe ser v3.11.x o superior

# Si necesitas instalar Python:
# macOS: brew install python@3.11
# O descarga desde: https://www.python.org/
```

### 3. Permisos IAM Necesarios

Tu usuario de AWS debe tener permisos para:
- CloudFormation
- Lambda
- API Gateway
- DynamoDB
- EventBridge
- Step Functions
- IAM (para crear roles)
- CloudWatch Logs

## 🚀 Paso 1: Instalación

```bash
# Clonar el proyecto
cd /Users/mauricioalarcon/utec/cloud/edo-proyecto

# Instalar Serverless Framework (si no lo tienes)
npm install -g serverless

# Nota: Las dependencias Python (boto3) vienen incluidas en el runtime de Lambda
# No necesitas instalar requirements.txt localmente para deployment
```

## 🔧 Paso 2: Configuración (Opcional)

Si quieres usar JWT real en producción:

```bash
# Crear archivo .env
echo "JWT_SECRET=tu-secret-super-seguro-cambialo-en-produccion" > .env
```

## 📦 Paso 3: Deploy a DEV

```bash
# Desplegar en entorno de desarrollo
npm run deploy:dev

# Espera aproximadamente 3-5 minutos
# Verás el progreso del deployment
```

### Salida Esperada

```
✔ Service deployed to stack edo-sushi-bar-dev

endpoints:
  POST - https://xxxxx.execute-api.us-east-1.amazonaws.com/dev/auth/login
  POST - https://xxxxx.execute-api.us-east-1.amazonaws.com/dev/orders
  GET - https://xxxxx.execute-api.us-east-1.amazonaws.com/dev/orders
  POST - https://xxxxx.execute-api.us-east-1.amazonaws.com/dev/orders/advance

functions:
  authLogin
  createOrder
  getOrders
  updateOrderStep
  notifyStaff

Stack Outputs:
  ApiEndpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
  EdoOrderWorkflowArn: arn:aws:states:us-east-1:xxxxx:stateMachine:EdoOrderWorkflow-dev
```

**💾 IMPORTANTE:** Guarda el `ApiEndpoint` que aparece en la salida.

## 🌱 Paso 4: Crear Datos de Prueba

```bash
# Dar permisos de ejecución al script
chmod +x scripts/seed-data.sh

# Ejecutar script de seed
./scripts/seed-data.sh dev
```

Esto creará:
- ✅ Usuario Cliente: `cliente@test.com` / `cliente123`
- ✅ Usuario Chef: `chef@edosushi.com` / `chef123`
- ✅ Usuario Empaquetador: `empaquetador@edosushi.com` / `emp123`
- ✅ Usuario Motorizado: `delivery@edosushi.com` / `delivery123`

## 🧪 Paso 5: Probar el Sistema

### 5.1 Login como Cliente

```bash
# Reemplaza API_ENDPOINT con tu endpoint real
API_ENDPOINT="https://xxxxx.execute-api.us-east-1.amazonaws.com/dev"

curl -X POST ${API_ENDPOINT}/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "cliente@test.com",
    "password": "cliente123"
  }'
```

**Respuesta esperada:**
```json
{
  "token": "fake-jwt-1700000000-cliente@test.com",
  "role": "CLIENTE",
  "tenant_id": "sede-miraflores",
  "email": "cliente@test.com"
}
```

💾 **Guarda el token** para los siguientes pasos.

### 5.2 Crear un Pedido

```bash
TOKEN="fake-jwt-1700000000-cliente@test.com"  # Usa tu token real

curl -X POST ${API_ENDPOINT}/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "tenant_id": "sede-miraflores",
    "items": [
      {
        "name": "Maki Acevichado",
        "quantity": 2,
        "price": 18.00
      },
      {
        "name": "Ramen Tradicional",
        "quantity": 1,
        "price": 22.00
      }
    ],
    "total": 58.00,
    "customer_info": {
      "name": "Juan Pérez",
      "phone": "+51999888777",
      "address": "Av. Larco 123, Miraflores"
    }
  }'
```

**Respuesta esperada:**
```json
{
  "message": "Pedido creado exitosamente",
  "order_id": "abc-123-def-456",
  "status": "RECEIVED",
  "execution_arn": "arn:aws:states:us-east-1:xxxxx:execution:..."
}
```

### 5.3 Ver Step Function en AWS Console

1. Ve a AWS Console → Step Functions
2. Busca `EdoOrderWorkflow-dev`
3. Verás una ejecución en estado **Running**
4. Click en la ejecución para ver el estado actual

Deberías ver que está en estado **WaitCocinero** esperando el callback.

### 5.4 Avanzar el Pedido (Como Chef)

Primero, login como chef:

```bash
curl -X POST ${API_ENDPOINT}/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "chef@edosushi.com",
    "password": "chef123"
  }'
```

Obtener el `taskToken` del pedido:

```bash
# Listar pedidos
CHEF_TOKEN="..."  # Token del chef

curl -X GET ${API_ENDPOINT}/orders \
  -H "Authorization: Bearer ${CHEF_TOKEN}"
```

Busca el campo `task_token` en el pedido y úsalo para avanzar:

```bash
ORDER_ID="abc-123-def-456"  # Tu order_id real
TASK_TOKEN="AQC8A3VuZ2luZ..."  # El taskToken del pedido

curl -X POST ${API_ENDPOINT}/orders/advance \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${CHEF_TOKEN}" \
  -d '{
    "order_id": "'${ORDER_ID}'",
    "tenant_id": "sede-miraflores",
    "task_token": "'${TASK_TOKEN}'",
    "step": "COOKING",
    "notes": "Preparación iniciada"
  }'
```

### 5.5 Verificar en Step Function

Vuelve a la AWS Console → Step Functions y verás que:
1. ✅ El estado **WaitCocinero** se completó
2. ✅ Se emitió un evento **EmitCookingStarted**
3. ⏸️ Ahora está en **WaitEmpaquetado**

## 📊 Paso 6: Monitoreo

### Ver Logs

```bash
# Ver logs de una función
npm run logs -- authLogin -- --tail

# Ver logs de createOrder
npm run logs -- createOrder -- --tail
```

### Ver eventos en EventBridge

```bash
aws events list-archives

aws events describe-archive \
  --archive-name EdoOrderBusArchive-dev
```

## 🌐 Paso 7: Deploy a Producción

Cuando estés listo para producción:

```bash
# Deploy a PROD
npm run deploy:prod

# Crear datos de prueba en PROD
./scripts/seed-data.sh prod
```

## 🗑️ Limpieza

Para eliminar todos los recursos de AWS:

```bash
# Eliminar stack de DEV
npm run remove -- --stage dev

# Eliminar stack de PROD
npm run remove -- --stage prod
```

⚠️ **ADVERTENCIA**: Esto eliminará todas las tablas de DynamoDB y sus datos.

## 🐛 Troubleshooting

### Error: "No se puede crear la tabla"
- Verifica que tu usuario AWS tenga permisos de DynamoDB

### Error: "Rate exceeded"
- Espera 1 minuto y vuelve a intentar el deploy

### Lambda no se actualiza
```bash
# Forzar actualización de código de una función específica
serverless deploy function -f authLogin

# O redeploy completo
sls deploy --force
```

### Ver errores detallados
```bash
# Deploy con modo verbose
serverless deploy --verbose
```

## 📚 Próximos Pasos

1. Implementar frontend (React/Vue)
2. Agregar WebSockets para actualizaciones en tiempo real
3. Implementar notificaciones push con SNS
4. Agregar tests automatizados con pytest
5. Configurar CI/CD con GitHub Actions

## 🎓 Recursos

- [AWS Step Functions Callback Pattern](https://docs.aws.amazon.com/step-functions/latest/dg/callback-task-sample-sqs.html)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Serverless Framework Docs](https://www.serverless.com/framework/docs)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
