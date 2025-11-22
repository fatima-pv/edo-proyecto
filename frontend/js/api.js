/**
 * API Configuration and Service
 * Maneja todas las llamadas al backend serverless
 */

// ⚠️ IMPORTANTE: Actualiza esta URL después del deployment
const API_CONFIG = {
    BASE_URL: 'https://YOUR_API_GATEWAY_URL/dev',
    // Ejemplo: 'https://xxxxx.execute-api.us-east-1.amazonaws.com/dev'
};

/**
 * Realiza una petición HTTP al backend
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;

    const defaultHeaders = {
        'Content-Type': 'application/json',
    };

    // Agregar token si existe
    const token = localStorage.getItem('token');
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || data.error || 'Error en la petición');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * API Service - Métodos para cada endpoint
 */
const API = {
    /**
     * Login de usuario
     */
    login: async (email, password) => {
        return await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    },

    /**
     * Crear un nuevo pedido (Solo CLIENTE)
     */
    createOrder: async (orderData) => {
        return await apiRequest('/orders', {
            method: 'POST',
            body: JSON.stringify(orderData),
        });
    },

    /**
     * Obtener pedidos
     * CLIENTE: Sus propios pedidos
     * STAFF: Todos los pedidos del tenant
     */
    getOrders: async () => {
        return await apiRequest('/orders', {
            method: 'GET',
        });
    },

    /**
     * Avanzar pedido al siguiente paso (Solo STAFF)
     */
    advanceOrder: async (orderData) => {
        return await apiRequest('/orders/advance', {
            method: 'POST',
            body: JSON.stringify(orderData),
        });
    },
};

// Exportar para uso global
window.API = API;
window.API_CONFIG = API_CONFIG;
