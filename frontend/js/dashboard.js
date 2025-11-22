/**
 * Dashboard Logic - Vista Staff
 * Gestiona el dashboard de pedidos para el personal
 */

// Verificar acceso
Auth.checkAccess('STAFF');

/**
 * Inicializar página
 */
function init() {
    const user = Auth.getUser();
    document.getElementById('userEmail').textContent = user.email;
    loadOrders();
    setInterval(loadOrders, 5000);
}

/**
 * Cargar pedidos desde el backend
 */
async function loadOrders() {
    try {
        const response = await API.getOrders();
        const orders = response.orders || [];
        renderOrders(orders);
        updateStatistics(orders);
        updateLastUpdate();
    } catch (error) {
        console.error('Error al cargar pedidos:', error);
        showError('Error al cargar pedidos: ' + error.message);
    }
}

/**
 * Renderizar tabla de pedidos
 */
function renderOrders(orders) {
    const tbody = document.getElementById('ordersTableBody');

    if (orders.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center" style="padding: 3rem; color: var(--text-secondary);">
                    No hay pedidos activos
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = orders.map(order => `
        <tr>
            <td><strong>#${order.order_id.substring(0, 8)}</strong></td>
            <td>${order.customer_email || 'N/A'}</td>
            <td>${new Date(order.created_at).toLocaleString('es-PE')}</td>
            <td><strong>S/ ${order.total}</strong></td>
            <td>${getStatusBadge(order.status)}</td>
            <td>${getActionButton(order)}</td>
        </tr>
    `).join('');
}

/**
 * Obtener badge de estado
 */
function getStatusBadge(status) {
    const badges = {
        'RECEIVED': '<span class="badge badge-received">Recibido</span>',
        'WAITING_KITCHEN': '<span class="badge badge-waiting">⏳ Esperando Cocina</span>',
        'COOKING': '<span class="badge badge-cooking">👨‍🍳 Cocinando</span>',
        'WAITING_PACKAGING': '<span class="badge badge-waiting">⏳ Esperando Empaquetado</span>',
        'PACKAGED': '<span class="badge badge-packaged">📦 Empaquetado</span>',
        'WAITING_DELIVERY': '<span class="badge badge-waiting">⏳ Esperando Delivery</span>',
        'DELIVERED': '<span class="badge badge-delivered">✓ Entregado</span>',
    };
    return badges[status] || `<span class="badge">${status}</span>`;
}

/**
 * Obtener botón de acción según el estado
 */
function getActionButton(order) {
    if (order.status === 'DELIVERED') {
        return '<span style="color: var(--success-color);">✓ Completado</span>';
    }

    const actionStates = {
        'WAITING_KITCHEN': { next: 'COOKING', label: '🍳 Iniciar Cocina' },
        'WAITING_PACKAGING': { next: 'PACKAGED', label: '📦 Empaquetar' },
        'WAITING_DELIVERY': { next: 'DELIVERED', label: '🚗 Entregar' },
    };

    const action = actionStates[order.status];

    if (action && order.task_token) {
        return `
            <button 
                class="btn btn-success btn-sm" 
                onclick="advanceOrder('${order.order_id}', '${order.tenant_id}', '${order.task_token}', '${action.next}')"
            >
                ${action.label}
            </button>
        `;
    }

    return '<span style="color: var(--info-color);">⏳ En proceso...</span>';
}

/**
 * Avanzar pedido al siguiente paso
 */
async function advanceOrder(orderId, tenantId, taskToken, nextStep) {
    try {
        await API.advanceOrder({
            order_id: orderId,
            tenant_id: tenantId,
            task_token: taskToken,
            step: nextStep,
            notes: `Avanzado por ${Auth.getUser().email}`
        });
        showSuccess(`Pedido #${orderId.substring(0, 8)} avanzado exitosamente`);
        loadOrders();
    } catch (error) {
        showError(`Error al avanzar pedido: ${error.message}`);
    }
}

/**
 * Actualizar estadísticas
 */
function updateStatistics(orders) {
    const total = orders.length;
    const completed = orders.filter(o => o.status === 'DELIVERED').length;
    const pending = total - completed;

    document.getElementById('statTotal').textContent = total;
    document.getElementById('statPending').textContent = pending;
    document.getElementById('statCompleted').textContent = completed;
}

/**
 * Actualizar timestamp de última actualización
 */
function updateLastUpdate() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent =
        `Última actualización: ${now.toLocaleTimeString('es-PE')}`;
}

/**
 * Mostrar mensaje de éxito
 */
function showSuccess(message) {
    const alertContainer = document.getElementById('alert-container');
    alertContainer.innerHTML = `<div class="alert alert-success">✓ ${message}</div>`;
    setTimeout(() => alertContainer.innerHTML = '', 3000);
}

/**
 * Mostrar mensaje de error
 */
function showError(message) {
    const alertContainer = document.getElementById('alert-container');
    alertContainer.innerHTML = `<div class="alert alert-error">✗ ${message}</div>`;
    setTimeout(() => alertContainer.innerHTML = '', 5000);
}

document.addEventListener('DOMContentLoaded', init);
window.loadOrders = loadOrders;
window.advanceOrder = advanceOrder;
