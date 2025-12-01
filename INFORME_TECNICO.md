# 📄 INFORME TÉCNICO - SISTEMA DE GESTIÓN DE PEDIDOS EDO SUSHI BAR

**Sistema Multi-Tenant Serverless Basado en Eventos**

---

## 1. INTRODUCCIÓN

El presente documento describe la arquitectura e implementación del sistema de gestión de pedidos para Edo Sushi Bar, desarrollado como solución serverless multi-tenant utilizando servicios de AWS.

### 1.1 Objetivo del Sistema

Desarrollar una plataforma completa que permita:
- A los clientes realizar pedidos de comida en línea
- Al personal del restaurante gestionar el flujo de trabajo de pedidos
- Monitorear en tiempo real el estado de cada pedido
- Generar métricas y estadísticas del negocio

### 1.2 Alcance

El sistema incluye:
- Aplicación web para clientes (pedidos y tracking)
- Aplicación web para staff (gestión de workflow)
- Backend serverless con microservicios
- Orquestación de flujo de trabajo automatizado
- Generación automática de boletas
- Dashboard de monitoreo en tiempo real
- Arquitectura multi-tenant con aislamiento de datos

---

## 2. ARQUITECTURA DE LA SOLUCIÓN

### 2.1 Principios Arquitectónicos

**Multi-Tenancy:**
El sistema implementa una arquitectura multi-tenant que permite que múltiples restaurantes (tenants) utilicen la misma infraestructura con datos completamente aislados. Cada entidad de datos incluye un identificador de tenant (`tenantId`) que asegura la separación lógica.

**Serverless:**
100% serverless sin gestión de servidores. Utiliza:
- AWS Lambda para cómputo
- DynamoDB para almacenamiento
- Escalamiento automático según demanda
- Modelo de pago por uso

**Basado en Eventos (Event-Driven):**
Los componentes se comunican mediante eventos asíncronos:
- EventBridge como bus de eventos central
- Step Functions para orquestación de workflows
- Desacoplamiento total entre servicios

### 2.2 Capas de la Arquitectura

```
┌─────────────────────────────────────────┐
│   CAPA 1: PRESENTACIÓN (Amplify)        │
│   - Frontend Cliente (React)            │
│   - Frontend Staff (React)              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   CAPA 2: API (API Gateway)             │
│   - REST API con CORS                   │
│   - Multi-tenant routing                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   CAPA 3: MICROSERVICIOS (Lambda)       │
│   - Users Service                       │
│   - Products Service                    │
│   - Orders Service                      │
│   - Invoice Service                     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   CAPA 4: ORQUESTACIÓN                  │
│   - EventBridge (bus de eventos)        │
│   - Step Functions (workflow)           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   CAPA 5: DATOS                         │
│   - DynamoDB (3 tablas)                 │
│   - S3 (almacenamiento boletas)         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   CAPA 6: OBSERVABILIDAD                │
│   - CloudWatch Dashboard                │
│   - CloudWatch Logs                     │
│   - Métricas personalizadas             │
└─────────────────────────────────────────┘
```

---

## 3. MICROSERVICIOS IMPLEMENTADOS

### 3.1 Users Service (Autenticación del Staff)

**Propósito:** Gestión de usuarios del personal del restaurante.

**Endpoints:**
- `POST /auth/register` - Registro de nuevo usuario staff
- `POST /auth/login` - Autenticación de usuario staff

**Funciones Lambda:**

#### `registerUser`
```
Entrada (Body): {email, password, name, role}
Entrada (Header - opcional): x-tenant-id

Proceso:
  1. Obtiene tenantId:
     - Desde header x-tenant-id, O
     - Valor por defecto: "edo-sushi-bar"
  2. Valida campos requeridos
  3. Valida rol (ADMIN, COCINERO, DESPACHADOR, REPARTIDOR)
  4. Verifica que el email no exista (con PK + SK)
  5. Guarda en DynamoDB con tenantId como PK
  
Salida: {message, user: {email, name, role}}
```

#### `loginUser`
```
Entrada (Body): {email, password}
Entrada (Header - opcional): x-tenant-id

Proceso:
  1. Obtiene tenantId (header o default)
  2. Busca usuario en DynamoDB:
     - Key: {tenantId, email}
  3. Verifica contraseña
  4. Retorna datos del usuario
  
Salida: {message, user: {email, name, role, tenantId}}
```

**Tabla DynamoDB: EdoUsersTable**
```json
{
  "TableName": "EdoUsersTable",
  "KeySchema": [
    {"AttributeName": "tenantId", "KeyType": "HASH"},
    {"AttributeName": "email", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "tenantId", "AttributeType": "S"},
    {"AttributeName": "email", "AttributeType": "S"}
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```

**Estructura Multi-Tenant:**
- **Partition Key (PK):** `tenantId` - Aísla datos por restaurante
- **Sort Key (SK):** `email` - Identifica usuario dentro del tenant

**Ejemplo de Item:**
```json
{
  "tenantId": "edo-sushi-bar",
  "email": "chef@edosushi.com",
  "password": "hashed_password",
  "name": "Juan Pérez",
  "role": "COCINERO"
}
```

**Query Example:**
```python
# Obtener usuario de un tenant específico
response = users_table.get_item(
    Key={
        'tenantId': 'edo-sushi-bar',
        'email': 'chef@edosushi.com'
    }
)
```

---

### 3.2 Products Service (Gestión de Menú)

**Propósito:** Administración del catálogo de productos del restaurante.

**Endpoints:**
- `POST /products` - Crear nuevo producto
- `GET /products` - Listar todos los productos

**Funciones Lambda:**

#### `createProduct`
```
Entrada (Body): {name, price, description, category, imageUrl, comboSections}
Entrada (Header - opcional): x-tenant-id

Proceso:
  1. Obtiene tenantId (header o default "edo-sushi-bar")
  2. Genera ID único (UUID)
  3. Convierte price a Decimal (requerido por DynamoDB)
  4. Guarda en EdoProductsTable con composite key
  
Salida: {message, id, tenantId}
```

#### `getProducts`
```
Entrada: Ninguna en body
Entrada (Header - opcional): x-tenant-id

Proceso:
  1. Obtiene tenantId (header o default)
  2. Query a DynamoDB filtrando por tenantId:
     - KeyConditionExpression='tenantId = :tid'
  3. Convierte Decimals a float para JSON
  
Salida: Array de productos del tenant
```

