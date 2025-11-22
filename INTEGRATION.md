# 🔗 Guía de Integración Frontend-Backend

## Paso 1: Deploy del Backend

```bash
cd /Users/mauricioalarcon/utec/cloud/edo-proyecto
sls deploy --stage dev
```

**Importante**: Guarda el URL del API Gateway que aparece en la salida:
```
ApiEndpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
```

## Paso 2: Crear Usuarios de Prueba

```bash
./scripts/seed-data.sh dev
```

Esto creará:
- `cliente@test.com` / `cliente123`
- `chef@edosushi.com` / `chef123`
- `empaquetador@edosushi.com` / `emp123`
- `delivery@edosushi.com` / `delivery123`

## Paso 3: Configurar Frontend

Edita `frontend/js/api.js` línea 7:

```javascript
const API_CONFIG = {
    BASE_URL: 'https://xxxxx.execute-api.us-east-1.amazonaws.com/dev',
    //              ↑ Pega aquí tu URL del API Gateway
};
```

## Paso 4: Probar el Frontend

### Opción A: Abrir directamente
```bash
open frontend/index.html
```

### Opción B: Servidor local (recomendado)
```bash
cd frontend
python3 -m http.server 8000
# Abre en: http://localhost:8000
```

## Paso 5: Flujo de Prueba Completo

### Como Cliente:
1. Login con `cliente@test.com` / `cliente123`
2. Agregar items al carrito
3. Realizar pedido
4. Ver estado en tiempo real

### Como Staff:
1. Login con `chef@edosushi.com` / `chef123`
2. Ver pedido en dashboard
3. Click en "🍳 Iniciar Cocina"
4. El pedido avanza automáticamente

### Continuar como Empaquetador:
1. Logout y login con `empaquetador@edosushi.com` / `emp123`
2. Ver pedido en estado "Esperando Empaquetado"
3. Click en "📦 Empaquetar"

### Finalizar como Motorizado:
1. Logout y login con `delivery@edosushi.com` / `delivery123`
2. Ver pedido en estado "Esperando Delivery"
3. Click en "🚗 Entregar"
4. ✅ Pedido completado!

## 🔍 Verificar en AWS Console

### Step Functions
1. Ve a AWS Console → Step Functions
2. Busca `EdoOrderWorkflow-dev`
3. Verás las ejecuciones en tiempo real

### DynamoDB
1. Ve a AWS Console → DynamoDB
2. Tabla `edo-sushi-bar-orders-dev`
3. Verás los pedidos con sus `task_token`

### CloudWatch Logs
```bash
sls logs -f createOrder --tail
sls logs -f updateOrderStep --tail
```

## 🐛 Troubleshooting

### Error: CORS
- Verifica que el backend tenga CORS habilitado (ya está configurado)

### Error: 401 Unauthorized
- Verifica que el token se esté enviando correctamente
- Revisa localStorage en DevTools

### Error: taskToken undefined
- El Step Function debe estar en estado `waitForTaskToken`
- Verifica en DynamoDB que el campo `task_token` existe

### Polling no funciona
- Abre DevTools → Console para ver errores
- Verifica que la URL del API esté correcta

## 📊 Endpoints del Backend

| Método | Endpoint | Rol | Descripción |
|--------|----------|-----|-------------|
| POST | `/auth/login` | Todos | Login |
| POST | `/orders` | CLIENTE | Crear pedido |
| GET | `/orders` | Ambos | Listar pedidos |
| POST | `/orders/advance` | STAFF | Avanzar workflow |

## ✅ Checklist de Integración

- [ ] Backend deployado
- [ ] Usuarios creados
- [ ] URL del API configurada en frontend
- [ ] Frontend accesible en navegador
- [ ] Login funciona
- [ ] Cliente puede crear pedidos
- [ ] Staff puede ver pedidos
- [ ] Botón "Avanzar Etapa" funciona
- [ ] Polling actualiza en tiempo real
- [ ] Flujo completo probado
