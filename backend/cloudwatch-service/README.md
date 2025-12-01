# 📊 CloudWatch Dashboard Service

Servicio de monitoreo y observabilidad para Edo Sushi Bar.

## 🎯 Propósito

Este servicio crea un **Dashboard de CloudWatch** que monitorea en tiempo real:

- **Lambda Functions**: Invocaciones, errores, duración
- **DynamoDB**: Capacidad consumida, latencia
- **API Gateway**: Requests, errores 4XX/5XX, latencia
- **Logs**: Análisis de pedidos creados y estados

## 📦 Recursos Creados

### CloudWatch Dashboard: `EdoSushiBar-Dashboard`

**Widgets incluidos:**

1. **Lambda - Total Invocaciones**
   - Cuenta todas las invocaciones de Lambdas
   - Período: 5 minutos
   - Métrica: Sum

2. **Lambda - Errores y Throttles**
   - Errores de ejecución (rojo)
   - Throttles por límites (naranja)

3. **Lambda - Duración**
   - Tiempo promedio de ejecución
   - Tiempo máximo de ejecución
   - Identifica cuellos de botella

4. **DynamoDB - Capacidad Consumida**
   - Read Capacity Units
   - Write Capacity Units

5. **API Gateway - Requests y Errores**
   - Total de requests
   - Errores 4XX (cliente)
   - Errores 5XX (servidor)

6. **API Gateway - Latencia**
   - Latencia promedio
   - Percentil 99 (p99)

7. **Pedidos Creados (Log Insights)**
   - Query sobre logs de createOrder
   - Cuenta pedidos cada 5 minutos

8. **Estados de Pedidos (Log Insights)**
   - Gráfico de pie con distribución de estados
   - CONFIRMADO, EN_PREPARACION, ENTREGADO, etc.

## 🚀 Despliegue

### Opción 1: Script automatizado
```bash
cd backend/cloudwatch-service
./deploy.sh
```

### Opción 2: Serverless directo
```bash
cd backend/cloudwatch-service
serverless deploy
```

### Opción 3: Desde la raíz
```bash
cd backend
serverless deploy --config cloudwatch-service/serverless.yml
```

## 🔗 Acceso al Dashboard

Una vez desplegado, accede al dashboard en:

```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=EdoSushiBar-Dashboard
```

O desde AWS Console:
1. CloudWatch → Dashboards
2. Buscar: `EdoSushiBar-Dashboard`

## 📈 Métricas Custom

El servicio también puede recibir métricas personalizadas desde las Lambdas:

```python
import boto3
cloudwatch = boto3.client('cloudwatch')

# Enviar métrica personalizada
cloudwatch.put_metric_data(
    Namespace='EdoSushiBar/Orders',
    MetricData=[{
        'MetricName': 'OrdersCreated',
        'Value': 1,
        'Unit': 'Count',
        'Dimensions': [
            {'Name': 'Status', 'Value': 'CONFIRMADO'}
        ]
    }]
)
```

## 🗑️ Eliminación

Para eliminar el dashboard:

```bash
cd backend/cloudwatch-service
serverless remove
```

## 🔧 Configuración

El dashboard está configurado para:
- **Región**: us-east-1
- **Período de actualización**: 5 minutos
- **Retención de logs**: Según configuración de CloudWatch Logs

## 📊 Dashboard Incluye

- ✅ Monitoreo de todos los microservicios
- ✅ Análisis de performance en tiempo real
- ✅ Detección de errores automática
- ✅ Métricas de negocio (pedidos, estados)
- ✅ Logs agregados con CloudWatch Insights

## 🎯 Cumplimiento de Requerimientos

Este servicio cumple con el requerimiento del proyecto:
> "También elaborar un dashboard resumen"

Utilizando **CloudWatch Dashboard** como servicio de AWS obligatorio para observabilidad.
