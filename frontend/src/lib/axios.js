import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Create axios instance with default config
const api = axios.create({
    baseURL: `${BACKEND_URL}/api`,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('zektrix_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - handle token expiration
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Handle token expiration globally
        if (error.response?.status === 401) {
            const errorMessage = error.response?.data?.detail || '';
            
            // Check if it's a token expiration error
            if (errorMessage.includes('expired') || errorMessage.includes('Token') || errorMessage.includes('Session')) {
                console.log('Token expired, clearing auth...');
                
                // Clear stored auth data
                localStorage.removeItem('zektrix_token');
                localStorage.removeItem('zektrix_user');
                
                // Dispatch custom event for auth context to listen to
                window.dispatchEvent(new CustomEvent('auth:expired'));
                
                // Optionally redirect to login
                // Only redirect if not already on login page
                if (!window.location.pathname.includes('/login')) {
                    // Save current location for redirect back
                    sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
                    window.location.href = '/login';
                }
            }
        }
        
        return Promise.reject(error);
    }
);

export default api;