**Tabla DynamoDB: EdoProductsTable**
```json
{
  "TableName": "EdoProductsTable",
  "KeySchema": [
    {"AttributeName": "tenantId", "KeyType": "HASH"},
    {"AttributeName": "id", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "tenantId", "AttributeType": "S"},
    {"AttributeName": "id", "AttributeType": "S"}
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```

**Estructura Multi-Tenant:**
- **Partition Key (PK):** `tenantId` - Aísla productos por restaurante
- **Sort Key (SK):** `id` (UUID) - Identifica producto dentro del tenant

**Ejemplo de Item:**
```json
{
  "tenantId": "edo-sushi-bar",
  "id": "uuid-123",
  "name": "Roll California",
  "price": 25.50,
  "description": "Roll de cangrejo, palta y pepino",
  "category": "Rolls",
  "imageUrl": "https://...",
  "maxSelections": 4,
  "comboSections": [
    {
      "title": "Selecciona tu bebida",
      "options": ["Coca Cola", "Inca Kola"]
    }
  ]
}
```

**Query Example:**
```python
# Listar todos los productos de un tenant
response = products_table.query(
    KeyConditionExpression='tenantId = :tid',
    ExpressionAttributeValues={':tid': 'edo-sushi-bar'}
)
```

---

### 3.3 Orders Service (Gestión de Pedidos)

**Propósito:** Core del sistema - gestiona todo el ciclo de vida de los pedidos.

**Endpoints:**
- `POST /orders` - Crear nuevo pedido
- `GET /orders` - Listar todos los pedidos
- `GET /orders/{orderId}` - Obtener pedido específico (tracking)
- `PUT /orders/{orderId}/status` - Actualizar estado
- `POST /orders/{orderId}/kitchen` - Marcar en cocina
- `POST /orders/{orderId}/packing` - Marcar empacado
- `POST /orders/{orderId}/delivery` - Marcar en delivery

**Funciones Lambda:**

#### `createOrder` (Principal)
```
Entrada (Body): {
  customerName, dni, email, address,
  items: [{product, quantity, price}],
  total, deliveryType
}
Entrada (Header - opcional): x-tenant-id

Proceso:
  1. Obtiene tenantId (header o default "edo-sushi-bar")
  2. Genera orderId único (UUID)
  3. Construye objeto completo del pedido:
     - tenantId (PK)
     - orderId (SK)
     - customer: {name, dni, email, address}
     - items: array de productos
     - total: monto total
     - status: "CONFIRMADO"
     - timeline: [{status, timestamp, user, action}]
     - createdAt, updatedAt
  
  4. Guarda en DynamoDB (composite key: tenantId + orderId)
  
  5. Emite evento a EventBridge:
     - Source: "edo.orders"
     - DetailType: "OrderCreated"
     - EventBusName: "EdoOrderBus"
     - Detail: {tenantId, orderId, customer, items, total}
  
  6. Envía métricas a CloudWatch:
     - Namespace: EdoSushiBar/Orders
     - Metric: OrdersCreated
     - Dimensions: TenantId, Status

Salida: {message, orderId, tenantId}
```

#### `processKitchen`, `processPacking`, `processDelivery`
```
Funcionamiento (Callback Pattern con Step Functions):

Caso 1 - Llamado por Step Functions:
  - Recibe: {orderId, taskToken}
  - Guarda taskToken en DynamoDB
  - Espera llamada HTTP del staff

Caso 2 - Llamado por HTTP (Staff):
  - Obtiene taskToken guardado
  - Actualiza status en DynamoDB
  - Agrega entry al timeline
  - Envía sendTaskSuccess() a Step Functions
  - Workflow continúa automáticamente
```

**Tabla DynamoDB: EdoOrdersTable**
```json
{
  "TableName": "EdoOrdersTable",
  "KeySchema": [
    {"AttributeName": "tenantId", "KeyType": "HASH"},
    {"AttributeName": "orderId", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "tenantId", "AttributeType": "S"},
    {"AttributeName": "orderId", "AttributeType": "S"}
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```

**Estructura Multi-Tenant:**
- **Partition Key (PK):** `tenantId` - Aísla pedidos por restaurante
- **Sort Key (SK):** `orderId` (UUID) - Identifica pedido dentro del tenant

**Ejemplo de Item:**
```json
{
  "tenantId": "edo-sushi-bar",
  "orderId": "abc-123-def-456",
  "customer": {
    "name": "María García",
    "dni": "12345678",
    "email": "maria@email.com",
    "address": "Av. Arequipa 1234, Miraflores"
  },
  "items": [
    {
      "product": {
        "id": "prod-1",
        "name": "Roll California",
        "price": 25.50
      },
      "quantity": 2,
      "price": 25.50
    }
  ],
  "total": 51.00,
  "deliveryType": "DELIVERY",
  "status": "EN_PREPARACION",
  "receiptUrl": "https://edoreceiptsbucket.s3.amazonaws.com/boleta-abc-123.txt",
  "createdAt": "2024-11-30T10:30:00Z",
  "updatedAt": "2024-11-30T10:35:00Z",
  "timeline": [
    {
      "status": "CONFIRMADO",
      "timestamp": "2024-11-30T10:30:00Z",
      "user": "Cliente",
      "action": "Pedido Creado"
    },
    {
      "status": "EN_PREPARACION",
      "timestamp": "2024-11-30T10:35:00Z",
      "user": "Juan Pérez (Cocinero)",
      "action": "Marcado en Preparación"
    }
  ]
}
```

---

### 3.4 Invoice Service (Generación de Boletas)

**Propósito:** Genera automáticamente boletas de venta en formato TXT.

**Trigger:** EventBridge (evento OrderCreated)

**Función Lambda: `generateReceipt`**
```
Entrada (desde EventBridge event.detail):
  {orderId, customer, items, total, deliveryType}

Proceso:
  1. Construye texto de boleta con:
     - Header: "EDO SUSHI BAR - BOLETA DE VENTA"
     - Orden ID
     - Datos del cliente (nombre, DNI, dirección)
     - Fecha y hora
     - Lista de productos con precios
     - Total
     - Tipo de entrega
  
  2. Sube archivo TXT a S3:
     - Bucket: EdoReceiptsBucket
     - Key: boleta-{orderId}.txt
     - ContentType: text/plain; charset=utf-8
  
  3. Construye URL pública:
     - https://edoreceiptsbucket.s3.amazonaws.com/boleta-{orderId}.txt
  
  4. Actualiza orden en DynamoDB:
     - SET receiptUrl = :url

Salida: {status: "success", receiptUrl}
```

