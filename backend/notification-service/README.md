# Notification Service - Edo Sushi Bar

Sistema de notificaciones por email usando **AWS SNS + SQS**.

## 🏗️ Arquitectura

```
Cliente hace pedido → orders-service → SQS Queue → Lambda → SNS → Email
```

## 📧 Emails que se Envían

1. **Pedido Confirmado** - Cuando se crea el pedido
2. **En Preparación** - Cuando la cocina empieza
3. **Listo para Retirar** - Cuando está empaquetado
4. **En Camino** - Cuando sale el delivery
5. **Entregado** - Cuando se completa

## 🚀 Despliegue

### 1. Desplegar Notification Service

```bash
cd backend/notification-service
sls deploy --stage dev
```

**Importante:** Copia el ARN del SNS Topic y la URL de la cola SQS que aparecen en el output.

### 2. Configurar Email en SNS

1. Ve a **AWS Console → SNS → Topics**
2. Selecciona `EdoOrderNotifications`
3. Click en **Create subscription**
4. Protocol: **Email**
5. Endpoint: **tu-email@ejemplo.com**
6. Click **Create subscription**
7. **Revisa tu email** y confirma la suscripción

### 3. Actualizar Orders Service

Agrega la URL de la cola SQS al `serverless.yml` de orders-service:

```yaml
provider:
  environment:
    ORDERS_TABLE: EdoOrdersTable
    ORDER_BUS_NAME: EdoOrderBus
    NOTIFICATION_QUEUE_URL: https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT/EdoNotificationQueue
```

Luego despliega:

```bash
cd backend/orders-service
sls deploy --stage dev
```

## 🧪 Testing

### Probar con endpoint manual:

```bash
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ORDER_CREATED",
    "orderId": "TEST-123",
    "customerEmail": "tu-email@ejemplo.com",
    "customerName": "Juan Pérez",
    "status": "CONFIRMADO"
  }'
```

### Probar flujo completo:

1. Crea un pedido desde el frontend
2. Revisa tu email - deberías recibir "Pedido Confirmado"
3. Marca el pedido como "En Preparación" desde el staff panel
4. Revisa tu email - deberías recibir "En Preparación"

## 📊 Monitoreo

### Ver mensajes en la cola:

```bash
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT/EdoNotificationQueue \
  --attribute-names ApproximateNumberOfMessages
```

### Ver logs de Lambda:

```bash
sls logs -f processNotification --tail
```

### Ver Dead Letter Queue (mensajes fallidos):

```bash
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT/EdoNotificationDLQ
```

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción |
|----------|-------------|
| `SNS_TOPIC_ARN` | ARN del topic SNS |
| `NOTIFICATION_QUEUE_URL` | URL de la cola SQS |
| `ORDERS_TABLE` | Nombre de la tabla DynamoDB |

### Tipos de Notificación

| Tipo | Cuándo se envía |
|------|----------------|
| `ORDER_CREATED` | Al crear el pedido |
| `STATUS_UPDATE` | Al cambiar de estado |
| `ORDER_READY` | Cuando está listo |
| `ORDER_DELIVERED` | Cuando se entrega |

## 💰 Costos

- **SNS**: $0.50 por millón de emails
- **SQS**: Primeros 1M requests/mes GRATIS
- **Lambda**: Primeras 1M invocaciones/mes GRATIS

**Estimado:** < $1 USD/mes para un restaurante

## 🐛 Troubleshooting

### Los emails no llegan:

1. **Verifica que confirmaste la suscripción** en SNS
2. Revisa la carpeta de spam
3. Verifica los logs de Lambda: `sls logs -f processNotification`
4. Verifica que NOTIFICATION_QUEUE_URL esté configurado en orders-service

### Mensajes en Dead Letter Queue:

```bash
# Ver mensajes fallidos
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT/EdoNotificationDLQ \
  --max-number-of-messages 10
```

### Purgar la cola (limpiar mensajes):

```bash
aws sqs purge-queue \
  --queue-url https://sqs.us-east-1.amazonaws.com/YOUR-ACCOUNT/EdoNotificationQueue
```

## 📝 Notas

- Los emails son texto plano (no HTML) para máxima compatibilidad
- La cola SQS tiene un Dead Letter Queue para mensajes fallidos
- Los mensajes se reintentan hasta 3 veces antes de ir al DLQ
- Los mensajes se retienen por 24 horas en la cola principal
- Los mensajes en DLQ se retienen por 14 días
