# Edo Sushi Bar — Sistema de Pedidos Serverless

Plataforma de gestión de pedidos para un restaurante de sushi con flujo **end‑to‑end** desde creación hasta entrega. El backend está construido 100% en AWS con un workflow orquestado por Step Functions y un API REST en API Gateway.

**API (dev):** https://mznmj4n3r1.execute-api.us-east-1.amazonaws.com/dev

---

## ✨ Características principales

- **Autenticación de usuarios** (cliente y roles de staff).
- **Creación y listado de pedidos** vía REST.
- **Workflow de cocina → empaquetado → delivery** con avance de estados.
- **Notificaciones al staff** mediante Lambda.
- **Arquitectura serverless** con baja operación y escalabilidad automática.

---

## 🧱 Arquitectura

- **API Gateway** expone endpoints REST.
- **AWS Lambda** implementa lógica de negocio:
	- `authLogin`
	- `createOrder`
	- `getOrders`
	- `updateOrderStep`
	- `notifyStaff`
- **AWS Step Functions** orquesta el workflow de pedidos.
- **DynamoDB** almacena usuarios y pedidos.
- **Frontend estático** para cliente y staff (dashboard/estado).

---

## 🔌 Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/login` | Autenticación |
| POST | `/orders` | Crear pedido (cliente) |
| GET | `/orders` | Listar pedidos |
| POST | `/orders/advance` | Avanzar workflow (staff) |

---

## 🧪 Pruebas rápidas (flujo funcional)

**Cliente**
1. Iniciar sesión.
2. Crear pedido.
3. Ver cambios de estado en tiempo real.

**Staff**
1. Chef: iniciar cocina.
2. Empaquetador: empaquetar.
3. Delivery: marcar entrega.

---

## ✅ Verificación en AWS

- **Step Functions:** `EdoOrderWorkflow-dev`
- **DynamoDB:**
	- `edo-sushi-bar-users-dev`
	- `edo-sushi-bar-orders-dev`

---

## 🛠️ Stack técnico

- **AWS Lambda**
- **API Gateway**
- **Step Functions**
- **DynamoDB**
- **Serverless Framework**
- **Frontend estático** (HTML/CSS/JS)

---

## 🎯 Logros destacables (para CV)

- Diseñé un **workflow de pedidos** con estados claros y roles de staff diferenciados.
- Implementé un **backend serverless** con **API REST** y funciones Lambda desacopladas.
- Orquesté el flujo con **Step Functions** para asegurar trazabilidad de cada pedido.
- Modelé datos en **DynamoDB** para usuarios y órdenes, optimizando lecturas y escrituras.

---

## 📄 Documentación adicional

- Deploy y validación: [DEPLOY_SUCCESS.md](DEPLOY_SUCCESS.md)
- Solución de login: [TROUBLESHOOTING_LOGIN.md](TROUBLESHOOTING_LOGIN.md)

---


