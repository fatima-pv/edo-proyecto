/**
 * Authentication Helper
 * Manejo de autenticación y localStorage
 */

const Auth = {
    /**
     * Guarda la información del usuario en localStorage
     */
    saveUser: (userData) => {
        localStorage.setItem('token', userData.token);
        localStorage.setItem('email', userData.email);
        localStorage.setItem('role', userData.role);
        localStorage.setItem('tenant_id', userData.tenant_id);
    },

    /**
     * Obtiene la información del usuario actual
     */
    getUser: () => {
        return {
            token: localStorage.getItem('token'),
            email: localStorage.getItem('email'),
            role: localStorage.getItem('role'),
            tenant_id: localStorage.getItem('tenant_id'),
        };
    },

    /**
     * Verifica si el usuario está autenticado
     */
    isAuthenticated: () => {
        return !!localStorage.getItem('token');
    },

    /**
     * Verifica si el usuario es STAFF
     */
    isStaff: () => {
        return localStorage.getItem('role') === 'STAFF';
    },

    /**
     * Verifica si el usuario es CLIENTE
     */
    isClient: () => {
        return localStorage.getItem('role') === 'CLIENTE';
    },

    /**
     * Cierra sesión
     */
    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('email');
        localStorage.removeItem('role');
        localStorage.removeItem('tenant_id');
        window.location.href = 'index.html';
    },

    /**
     * Redirige según el rol del usuario
     */
    redirectByRole: () => {
        if (Auth.isStaff()) {
            window.location.href = 'dashboard.html';
        } else if (Auth.isClient()) {
            window.location.href = 'menu.html';
        }
    },

    /**
     * Verifica que el usuario tenga acceso a la página actual
     */
    checkAccess: (requiredRole) => {
        if (!Auth.isAuthenticated()) {
            window.location.href = 'index.html';
            return false;
        }

        const currentRole = localStorage.getItem('role');
        if (requiredRole && currentRole !== requiredRole) {
            Auth.redirectByRole();
            return false;
        }

        return true;
    },
};

// Exportar para uso global
window.Auth = Auth;
