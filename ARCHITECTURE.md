# 🍣 Edo Sushi Bar - Arquitectura del Sistema

## Diagrama de Arquitectura

```mermaid
graph TB
    subgraph "Cliente"
        A[App Móvil/Web]
    end
    
    subgraph "AWS API Gateway"
        B[POST /auth/login]
        C[POST /orders]
        D[GET /orders]
        E[POST /orders/advance]
    end
    
    subgraph "Lambda Functions"
        F[authLogin]
        G[createOrder]
        H[getOrders]
        I[updateOrderStep]
        J[notifyStaff]
    end
    
    subgraph "DynamoDB"
        K[(EdoUsersTable)]
        L[(EdoOrdersTable)]
    end
    
    subgraph "Step Functions"
        M[EdoOrderWorkflow]
        M1[ReceiveOrder]
        M2[WaitCocinero 🍳]
        M3[WaitEmpaquetado 📦]
        M4[WaitDelivery 🛵]
        M5[Success ✅]
        
        M1 --> M2
        M2 --> M3
        M3 --> M4
        M4 --> M5
    end
    
    subgraph "EventBridge"
        N[EdoOrderBus]
    end
    
    A -->|Login| B
    A -->|Crear Pedido| C
    A -->|Ver Pedidos| D
    A -->|Avanzar Pedido| E
    
    B --> F
    C --> G
    D --> H
    E --> I
    
    F --> K
    G --> L
    G -->|StartExecution| M
    H --> L
    I --> L
    I -->|SendTaskSuccess| M
    
    M -->|PutEvents| N
    N -->|Trigger| J
    J --> L
    
    style M2 fill:#f9a825
    style M3 fill:#f9a825
    style M4 fill:#f9a825
```

## Flujo de Trabajo Detallado

```mermaid
sequenceDiagram
    participant C as Cliente
    participant API as API Gateway
    participant CO as createOrder λ
    participant DB as DynamoDB
    participant SF as Step Function
    participant EB as EventBridge
    participant NS as notifyStaff λ
    participant Staff as Staff (Chef)
    participant UO as updateOrderStep λ
    
    C->>API: POST /orders
    API->>CO: Invoke
    CO->>DB: PutItem (order)
    CO->>SF: StartExecution
    SF->>EB: OrderStatusChanged (RECEIVED)
    SF->>NS: WaitCocinero (taskToken)
    NS->>DB: SaveTaskToken
    Note over SF: ⏸️ PAUSED (esperando callback)
    
    Staff->>API: POST /orders/advance
    API->>UO: Invoke (con taskToken)
    UO->>DB: UpdateOrder (COOKING)
    UO->>SF: SendTaskSuccess ✅
    Note over SF: ▶️ RESUMED
    SF->>EB: OrderStatusChanged (COOKING)
    SF->>NS: WaitEmpaquetado (taskToken)
    Note over SF: ⏸️ PAUSED
```

## Callback Pattern - Explicación Visual

```mermaid
stateDiagram-v2
    [*] --> ReceiveOrder
    ReceiveOrder --> WaitCocinero: Emit RECEIVED
    
    state WaitCocinero {
        [*] --> GenerateToken: .waitForTaskToken
        GenerateToken --> SaveToken: taskToken = "ABC123"
        SaveToken --> Pause: Guardar en DynamoDB
        Pause --> [*]: ⏸️ ESPERANDO
    }
    
    WaitCocinero --> EmitCooking: Chef llama /orders/advance<br/>con taskToken
    EmitCooking --> WaitEmpaquetado: Emit COOKING
    
    state WaitEmpaquetado {
        [*] --> GenerateToken2: .waitForTaskToken
        GenerateToken2 --> SaveToken2: taskToken = "XYZ789"
        SaveToken2 --> Pause2: Guardar en DynamoDB
        Pause2 --> [*]: ⏸️ ESPERANDO
    }
    
    WaitEmpaquetado --> EmitPackaged: Empaquetador avanza
    EmitPackaged --> WaitDelivery: Emit PACKAGED
    
    WaitDelivery --> EmitDelivered: Motorizado avanza
    EmitDelivered --> Success: Emit DELIVERED
    Success --> [*]
```

## Modelo de Datos Multi-Tenant

```mermaid
erDiagram
    EdoUsersTable ||--o{ EdoOrdersTable : "pertenece a tenant"
    
    EdoUsersTable {
        string email PK
        string password
        string role
        string tenant_id
        string staff_type
    }
    
    EdoOrdersTable {
        string tenant_id PK
        string order_id SK
        string customer_email
        array items
        number total
        string status
        string task_token
        number created_at
        number updated_at
    }
```

## Estados del Pedido

```mermaid
graph LR
    A[RECEIVED] -->|Chef acepta| B[COOKING]
    B -->|Listo para empaquetar| C[PACKAGED]
    C -->|Motorizado toma pedido| D[DELIVERING]
    D -->|Entregado| E[DELIVERED]
    
    style A fill:#2196f3
    style B fill:#ff9800
    style C fill:#9c27b0
    style D fill:#00bcd4
    style E fill:#4caf50
```

## Eventos de EventBridge

Todos los cambios de estado emiten eventos al `EdoOrderBus`:

```json
{
  "source": "edo.orders",
  "detail-type": "OrderStatusChanged",
  "detail": {
    "order_id": "abc-123",
    "tenant_id": "sede-miraflores",
    "status": "COOKING",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Roles y Permisos

| Rol | Permisos |
|-----|----------|
| **CLIENTE** | • Crear pedidos<br>• Ver sus propios pedidos |
| **STAFF** | • Ver todos los pedidos del tenant<br>• Avanzar pedidos (con taskToken)<br>• Recibir notificaciones |

## Escalabilidad Multi-Tenant

Cada sede (tenant) tiene:
- ✅ Aislamiento de datos por `tenant_id`
- ✅ Staff dedicado por sede
- ✅ Flujos de trabajo independientes
- ✅ Métricas separadas en CloudWatch

### Ejemplo de Tenants

```
sede-miraflores
├── Chef: chef@miraflores.com
├── Empaquetador: emp@miraflores.com
└── Motorizado: delivery@miraflores.com

sede-surco
├── Chef: chef@surco.com
├── Empaquetador: emp@surco.com
└── Motorizado: delivery@surco.com
```

## Costos Estimados (DEV)

Con uso bajo a moderado:

| Servicio | Costo Mensual |
|----------|---------------|
| Lambda | ~$0.20 |
| DynamoDB On-Demand | ~$2.50 |
| Step Functions | ~$0.25 |
| API Gateway | ~$1.00 |
| EventBridge | ~$0.10 |
| **TOTAL** | **~$4.05/mes** |

> 💡 En producción con mayor tráfico, los costos escalan según uso real.

## Ventajas de esta Arquitectura

✅ **Serverless**: Escalado automático, pago por uso  
✅ **Event-Driven**: Desacoplamiento mediante EventBridge  
✅ **Resiliente**: Reintentos automáticos en Step Functions  
✅ **Auditable**: Historial completo de eventos  
✅ **Multi-Tenant**: Aislamiento por sede  
✅ **Sin Cognito**: Autenticación custom con DynamoDB  

## Próximas Mejoras

1. **WebSockets** para actualizaciones en tiempo real
2. **S3** para almacenar imágenes de platos
3. **CloudFront** para CDN
4. **SNS** para notificaciones push
5. **SES** para emails transaccionales
6. **X-Ray** para tracing distribuido