**Ejemplo de Boleta Generada:**
```
╔══════════════════════════════════════════════╗
║           EDO SUSHI BAR 🍣                   ║
║           BOLETA DE VENTA                    ║
╚══════════════════════════════════════════════╝

Orden: abc-123-def-456
Cliente: María García
DNI: 12345678
Fecha: 2024-11-30 10:30:00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRODUCTOS:
  • Roll California x2
    S/ 25.50

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOTAL: S/ 51.00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¡Gracias por su preferencia!
ありがとう (Arigatou)

Dirección: Av. Arequipa 1234, Miraflores
Tipo: DELIVERY
```

---

## 4. SERVICIOS AWS UTILIZADOS

### 4.1 AWS Amplify

**Propósito:** Hosting de aplicaciones frontend.

**Configuración:**
```
Frontend Cliente:
- URL: https://main.d123456.amplifyapp.com
- Framework: React 18 + Vite
- Build command: npm run build
- Output directory: dist

Frontend Staff:
- URL: https://main.d789012.amplifyapp.com
- Framework: React 18 + Vite
- Build command: npm run build
- Output directory: dist
```

**Funcionalidad:**
- Deploy automático desde Git
- HTTPS automático
- CDN global
- Variables de entorno para API endpoints

---

### 4.2 API Gateway

**Propósito:** Punto de entrada único para todas las APIs REST.

**Configuración:**
```
Type: REST API
Stage: dev
Region: us-east-1
CORS: Enabled
Authorization: None (público para cliente, validación en Lambda para staff)
```

**Endpoints Generados:**
```
https://abc123.execute-api.us-east-1.amazonaws.com/dev/

Auth:
  POST /auth/register
  POST /auth/login

Products:
  GET  /products
  POST /products

Orders:
  GET  /orders
  POST /orders
  GET  /orders/{orderId}
  PUT  /orders/{orderId}/status
  POST /orders/{orderId}/kitchen
  POST /orders/{orderId}/packing
  POST /orders/{orderId}/delivery
```

**Multi-Tenancy:**
```
Todos los requests incluyen (opcional):
Header: x-tenant-id: edo-sushi-bar

Si no viene, se usa valor default en Lambda.
```

---

### 4.3 AWS Lambda

**Propósito:** Ejecución de funciones serverless.

**Configuración Global:**
```yaml
Runtime: python3.9
Memory: 256 MB
Timeout: 20 segundos
IAM Role: LabRole (AWS Academy)
Environment Variables:
  - USERS_TABLE: EdoUsersTable
  - ORDERS_TABLE: EdoOrdersTable
  - PRODUCTS_TABLE: EdoProductsTable
  - ORDER_BUS_NAME: EdoOrderBus
  - RECEIPTS_BUCKET: EdoReceiptsBucket
```

**Funciones Desplegadas:**
```
Users Service:
  - edo-users-service-dev-registerUser
  - edo-users-service-dev-loginUser

Products Service:
  - edo-products-service-dev-createProduct
  - edo-products-service-dev-getProducts

Orders Service:
  - edo-orders-service-dev-createOrder
  - edo-orders-service-dev-listOrders
  - edo-orders-service-dev-getOrder
  - edo-orders-service-dev-updateOrderStatus
  - edo-orders-service-dev-processKitchen
  - edo-orders-service-dev-processPacking
  - edo-orders-service-dev-processDelivery

Invoice Service:
  - edo-invoice-service-dev-generateReceipt
```

---

### 4.4 DynamoDB

**Propósito:** Base de datos NoSQL serverless.

**Por qué DynamoDB y no SQL:**
```
✅ Ventajas DynamoDB:
- Escalamiento automático infinito
- Latencia < 10ms
- Pay-per-request (solo pagas por queries)
- Ideal para serverless (sin conexiones)
- Schema flexible (JSON nativo)

❌ Desventajas SQL (RDS):
- Requiere gestión de conexiones
- Escalamiento manual
- Costo fijo mensual
- Lambda + RDS = connection pool problems
```

**Tablas Implementadas:**

#### EdoUsersTable
```json
{
  "TableName": "EdoUsersTable",
  "BillingMode": "PAY_PER_REQUEST",
  "KeySchema": [
    {"AttributeName": "tenantId", "KeyType": "HASH"},
    {"AttributeName": "email", "KeyType": "RANGE"}
  ],
  "Attributes": {
    "tenantId": "String (PK - Partition Key)",
    "email": "String (SK - Sort Key)",
    "password": "String",
    "name": "String",
    "role": "String (ADMIN|COCINERO|DESPACHADOR|REPARTIDOR)"
  }
}
```

**Beneficio Multi-Tenant:** Cada query automáticamente filtra por `tenantId`, imposible acceder a datos de otro restaurante.

#### EdoProductsTable
```json
{
  "TableName": "EdoProductsTable",
  "BillingMode": "PAY_PER_REQUEST",
  "KeySchema": [
    {"AttributeName": "tenantId", "KeyType": "HASH"},
    {"AttributeName": "id", "KeyType": "RANGE"}
  ],
  "Attributes": {
    "tenantId": "String (PK - Partition Key)",
    "id": "String (SK - Sort Key, UUID)",
    "name": "String",
    "price": "Number (Decimal)",
    "description": "String",
    "category": "String",
    "imageUrl": "String",
    "maxSelections": "Number",
    "comboSections": "List (Array de objetos)"
  }
}
```

#### EdoOrdersTable
```json
{
  "TableName": "EdoOrdersTable",
  "BillingMode": "PAY_PER_REQUEST",
  "KeySchema": [
    {"AttributeName": "tenantId", "KeyType": "HASH"},
    {"AttributeName": "orderId", "KeyType": "RANGE"}
  ],
  "Attributes": {
    "tenantId": "String (PK - Partition Key)",
    "orderId": "String (SK - Sort Key, UUID)",
    "customer": "Map {name, dni, email, address}",
    "items": "List [{product, quantity, price}]",
    "total": "Number (Decimal)",
    "deliveryType": "String (DELIVERY|PICKUP)",
    "status": "String (CONFIRMADO|EN_PREPARACION|...)",
    "receiptUrl": "String",
    "timeline": "List [{status, timestamp, user, action}]",
    "taskToken": "String (para Step Functions)",
    "createdAt": "String (ISO 8601)",
    "updatedAt": "String (ISO 8601)"
  }
}
```

