/**
 * Menu Logic - Vista Cliente
 * Gestiona el carrito y pedidos del cliente
 */

// Verificar acceso
Auth.checkAccess('CLIENTE');

// Estado del carrito
let cart = [];

// Menú de ejemplo (en producción, traerlo del backend)
const menuItems = [
    { id: 1, name: 'Maki Acevichado', description: 'Delicioso maki con pescado fresco', price: 18.00 },
    { id: 2, name: 'Ramen Tradicional', description: 'Ramen casero con caldo de huesos', price: 22.00 },
    { id: 3, name: 'Gyoza', description: 'Empanadillas japonesas fritas', price: 12.00 },
    { id: 4, name: 'Tempura Mix', description: 'Vegetales y camarones empanizados', price: 24.00 },
    { id: 5, name: 'Nigiri Salmón', description: '5 piezas de nigiri de salmón', price: 20.00 },
    { id: 6, name: 'California Roll', description: '8 piezas de california roll', price: 16.00 },
];

/**
 * Inicializar página
 */
function init() {
    // Mostrar email del usuario
    const user = Auth.getUser();
    document.getElementById('userEmail').textContent = user.email;

    // Renderizar menú
    renderMenu();

    // Cargar pedidos del cliente
    loadMyOrders();

    // Polling cada 5 segundos para actualizar pedidos
    setInterval(loadMyOrders, 5000);
}

/**
 * Renderizar items del menú
 */
function renderMenu() {
    const container = document.getElementById('menuItems');

    container.innerHTML = menuItems.map(item => `
        <div class="menu-item">
            <div class="menu-item-name">${item.name}</div>
            <div class="menu-item-description">${item.description}</div>
            <div class="menu-item-price">S/ ${item.price.toFixed(2)}</div>
            <div class="menu-item-actions">
                <button class="btn btn-primary btn-sm" onclick="addToCart(${item.id})">
                    Agregar al carrito
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Agregar item al carrito
 */
function addToCart(itemId) {
    const item = menuItems.find(i => i.id === itemId);
    const existingItem = cart.find(i => i.id === itemId);

    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({ ...item, quantity: 1 });
    }

    renderCart();
}

/**
 * Remover item del carrito
 */
function removeFromCart(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    renderCart();
}

/**
 * Actualizar cantidad de un item
 */
function updateQuantity(itemId, change) {
    const item = cart.find(i => i.id === itemId);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            removeFromCart(itemId);
        } else {
            renderCart();
        }
    }
}

/**
 * Renderizar carrito
 */
function renderCart() {
    const container = document.getElementById('cartItems');
    const footer = document.getElementById('cartFooter');
    const totalElement = document.getElementById('cartTotal');

    if (cart.length === 0) {
        container.innerHTML = `
            <p class="text-center" style="color: var(--text-secondary); padding: 2rem;">
                Tu carrito está vacío
            </p>
        `;
        footer.classList.add('hidden');
        return;
    }

    // Renderizar items
    container.innerHTML = cart.map(item => `
        <div class="cart-item">
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-quantity">
                    <button class="btn btn-sm" onclick="updateQuantity(${item.id}, -1)">-</button>
                    ${item.quantity}x S/ ${item.price.toFixed(2)}
                    <button class="btn btn-sm" onclick="updateQuantity(${item.id}, 1)">+</button>
                </div>
            </div>
            <div>
                <strong>S/ ${(item.price * item.quantity).toFixed(2)}</strong>
                <button class="btn btn-secondary btn-sm" onclick="removeFromCart(${item.id})" style="margin-left: 0.5rem;">
                    ✕
                </button>
            </div>
        </div>
    `).join('');

    // Calcular total
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    totalElement.textContent = `S/ ${total.toFixed(2)}`;
    footer.classList.remove('hidden');
}

/**
 * Realizar pedido
 */
async function placeOrder() {
    if (cart.length === 0) return;

    const alertContainer = document.getElementById('alert-container');
    const user = Auth.getUser();

    try {
        // Preparar datos del pedido
        const orderData = {
            tenant_id: user.tenant_id,
            items: cart.map(item => ({
                name: item.name,
                quantity: item.quantity,
                price: item.price
            })),
            total: cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
            customer_info: {
                name: user.email.split('@')[0],
                email: user.email,
            }
        };

        // Enviar pedido
        const response = await API.createOrder(orderData);

        // Mostrar éxito
        alertContainer.innerHTML = `
            <div class="alert alert-success">
                ✓ Pedido #${response.order_id.substring(0, 8)} creado exitosamente!
            </div>
        `;

        // Limpiar carrito
        cart = [];
        renderCart();

        // Recargar pedidos
        loadMyOrders();

        // Limpiar alerta después de 3 segundos
        setTimeout(() => {
            alertContainer.innerHTML = '';
        }, 3000);

    } catch (error) {
        alertContainer.innerHTML = `
            <div class="alert alert-error">
                ✗ Error al crear pedido: ${error.message}
            </div>
        `;
    }
}

/**
 * Cargar mis pedidos (con polling)
 */
async function loadMyOrders() {
    try {
        const response = await API.getOrders();
        const orders = response.orders || [];

        renderMyOrders(orders);
    } catch (error) {
        console.error('Error al cargar pedidos:', error);
    }
}

/**
 * Renderizar mis pedidos
 */
function renderMyOrders(orders) {
    const container = document.getElementById('myOrders');

    if (orders.length === 0) {
        container.innerHTML = `
            <p class="text-center" style="color: var(--text-secondary);">
                No tienes pedidos activos
            </p>
        `;
        return;
    }

    container.innerHTML = orders.map(order => `
        <div class="card" style="margin-bottom: 1rem; padding: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>Pedido #${order.order_id.substring(0, 8)}</strong>
                    <div style="color: var(--text-secondary); font-size: 0.9rem;">
                        ${new Date(order.created_at).toLocaleString('es-PE')}
                    </div>
                </div>
                <div>
                    ${getStatusBadge(order.status)}
                </div>
            </div>
            <div style="margin-top: 0.5rem;">
                <strong>Total:</strong> S/ ${order.total}
            </div>
        </div>
    `).join('');
}

/**
 * Obtener badge de estado
 */
function getStatusBadge(status) {
    const badges = {
        'RECEIVED': '<span class="badge badge-received">Recibido</span>',
        'WAITING_KITCHEN': '<span class="badge badge-waiting">En Espera - Cocina</span>',
        'COOKING': '<span class="badge badge-cooking">Cocinando</span>',
        'WAITING_PACKAGING': '<span class="badge badge-waiting">En Espera - Empaquetado</span>',
        'PACKAGED': '<span class="badge badge-packaged">Empaquetado</span>',
        'WAITING_DELIVERY': '<span class="badge badge-waiting">En Espera - Delivery</span>',
        'DELIVERED': '<span class="badge badge-delivered">Entregado</span>',
    };

    return badges[status] || `<span class="badge">${status}</span>`;
}

// Inicializar cuando carga la página
document.addEventListener('DOMContentLoaded', init);

// Exponer funciones globales
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateQuantity = updateQuantity;
window.placeOrder = placeOrder;
