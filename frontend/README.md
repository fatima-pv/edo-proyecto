# 🍣 Edo Sushi Bar - Frontend

Frontend HTML/CSS/JavaScript para el sistema de gestión de pedidos.

## 📁 Estructura

```
frontend/
├── index.html          # Login
├── menu.html           # Vista Cliente
├── dashboard.html      # Vista Staff
├── css/
│   └── styles.css      # Estilos globales
└── js/
    ├── api.js          # Servicio API
    ├── auth.js         # Autenticación
    ├── menu.js         # Lógica cliente
    └── dashboard.js    # Lógica staff
```

## 🚀 Configuración

### 1. Actualizar URL del Backend

Edita `js/api.js` y actualiza la URL:

```javascript
const API_CONFIG = {
    BASE_URL: 'https://TU_API_GATEWAY_URL/dev',
};
```

### 2. Abrir en el navegador

Simplemente abre `index.html` en tu navegador o usa un servidor local:

```bash
# Con Python
python3 -m http.server 8000

# Con Node.js
npx serve .
```

## 👥 Usuarios de Prueba

- **Cliente**: cliente@test.com / cliente123
- **Chef**: chef@edosushi.com / chef123
- **Empaquetador**: empaquetador@edosushi.com / emp123
- **Motorizado**: delivery@edosushi.com / delivery123

## ✨ Características

### Vista Cliente (menu.html)
- ✅ Catálogo de productos
- ✅ Carrito de compras
- ✅ Crear pedidos
- ✅ Ver estado de pedidos en tiempo real (polling 5s)

### Vista Staff (dashboard.html)
- ✅ Tabla de pedidos activos
- ✅ Botón "Avanzar Etapa" con taskToken
- ✅ Actualización automática (polling 5s)
- ✅ Estadísticas en tiempo real

## 🔄 Flujo de Trabajo

1. **Cliente** realiza pedido → Estado: `RECEIVED`
2. **Chef** acepta → Estado: `COOKING`
3. **Empaquetador** empaqueta → Estado: `PACKAGED`
4. **Motorizado** entrega → Estado: `DELIVERED`

Cada cambio usa el **Callback Pattern** con `taskToken`.