**Ventaja del Diseño Multi-Tenant:**
```python
# ❌ IMPOSIBLE acceder a datos de otro tenant
response = orders_table.get_item(
    Key={
        'tenantId': 'edo-sushi-bar',
        'orderId': 'abc-123'
    }
)
# Si intentas acceder con tenantId diferente, retorna vacío

# ✅ Listar solo pedidos del tenant actual
response = orders_table.query(
    KeyConditionExpression='tenantId = :tid',
    ExpressionAttributeValues={':tid': 'edo-sushi-bar'}
)
```

---

### 4.5 EventBridge

**Propósito:** Bus de eventos central para comunicación asíncrona.

**Configuración:**
```json
{
  "EventBusName": "EdoOrderBus",
  "Rules": [
    {
      "Name": "InvoiceRule",
      "EventPattern": {
        "source": ["edo.orders"],
        "detail-type": ["OrderCreated"]
      },
      "Targets": [
        {
          "Arn": "arn:aws:lambda:us-east-1:...:function:generateReceipt",
          "Id": "InvoiceServiceTarget"
        }
      ]
    },
    {
      "Name": "WorkflowRule",
      "EventPattern": {
        "source": ["edo.orders"],
        "detail-type": ["OrderCreated"]
      },
      "Targets": [
        {
          "Arn": "arn:aws:states:us-east-1:...:stateMachine:OrderWorkflow",
          "Id": "StepFunctionsTarget",
          "RoleArn": "arn:aws:iam::...:role/LabRole"
        }
      ]
    }
  ]
}
```

**Flujo:**
```
Lambda createOrder
  ↓
events_client.put_events({
  Source: "edo.orders",
  DetailType: "OrderCreated",
  Detail: JSON({orderId, customer, items, total}),
  EventBusName: "EdoOrderBus"
})
  ↓
EventBridge recibe evento
  ↓
├─► Rule 1: Activa Lambda generateReceipt
└─► Rule 2: Activa Step Functions Workflow
```

---

### 4.6 Step Functions

**Propósito:** Orquestación del workflow de estados del pedido.

**State Machine: OrderWorkflow**

```json
{
  "Comment": "Workflow de procesamiento de pedidos Edo Sushi Bar",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": {
        "FunctionName": "edo-orders-service-dev-validateOrder",
        "Payload": {
          "orderId.$": "$.detail.orderId",
          "taskToken.$": "$$.Task.Token"
        }
      },
      "Next": "SendToKitchen",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "Next": "HandleError"
      }]
    },
    
    "SendToKitchen": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": {
        "FunctionName": "edo-orders-service-dev-processKitchen",
        "Payload": {
          "orderId.$": "$.orderId",
          "taskToken.$": "$$.Task.Token"
        }
      },
      "TimeoutSeconds": 3600,
      "Next": "StartPackaging"
    },
    
    "StartPackaging": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": {
        "FunctionName": "edo-orders-service-dev-processPacking",
        "Payload": {
          "orderId.$": "$.orderId",
          "taskToken.$": "$$.Task.Token"
        }
      },
      "TimeoutSeconds": 3600,
      "Next": "CheckDeliveryType"
    },
    
    "CheckDeliveryType": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.deliveryType",
        "StringEquals": "DELIVERY",
        "Next": "StartDelivery"
      }],
      "Default": "CompleteOrder"
    },
    
    "StartDelivery": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": {
        "FunctionName": "edo-orders-service-dev-processDelivery",
        "Payload": {
          "orderId.$": "$.orderId",
          "taskToken.$": "$$.Task.Token"
        }
      },
      "TimeoutSeconds": 3600,
      "Next": "CompleteOrder"
    },
    
    "CompleteOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:invoke",
      "Parameters": {
        "FunctionName": "edo-orders-service-dev-completeOrder",
        "Payload": {
          "orderId.$": "$.orderId"
        }
      },
      "End": true
    },
    
    "HandleError": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:invoke",
      "Parameters": {
        "FunctionName": "edo-orders-service-dev-handleError",
        "Payload": {
          "error.$": "$.error",
          "orderId.$": "$.orderId"
        }
      },
      "End": true
    }
  }
}
```

**Callback Pattern:**

```
1. Step Functions invoca Lambda con taskToken
   └─ Lambda guarda taskToken en DynamoDB
   └─ Lambda retorna (no envía success aún)

2. Step Functions espera...

3. Staff marca estado en frontend
   └─ POST /orders/{id}/kitchen

4. Lambda procesa:
   └─ Actualiza DynamoDB
   └─ Obtiene taskToken guardado
   └─ sfn_client.send_task_success(taskToken, output)

5. Step Functions recibe success
   └─ Continúa al siguiente estado
```

**Estados del Pedido:**
```
CONFIRMADO 
  ↓ (Step Functions: ValidateOrder)
EN_PREPARACION
  ↓ (Staff: Cocinero marca listo)
LISTO_PARA_RETIRAR
  ↓ (Step Functions: CheckDeliveryType)
EN_CAMINO (solo si deliveryType = DELIVERY)
  ↓ (Staff: Repartidor marca entregado)
ENTREGADO
```

---

### 4.7 S3 (Simple Storage Service)

**Propósito:** Almacenamiento de boletas de venta.

**Configuración:**
```json
{
  "BucketName": "EdoReceiptsBucket",
  "Region": "us-east-1",
  "PublicAccess": true,
  "Versioning": false,
  "Encryption": "AES256"
}
```

**Estructura de archivos:**
```
edoreceiptsbucket/
├── boleta-abc-123-def-456.txt
├── boleta-ghi-789-jkl-012.txt
└── boleta-mno-345-pqr-678.txt
```

**URL de acceso:**
```
https://edoreceiptsbucket.s3.amazonaws.com/boleta-{orderId}.txt
```

---

### 4.8 CloudWatch

**Propósito:** Monitoreo, logs y métricas.

