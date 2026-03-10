import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    // Initialize state from localStorage synchronously
    const [user, setUser] = useState(() => {
        try {
            const savedUser = localStorage.getItem('zektrix_user');
            return savedUser ? JSON.parse(savedUser) : null;
        } catch {
            return null;
        }
    });
    const [token, setToken] = useState(() => localStorage.getItem('zektrix_token'));
    const [loading, setLoading] = useState(true);
    const authCheckDone = useRef(false);
    const retryCount = useRef(0);

    const saveAuth = useCallback((newToken, userData) => {
        try {
            if (newToken) {
                localStorage.setItem('zektrix_token', newToken);
                setToken(newToken);
            }
            if (userData) {
                localStorage.setItem('zektrix_user', JSON.stringify(userData));
                setUser(userData);
            }
        } catch (e) {
            console.warn('Failed to save auth to localStorage:', e);
        }
    }, []);

    const clearAuth = useCallback(() => {
        try {
            localStorage.removeItem('zektrix_token');
            localStorage.removeItem('zektrix_user');
            // Also clear old keys for migration
            localStorage.removeItem('token');
            localStorage.removeItem('user');
        } catch (e) {
            console.warn('Failed to clear localStorage:', e);
        }
        setToken(null);
        setUser(null);
    }, []);

    const checkAuth = useCallback(async () => {
        // Prevent multiple checks
        if (authCheckDone.current) return;
        
        // Skip if OAuth callback in progress
        const searchParams = new URLSearchParams(window.location.search);
        const hashParams = new URLSearchParams(window.location.hash?.replace('#', ''));
        
        if (searchParams.has('session_id') || hashParams.has('session_id')) {
            setLoading(false);
            return;
        }

        // Try to get token from new key first, then fall back to old key
        let storedToken = localStorage.getItem('zektrix_token');
        let storedUser = localStorage.getItem('zektrix_user');
        
        // Migration from old keys
        if (!storedToken) {
            storedToken = localStorage.getItem('token');
            storedUser = localStorage.getItem('user');
            if (storedToken) {
                // Migrate to new keys
                localStorage.setItem('zektrix_token', storedToken);
                if (storedUser) localStorage.setItem('zektrix_user', storedUser);
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        }
        
        if (!storedToken) {
            authCheckDone.current = true;
            setLoading(false);
            return;
        }

        // Set token immediately
        setToken(storedToken);
        
        // Use cached user data immediately for faster UX
        if (storedUser) {
            try {
                const parsedUser = JSON.parse(storedUser);
                setUser(parsedUser);
            } catch (e) {
                console.warn('Failed to parse stored user');
            }
        }

        // Verify with server
        try {
            const response = await axios.get(`${API}/auth/me`, {
                headers: { Authorization: `Bearer ${storedToken}` },
                timeout: 10000 // 10 second timeout
            });
            
            // Update with fresh data
            saveAuth(storedToken, response.data);
            retryCount.current = 0;
            
        } catch (error) {
            console.warn('Auth check failed:', error?.response?.status || error.message);
            
            if (error.response?.status === 401) {
                // Token is definitely invalid - clear only after 401
                clearAuth();
            } else if (error.response?.status === 403) {
                // User might be blocked
                clearAuth();
            } else {
                // Network error, timeout, or server error - KEEP using cached data
                // Don't clear auth for temporary network issues
                console.log('Network issue, keeping cached auth data');
                
                // Retry once after 3 seconds for network errors
                if (retryCount.current < 1) {
                    retryCount.current++;
                    setTimeout(() => {
                        authCheckDone.current = false;
                        checkAuth();
                    }, 3000);
                }
            }
        } finally {
            authCheckDone.current = true;
            setLoading(false);
        }
    }, [saveAuth, clearAuth]);

    useEffect(() => {
        checkAuth();
        
        // Re-check auth on window focus (user comes back to tab)
        const handleFocus = () => {
            if (token) {
                authCheckDone.current = false;
                checkAuth();
            }
        };
        
        window.addEventListener('focus', handleFocus);
        return () => window.removeEventListener('focus', handleFocus);
    }, [checkAuth, token]);

    // Handle storage changes from other tabs
    useEffect(() => {
        const handleStorageChange = (e) => {
            if (e.key === 'zektrix_token') {
                if (e.newValue) {
                    setToken(e.newValue);
                } else {
                    setToken(null);
                    setUser(null);
                }
            }
            if (e.key === 'zektrix_user' && e.newValue) {
                try {
                    setUser(JSON.parse(e.newValue));
                } catch {}
            }
        };
        
        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, []);

    // Handle token expiration from axios interceptor
    useEffect(() => {
        const handleAuthExpired = () => {
            console.log('Auth expired event received');
            clearAuth();
        };
        
        window.addEventListener('auth:expired', handleAuthExpired);
        return () => window.removeEventListener('auth:expired', handleAuthExpired);
    }, [clearAuth]);

    const login = async (email, password) => {
        const response = await axios.post(`${API}/auth/login`, { email, password });
        const { token: newToken, user: userData } = response.data;
        saveAuth(newToken, userData);
        return userData;
    };

    const register = async (username, email, password, firstName, lastName, phone) => {
        const response = await axios.post(`${API}/auth/register`, { 
            username, 
            email, 
            password,
            first_name: firstName,
            last_name: lastName,
            phone: phone
        });
        const { token: newToken, user: userData } = response.data;
        saveAuth(newToken, userData);
        return userData;
    };

    const loginWithGoogle = async (sessionId) => {
        const response = await axios.get(`${API}/auth/session?session_id=${sessionId}`);
        const { token: newToken, user: userData } = response.data;
        saveAuth(newToken, userData);
        return userData;
    };

    const logout = () => {
        clearAuth();
    };

    const refreshUser = async () => {
        if (!token) return;
        try {
            const response = await axios.get(`${API}/auth/me`, {
                headers: { Authorization: `Bearer ${token}` },
                timeout: 10000
            });
            saveAuth(token, response.data);
        } catch (error) {
            console.error('Failed to refresh user:', error?.message);
        }
    };

    const isAdmin = user?.role === 'admin';
    const isAuthenticated = !!token && !!user;

    return (
        <AuthContext.Provider value={{
            user,
            token,
            loading,
            isAdmin,
            isAuthenticated,
            login,
            register,
            loginWithGoogle,
            logout,
            refreshUser
        }}>
            {children}
        </AuthContext.Provider>
    );
};
