# 🍣 Edo Sushi Bar - Sistema de Gestión de Pedidos

Sistema serverless multi-tenant para gestión de pedidos usando AWS Step Functions, DynamoDB, EventBridge y Lambda.

## 🏗️ Arquitectura

Este proyecto implementa un flujo de trabajo humano para procesar pedidos:

```
Cliente → Cocina → Empaquetado → Delivery → Completado
```

### Componentes Principales

1. **DynamoDB Tables**
   - `EdoUsersTable`: Usuarios con autenticación custom (email, password, role, tenant_id)
   - `EdoOrdersTable`: Pedidos multi-tenant con GSI para búsqueda por estado

2. **EventBridge**
   - `EdoOrderBus`: Event Bus para arquitectura Event-Driven

3. **Step Functions**
   - `EdoOrderWorkflow`: Orquesta el flujo de trabajo con callback pattern

4. **Lambda Functions**
   - `authLogin`: Autenticación custom
   - `createOrder`: Crea pedido e inicia workflow
   - `getOrders`: Lista pedidos según rol
   - `updateOrderStep`: Avanza workflow usando taskToken
   - `notifyStaff`: Notifica al staff sobre cambios

## 🚀 Deployment

### Prerrequisitos

```bash
# Instalar Python 3.11
# Instalar AWS CLI y configurar credenciales
aws configure
```

### Instalación

```bash
# Instalar dependencias
npm install

# Deploy a DEV
npm run deploy:dev

# Deploy a PROD
npm run deploy:prod
```

### Variables de Entorno

Crear archivo `.env` (opcional):

```bash
JWT_SECRET=tu-secret-key-super-seguro
```

## 📊 Callback Pattern - waitForTaskToken

El flujo usa el **Callback Pattern** de Step Functions:

### ¿Cómo funciona?

1. **Step Function se pausa**: Cuando llega a un estado con `.waitForTaskToken`, el Step Function se pausa y genera un un `taskToken` único.

2. **TaskToken se almacena**: El token se guarda en DynamoDB junto con el pedido.

3. **Staff recibe notificación**: El staff es notificado que hay una acción pendiente.

4. **Staff completa la tarea**: El staff llama al endpoint `/orders/advance` con el `taskToken`.

5. **Workflow continúa**: La función `updateOrderStep` ejecuta `SendTaskSuccess` con el token, desbloqueando el Step Function.

### Ejemplo de Flujo

```javascript
// 1. Cliente crea pedido
POST /orders
{
  "items": [...],
  "total": 45.50,
  "tenant_id": "sede-miraflores"
}

// 2. Step Function inicia y se pausa en WaitCocinero
// Se genera taskToken: "AQC8A3VuZ2luZ..."

// 3. Cocinero ve pedido en dashboard y lo acepta
POST /orders/advance
{
  "order_id": "abc-123",
  "tenant_id": "sede-miraflores",
  "task_token": "AQC8A3VuZ2luZ...",
  "step": "COOKING",
  "notes": "Iniciando preparación"
}

// 4. Step Function continúa al siguiente estado
```

## 🔐 Autenticación

Este proyecto usa **autenticación custom** (sin AWS Cognito):

```javascript
// Login
POST /auth/login
{
  "email": "chef@edosushi.com",
  "password": "secret123"
}

// Respuesta
{
  "token": "fake-jwt-...",
  "role": "STAFF",
  "tenant_id": "sede-miraflores"
}

// Usar token en headers
Authorization: Bearer fake-jwt-...
```

## 📝 API Endpoints

### Autenticación
- `POST /auth/login` - Login de usuario

### Pedidos
- `POST /orders` - Crear pedido (CLIENTE)
- `GET /orders` - Listar pedidos (CLIENTE: propios, STAFF: todos del tenant)
- `POST /orders/advance` - Avanzar workflow (STAFF)

## 🗄️ Estructura de Datos

### Usuario (EdoUsersTable)

```json
{
  "email": "chef@edosushi.com",
  "password": "hashed-password",
  "role": "STAFF",
  "tenant_id": "sede-miraflores"
}
```

### Pedido (EdoOrdersTable)

```json
{
  "tenant_id": "sede-miraflores",
  "order_id": "abc-123",
  "customer_email": "cliente@example.com",
  "items": [...],
  "total": 45.50,
  "status": "COOKING",
  "task_token": "AQC8A3VuZ2luZ...",
  "created_at": 1700000000000,
  "updated_at": 1700000000000
}
```

## 📈 Monitoreo

Ver logs de una función:

```bash
npm run logs -- authLogin -- --tail
```

Invocar función manualmente:

```bash
npm run invoke -- authLogin -- --data '{"body": "{\"email\":\"test@test.com\",\"password\":\"test\"}"}'
```

## 🧪 Testing

Crear un usuario de prueba:

```bash
aws dynamodb put-item \
  --table-name edo-sushi-bar-users-dev \
  --item '{
    "email": {"S": "chef@edosushi.com"},
    "password": {"S": "secret123"},
    "role": {"S": "STAFF"},
    "tenant_id": {"S": "sede-miraflores"}
  }'
```

## 🔧 Desarrollo Local

Para desarrollo local, usar serverless-offline:

```bash
npm install --save-dev serverless-offline
serverless offline start
```

## 📦 Estructura del Proyecto

```
edo-proyecto/
├── serverless.yml          # Configuración principal
├── package.json
├── src/
│   └── handlers/
│       ├── auth.js         # Autenticación
│       ├── orders.js       # Gestión de pedidos
│       └── notifications.js # Notificaciones
└── README.md
```

## 🌟 Características Principales

✅ Multi-tenant (múltiples sedes)  
✅ Autenticación custom sin Cognito  
✅ Step Functions con Callback Pattern  
✅ EventBridge para arquitectura EDA  
✅ DynamoDB con GSI optimizados  
✅ CORS habilitado  
✅ Roles (CLIENTE/STAFF)  

## 🚧 TODOs para Producción

- [ ] Implementar JWT real con PyJWT
- [ ] Hash de passwords con bcrypt o argon2
- [ ] Implementar Custom Authorizer en API Gateway
- [ ] Agregar validación de schemas (Joi/Yup)
- [ ] Implementar notificaciones reales (SNS/SES)
- [ ] Agregar CloudWatch Alarms
- [ ] Implementar DynamoDB Streams para auditoría
- [ ] Tests unitarios y de integración
- [ ] CI/CD pipeline

## 📄 Licencia

MIT