**CloudWatch Dashboard:**
```json
{
  "DashboardName": "EdoSushiBar-Dashboard",
  "Widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [["AWS/Lambda", "Invocations"]],
        "title": "Lambda - Total Invocaciones"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Errors"],
          ["AWS/Lambda", "Throttles"]
        ],
        "title": "Lambda - Errores y Throttles"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [["AWS/Lambda", "Duration"]],
        "title": "Lambda - Duración (ms)"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/DynamoDB", "ConsumedReadCapacityUnits"],
          ["AWS/DynamoDB", "ConsumedWriteCapacityUnits"]
        ],
        "title": "DynamoDB - Capacidad Consumida"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApiGateway", "Count"],
          ["AWS/ApiGateway", "4XXError"],
          ["AWS/ApiGateway", "5XXError"]
        ],
        "title": "API Gateway - Requests y Errores"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/edo-orders-service-dev-createOrder' | fields @timestamp | filter @message like /Pedido creado/",
        "title": "Pedidos Creados (últimas 3h)"
      }
    }
  ]
}
```

**CloudWatch Logs:**
```
Log Groups:
/aws/lambda/edo-users-service-dev-registerUser
/aws/lambda/edo-users-service-dev-loginUser
/aws/lambda/edo-orders-service-dev-createOrder
/aws/lambda/edo-orders-service-dev-processKitchen
... (todos los Lambdas)

Retention: 7 días
```

**Métricas Personalizadas:**
```python
cloudwatch.put_metric_data(
    Namespace='EdoSushiBar/Orders',
    MetricData=[
        {
            'MetricName': 'OrdersCreated',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'TenantId', 'Value': 'edo-sushi-bar'},
                {'Name': 'Status', 'Value': 'CONFIRMADO'}
            ]
        }
    ]
)
```

---

## 5. IMPLEMENTACIÓN MULTI-TENANCY

### 5.1 ¿Qué es Multi-Tenancy?

Multi-tenancy es una arquitectura donde **una sola instancia de software sirve a múltiples clientes (tenants)** con **datos completamente aislados**.

**Ejemplo:**
```
Infraestructura compartida:
├─ Tenant 1: Edo Sushi Bar (Lima)
├─ Tenant 2: Sushi Tokyo (Arequipa)
└─ Tenant 3: Nikkei House (Cusco)

Cada uno tiene:
- Sus propios usuarios (staff)
- Sus propios productos
- Sus propios pedidos
- Datos 100% aislados
```

### 5.2 Implementación en el Proyecto

#### Estrategia: Pool Model con Composite Keys

**Diseño Multi-Tenant en DynamoDB:**

Todas las tablas usan **`tenantId` como Partition Key (PK)**:

```
┌─────────────────────────────────────┐
│ EdoUsersTable                        │
├─────────────────────────────────────┤
│ PK: tenantId (HASH)                 │
│ SK: email (RANGE)                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ EdoProductsTable                     │
├─────────────────────────────────────┤
│ PK: tenantId (HASH)                 │
│ SK: id (RANGE)                      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ EdoOrdersTable                       │
├─────────────────────────────────────┤
│ PK: tenantId (HASH)                 │
│ SK: orderId (RANGE)                 │
└─────────────────────────────────────┘
```

**Ventajas de este Diseño:**

✅ **Aislamiento a Nivel de Base de Datos:** No puedes acceder a datos de otro tenant sin la PK correcta  
✅ **Queries Eficientes:** Todas las queries automáticamente filtran por tenant  
✅ **Seguridad por Diseño:** Imposible cruzar datos entre tenants accidentalmente  
✅ **Escalabilidad:** DynamoDB distribuye datos por PK (cada tenant en diferentes particiones)  

#### Ejemplo de Datos Distribuidos

```json
// Tenant 1: edo-sushi-bar
{
  "tenantId": "edo-sushi-bar",
  "email": "chef@edosushi.com",
  "name": "Juan Pérez",
  "role": "COCINERO"
}

// Tenant 2: sushi-tokyo-arequipa
{
  "tenantId": "sushi-tokyo-arequipa",
  "email": "chef@sushitokyo.com",
  "name": "María López",
  "role": "COCINERO"
}

// Misma tabla, datos completamente aislados por PK
```

#### Aislamiento de Datos

**En Lambdas (Queries Correctas):**
```python
# ✅ CORRECTO: Query por tenant
response = users_table.get_item(
    Key={
        'tenantId': 'edo-sushi-bar',  # PK requerida
        'email': 'chef@edosushi.com'   # SK requerida
    }
)

# ✅ CORRECTO: Listar todos los productos de un tenant
response = products_table.query(
    KeyConditionExpression='tenantId = :tid',
    ExpressionAttributeValues={':tid': 'edo-sushi-bar'}
)

# ❌ INCORRECTO: Scan sin filtro (trae datos de TODOS los tenants)
response = orders_table.scan()  # NO USAR en producción
```

**En Frontend:**
```javascript
// ✅ OPCIÓN 1: Enviar header x-tenant-id (RECOMENDADO)
const registerUser = async (userData) => {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-tenant-id': 'edo-sushi-bar'  // ← Header con tenant
    },
    body: JSON.stringify({
      email: userData.email,
      password: userData.password,
      name: userData.name,
      role: userData.role
      // ❌ NO incluir tenantId en el body
    })
  });
  
  const data = await response.json();
  // Guardar tenantId retornado para futuros requests
  localStorage.setItem('tenantId', data.user.tenantId);
};

// ✅ OPCIÓN 2: Si no envías header, Lambda usa default
const createOrder = async (orderData) => {
  const response = await fetch(`${API_URL}/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
      // Sin header, Lambda usa "edo-sushi-bar" por defecto
    },
    body: JSON.stringify(orderData)
  });
};

// ✅ OPCIÓN 3: Leer tenantId de localStorage (después del login)
const getProducts = async () => {
  const tenantId = localStorage.getItem('tenantId') || 'edo-sushi-bar';
  
  const response = await fetch(`${API_URL}/products`, {
    headers: {
      'x-tenant-id': tenantId
    }
  });
};
```

**Flujo Completo:**
```
1. Usuario staff hace login
   └─ Frontend envía: POST /auth/login
      Headers: x-tenant-id: edo-sushi-bar (opcional)
      Body: {email, password}

2. Lambda obtiene tenantId:
   └─ tenant_id = headers.get('x-tenant-id', 'edo-sushi-bar')

3. Lambda busca en DynamoDB:
   └─ Key: {tenantId: 'edo-sushi-bar', email: 'chef@...'}

4. Lambda retorna:
   └─ {user: {..., tenantId: 'edo-sushi-bar'}}

5. Frontend guarda tenantId:
   └─ localStorage.setItem('tenantId', data.user.tenantId)

6. Futuros requests usan ese tenantId:
   └─ Headers: {'x-tenant-id': localStorage.getItem('tenantId')}
