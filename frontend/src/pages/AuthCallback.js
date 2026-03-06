import React, { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

const AuthCallback = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { processGoogleCallback } = useAuth();
    const hasProcessed = useRef(false);

    useEffect(() => {
        if (hasProcessed.current) return;
        hasProcessed.current = true;

        const processAuth = async () => {
            try {
                const hash = location.hash;
                const sessionIdMatch = hash.match(/session_id=([^&]+)/);
                
                if (sessionIdMatch) {
                    const sessionId = sessionIdMatch[1];
                    await processGoogleCallback(sessionId);
                    navigate('/dashboard', { replace: true });
                } else {
                    navigate('/login', { replace: true });
                }
            } catch (error) {
                console.error('Auth callback error:', error);
                navigate('/login', { replace: true });
            }
        };

        processAuth();
    }, [location, navigate, processGoogleCallback]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="text-center">
                <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
                <p className="text-muted-foreground">Processing authentication...</p>
            </div>
        </div>
    );
};

export default AuthCallback;