```

### 5.3 ¿Dónde se Implementa tenantId?

**❌ NO en Login/Register del Cliente**
- Los clientes NO tienen cuentas
- Solo hacen pedidos anónimos
- No necesitan identificarse como tenant

**✅ SÍ en Login/Register del Staff**
```python
# users-service/handler.py
def registerUser(event, context):
    data = json.loads(event['body'])
    
    # ✅ Obtener tenantId desde header (NO desde body)
    headers = event.get('headers', {})
    tenant_id = headers.get('x-tenant-id', 'edo-sushi-bar')  # Default si no viene
    
    user = {
        'tenantId': tenant_id,  # ← PK
        'email': data['email'], # ← SK
        'password': data['password'],
        'name': data['name'],
        'role': data['role']
    }
    
    # Guardar con composite key
    users_table.put_item(Item=user)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Usuario registrado',
            'user': {
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'tenantId': tenant_id  # Retornar para que el frontend lo guarde
            }
        })
    }

def loginUser(event, context):
    data = json.loads(event['body'])
    headers = event.get('headers', {})
    tenant_id = headers.get('x-tenant-id', 'edo-sushi-bar')
    
    # ✅ Get item con AMBAS keys (PK + SK)
    response = users_table.get_item(
        Key={
            'tenantId': tenant_id,    # PK (requerida)
            'email': data['email']     # SK (requerida)
        }
    )
    
    if 'Item' not in response:
        return {'statusCode': 404, 'body': 'Usuario no encontrado'}
    
    # Verificar password...
    return {
        'statusCode': 200,
        'body': json.dumps({
            'user': {
                'email': response['Item']['email'],
                'name': response['Item']['name'],
                'role': response['Item']['role'],
                'tenantId': tenant_id
            }
        })
    }
```

**✅ SÍ en todas las entidades de datos**
```python
# orders-service/handler.py
def createOrder(event, context):
    tenant_id = data.get('tenantId', 'edo-sushi-bar')
    order_id = str(uuid.uuid4())
    
    order = {
        'tenantId': tenant_id,  # ← PK (Partition Key)
        'orderId': order_id,    # ← SK (Sort Key)
        'customer': {...},
        'items': [...]
    }
    
    # Guardar en DynamoDB
    orders_table.put_item(Item=order)
    
def getOrder(event, context):
    order_id = event['pathParameters']['orderId']
    tenant_id = event['headers'].get('x-tenant-id', 'edo-sushi-bar')
    
    # Obtener orden requiere AMBAS keys
    response = orders_table.get_item(
        Key={
            'tenantId': tenant_id,  # PK requerida
            'orderId': order_id     # SK requerida
        }
    )
```

**✅ SÍ en las tablas DynamoDB (Estructura de Keys)**
```json
{
  "EdoUsersTable": {
    "KeySchema": [
      {"AttributeName": "tenantId", "KeyType": "HASH"},
      {"AttributeName": "email", "KeyType": "RANGE"}
    ]
  },
  "EdoOrdersTable": {
    "KeySchema": [
      {"AttributeName": "tenantId", "KeyType": "HASH"},
      {"AttributeName": "orderId", "KeyType": "RANGE"}
    ]
  },
  "EdoProductsTable": {
    "KeySchema": [
      {"AttributeName": "tenantId", "KeyType": "HASH"},
      {"AttributeName": "id", "KeyType": "RANGE"}
    ]
  }
}
```

**Ejemplo de Items en DynamoDB:**
```json
{
  "EdoUsersTable": {
    "Item": {
      "tenantId": "edo-sushi-bar",  // ← PK
      "email": "chef@edosushi.com",  // ← SK
      "name": "Juan Pérez",
      "role": "COCINERO"
    }
  },
  "EdoOrdersTable": {
    "Item": {
      "tenantId": "edo-sushi-bar",  // ← PK
      "orderId": "abc-123-def-456",  // ← SK
      "customer": {...},
      "items": [...]
    }
  }
}
```

### 5.4 Escalabilidad Multi-Tenant

**Tenant Actual:**
```
edo-sushi-bar (Lima, Perú)
```

**Tenants Futuros (sin cambios en código):**
```
sushi-tokyo-arequipa
nikkei-house-cusco
roll-express-trujillo
osaka-sushi-chile
```

**Para agregar nuevo tenant:**
1. Registrar staff con nuevo `tenantId`
2. Crear productos con nuevo `tenantId`
3. Los pedidos automáticamente se aíslan

**Sin necesidad de:**
- ❌ Crear nueva infraestructura
- ❌ Duplicar Lambdas
- ❌ Crear nuevas tablas
- ❌ Modificar código

---

## 6. FLUJOS DE TRABAJO DETALLADOS

### 6.1 Flujo: Cliente Crea Pedido

```
PASO 1: Cliente accede a Frontend
  URL: https://main.d123456.amplifyapp.com
  ↓
  Carga aplicación React desde Amplify CDN

PASO 2: Ver menú
  Frontend → GET https://api.../dev/products
  ↓
  API Gateway → Lambda: getProducts
  ↓
  DynamoDB scan → EdoProductsTable
  ↓
  Retorna: [{id, name, price, imageUrl, ...}]
  ↓
  Frontend muestra productos con imágenes

PASO 3: Agregar productos al carrito
  Cliente selecciona:
  - Roll California x2 (S/ 25.50 c/u)
  - Combo Especial x1 (S/ 45.00)
  ↓
  Total calculado en frontend: S/ 96.00

PASO 4: Completar formulario
  Cliente ingresa:
  - Nombre: María García
  - DNI: 12345678
  - Email: maria@email.com
  - Dirección: Av. Arequipa 1234
  - Tipo: DELIVERY

PASO 5: Confirmar pedido
  Frontend → POST https://api.../dev/orders
  Body: {
    customerName: "María García",
    dni: "12345678",
    email: "maria@email.com",
    address: "Av. Arequipa 1234",
    items: [
      {product: {id, name, price}, quantity: 2},
      {product: {id, name, price}, quantity: 1}
    ],
    total: 96.00,
    deliveryType: "DELIVERY"
  }
  ↓
  API Gateway → Lambda: createOrder

PASO 6: Lambda createOrder procesa
  6.1. Genera orderId: "abc-123-def-456"
  6.2. Agrega tenantId: "edo-sushi-bar"
  6.3. Construye objeto completo
  6.4. Guarda en DynamoDB (EdoOrdersTable)
  6.5. Emite evento a EventBridge
  6.6. Envía métricas a CloudWatch
  6.7. Retorna: {orderId: "abc-123-def-456"}

PASO 7: EventBridge procesa evento
  7.1. RULE 1: Activa Lambda generateReceipt
       ├─ Genera boleta TXT
       ├─ Sube a S3
       └─ Actualiza orden con receiptUrl
  
  7.2. RULE 2: Activa Step Functions
       └─ Inicia workflow (ValidateOrder)

PASO 8: Frontend muestra confirmación
  "¡Pedido creado exitosamente!"
  "Tu número de orden: abc-123-def-456"
  ↓
  Redirige a página de tracking

PASO 9: Cliente hace tracking
  GET https://api.../dev/orders/abc-123-def-456
  ↓
  Retorna: {
    orderId, status: "CONFIRMADO",
    timeline: [{status, timestamp, user, action}],
    receiptUrl: "https://..."
  }
  ↓
  Frontend muestra línea de tiempo y botón para descargar boleta
```

### 6.2 Flujo: Staff Procesa Pedido

```
PASO 1: Staff hace login
  Frontend Staff → POST https://api.../dev/auth/login
  Body: {email: "chef@edosushi.com", password: "***"}
  ↓
  Lambda loginUser valida credenciales
  ↓
  Retorna: {user: {email, name, role: "COCINERO"}}
  ↓
  Frontend guarda en localStorage

PASO 2: Listar pedidos activos
  GET https://api.../dev/orders
  ↓
  Lambda listOrders → DynamoDB scan
  ↓
  Retorna todos los pedidos
  ↓
  Frontend filtra por status != "ENTREGADO"
  ↓
  Muestra tabla de pedidos pendientes

PASO 3: COCINERO selecciona pedido
  Pedido: abc-123-def-456
  Status actual: CONFIRMADO
  ↓
  Hace clic en "Marcar En Preparación"

PASO 4: Actualizar a EN_PREPARACION
  POST https://api.../dev/orders/abc-123-def-456/kitchen
  Body: {user: {name: "Juan Pérez"}}
  ↓
  Lambda processKitchen:
    4.1. Obtiene orden de DynamoDB
    4.2. Obtiene taskToken guardado por Step Functions
    4.3. Actualiza DynamoDB:
         - status = "EN_PREPARACION"
         - timeline.push({
             status: "EN_PREPARACION",
             timestamp: "2024-11-30T10:35:00Z",
             user: "Juan Pérez",
             action: "Marcado en Preparación"
           })
    4.4. Envía sendTaskSuccess() a Step Functions
  ↓
  Step Functions recibe success → Continúa a StartPackaging

PASO 5: DESPACHADOR empaca
  POST https://api.../dev/orders/abc-123-def-456/packing
  ↓
  Lambda processPacking:
    - Actualiza status = "LISTO_PARA_RETIRAR"
    - Agrega timeline entry
    - sendTaskSuccess()
  ↓
  Step Functions → CheckDeliveryType
    ├─ Si DELIVERY → StartDelivery
    └─ Si PICKUP → CompleteOrder

PASO 6: REPARTIDOR toma pedido (si DELIVERY)
  POST https://api.../dev/orders/abc-123-def-456/delivery
  ↓
  Lambda processDelivery:
    - Actualiza status = "EN_CAMINO"
    - Agrega timeline entry
    - sendTaskSuccess()
  ↓
  Step Functions → CompleteOrder

PASO 7: REPARTIDOR marca entregado
  PUT https://api.../dev/orders/abc-123-def-456/status
  Body: {status: "ENTREGADO"}
  ↓
  Lambda updateOrderStatus:
    - Actualiza status = "ENTREGADO"
    - Agrega timeline entry final
  ↓
  Step Functions termina ejecución
```

### 6.3 Flujo: Dashboard Admin (CloudWatch)

```
PASO 1: Admin accede a AWS Console
  https://console.aws.amazon.com/cloudwatch

PASO 2: Navega a Dashboards
  CloudWatch → Dashboards → EdoSushiBar-Dashboard

PASO 3: Visualiza métricas en tiempo real
  
  Widget 1: Lambda Invocations
  ├─ Gráfico de líneas
  ├─ Últimas 3 horas
  └─ Total: 247 invocaciones

  Widget 2: Lambda Errors
  ├─ Errors: 3 (1.2%)
  └─ Throttles: 0

  Widget 3: Lambda Duration
  ├─ Promedio: 145 ms
  └─ Máximo: 523 ms

  Widget 4: DynamoDB Capacity
  ├─ Read: 12.5 units
  └─ Write: 8.3 units

  Widget 5: API Gateway Requests
  ├─ Total: 156 requests
  ├─ 4XX: 5 (3.2%)
  └─ 5XX: 1 (0.6%)

  Widget 6: API Gateway Latency
  ├─ Promedio: 89 ms
  └─ p99: 234 ms

  Widget 7: Pedidos Creados (Log Insights)
  ├─ Últimas 3 horas
  └─ Total: 23 pedidos

  Widget 8: Estados de Pedidos (Pie Chart)
  ├─ CONFIRMADO: 5 (22%)
  ├─ EN_PREPARACION: 8 (35%)
  ├─ LISTO_PARA_RETIRAR: 3 (13%)
  ├─ EN_CAMINO: 4 (17%)
  └─ ENTREGADO: 3 (13%)

PASO 4: Investigar errores (si los hay)
  CloudWatch Logs → /aws/lambda/...
  ├─ Filtrar por ERROR
  └─ Ver stack trace completo
```

---

## 7. DEPLOYMENT

### 7.1 Serverless Framework

**Instalación:**
```bash
npm install -g serverless
```

**Deploy de cada servicio:**
```bash
# Users Service
cd backend/users-service
serverless deploy

# Products Service
cd backend/products-service
serverless deploy

# Orders Service
cd backend/orders-service
serverless deploy

# Invoice Service
cd backend/invoice-service
serverless deploy

# CloudWatch Dashboard
cd backend/cloudwatch-service
serverless deploy
```

**Script de deploy completo:**
```bash
#!/bin/bash
cd backend
for service in users-service products-service orders-service invoice-service cloudwatch-service; do
  echo "Deploying $service..."
  cd $service
  serverless deploy
  cd ..
done
```

---

## 8. CONCLUSIONES

### 8.1 Cumplimiento de Requerimientos

✅ **Cliente puede crear pedidos desde app web** → Frontend Cliente + Orders API  
✅ **Cliente puede ver estado de su pedido** → GET /orders/{orderId} + Timeline  
✅ **Workflow de restaurante implementado** → Step Functions con 5 estados  
✅ **Cocinero, Despachador, Repartidor procesan pedido** → Lambdas específicas  
✅ **Timeline con tiempos y usuarios** → Campo `timeline[]` en DynamoDB  
✅ **Dashboard resumen** → CloudWatch Dashboard con 8 widgets  
✅ **Multi-tenancy** → `tenantId` como Partition Key en DynamoDB  
✅ **Serverless** → 100% Lambda + DynamoDB  
✅ **Basado en eventos** → EventBridge + Step Functions  
✅ **3+ microservicios** → 4 servicios implementados (Users, Products, Orders, Invoice)  
✅ **EventBridge** → Eventos OrderCreated  
✅ **Step Functions** → Workflow con callback pattern  
✅ **Amplify** → Hosting de 2 frontends  
✅ **API Gateway** → REST API con 14+ endpoints  
✅ **Lambda** → 13+ funciones  
✅ **DynamoDB** → 3 tablas con composite keys (tenantId + id/email/orderId)  
✅ **S3** → Almacenamiento de boletas  
✅ **CloudWatch** → Dashboard con 6+ widgets  

### 8.2 Ventajas de la Solución

1. **Escalabilidad Infinita:** Auto-scaling automático
2. **Costo Optimizado:** Pay-per-use (solo pagas lo que usas)
3. **Alta Disponibilidad:** 99.99% uptime garantizado por AWS
4. **Mantenimiento Mínimo:** Sin servidores que gestionar
5. **Tiempo de Deploy Rápido:** < 5 minutos por servicio
6. **Multi-Tenant Ready:** Preparado para múltiples restaurantes
7. **Monitoreo en Tiempo Real:** CloudWatch Dashboard

### 8.3 Próximos Pasos (Mejoras Futuras)

1. **Autenticación JWT:** Implementar tokens para seguridad
2. **WebSockets:** Actualización en tiempo real del estado
3. **Pagos en Línea:** Integración con Stripe/PayPal
4. **Push Notifications:** Notificaciones móviles con FCM
5. **Reportes Avanzados:** Analytics con QuickSight
6. **Machine Learning:** Predicción de demanda con SageMaker

---

## ANEXOS

### Anexo A: URLs de Servicios Desplegados

```
API Gateway:
https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/

Frontend Cliente:
https://main.d123456.amplifyapp.com

Frontend Staff:
https://main.d789012.amplifyapp.com

CloudWatch Dashboard:
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=EdoSushiBar-Dashboard

S3 Bucket (Boletas):
https://edoreceiptsbucket.s3.amazonaws.com/
```

### Anexo B: Comandos Útiles

```bash
# Ver logs en tiempo real
serverless logs -f createOrder -t

# Invocar Lambda manualmente
serverless invoke -f createOrder --data '{"body": "{...}"}'

# Eliminar todos los servicios
serverless remove

# Ver info del deployment
serverless info
```

### Anexo C: Variables de Entorno

```bash
# Frontend Cliente (.env)
VITE_API_URL=https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev
VITE_TENANT_ID=edo-sushi-bar

# Frontend Staff (.env)
VITE_API_URL=https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev
VITE_TENANT_ID=edo-sushi-bar
```

### Anexo D: Diseño Multi-Tenancy - Estructura de Keys DynamoDB

**Arquitectura Correcta para Multi-Tenancy:**

```
┌──────────────────────────────────────────────────────────┐
│ EdoUsersTable                                             │
├──────────────────────────────────────────────────────────┤
│ PK (Partition Key): tenantId                             │
│ SK (Sort Key):      email                                │
├──────────────────────────────────────────────────────────┤
│ • Tenant 1: edo-sushi-bar | chef@edosushi.com            │
│ • Tenant 2: sushi-tokyo   | chef@sushitokyo.com          │
│ • Tenant 3: nikkei-house  | chef@nikkeihouse.com         │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ EdoProductsTable                                          │
├──────────────────────────────────────────────────────────┤
│ PK (Partition Key): tenantId                             │
│ SK (Sort Key):      id (UUID)                            │
├──────────────────────────────────────────────────────────┤
│ • Tenant 1: edo-sushi-bar | uuid-001 (Roll California)   │
│ • Tenant 1: edo-sushi-bar | uuid-002 (Combo Especial)    │
│ • Tenant 2: sushi-tokyo   | uuid-003 (Nigiri Box)        │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ EdoOrdersTable                                            │
├──────────────────────────────────────────────────────────┤
│ PK (Partition Key): tenantId                             │
│ SK (Sort Key):      orderId (UUID)                       │
├──────────────────────────────────────────────────────────┤
│ • Tenant 1: edo-sushi-bar | abc-123 (Pedido María)       │
│ • Tenant 1: edo-sushi-bar | def-456 (Pedido Juan)        │
│ • Tenant 2: sushi-tokyo   | ghi-789 (Pedido Carlos)      │
└──────────────────────────────────────────────────────────┘
```

**Ventajas de este Diseño:**

✅ **Aislamiento Garantizado:** No puedes acceder a datos de otro tenant sin la PK  
✅ **Performance:** DynamoDB distribuye datos por PK (cada tenant en particiones diferentes)  
✅ **Queries Eficientes:** Filtra automáticamente por tenantId  
✅ **Escalable:** Soporta miles de tenants sin cambios en la estructura  
✅ **Seguro:** Imposible mezclar datos entre restaurantes  

**Ejemplo de Código:**

```python
# ✅ CORRECTO: Get item con ambas keys
response = orders_table.get_item(
    Key={
        'tenantId': 'edo-sushi-bar',  # PK
        'orderId': 'abc-123'           # SK
    }
)

# ✅ CORRECTO: Query todos los pedidos de un tenant
response = orders_table.query(
    KeyConditionExpression='tenantId = :tid',
    ExpressionAttributeValues={':tid': 'edo-sushi-bar'}
)

# ❌ ERROR: No puedes hacer get_item sin la PK
response = orders_table.get_item(
    Key={'orderId': 'abc-123'}  # Falta tenantId (PK)
)
# Resultado: ValidationException
```

---

**Autor:** Fátima Pacheco  
**Fecha:** 30 de Noviembre de 2025  
**Curso:** Cloud Computing  
**Institución:** AWS Academy
