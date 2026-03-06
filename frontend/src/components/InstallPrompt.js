import React, { useState, useEffect } from 'react';
import { X, Download, Smartphone } from 'lucide-react';
import { Button } from './ui/button';

const InstallPrompt = () => {
    const [showPrompt, setShowPrompt] = useState(false);
    const [deferredPrompt, setDeferredPrompt] = useState(null);
    const [isIOS, setIsIOS] = useState(false);

    useEffect(() => {
        // Check if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            return;
        }

        // Check if dismissed recently
        const dismissed = localStorage.getItem('installPromptDismissed');
        if (dismissed) {
            const dismissedDate = new Date(dismissed);
            const daysSinceDismissed = (new Date() - dismissedDate) / (1000 * 60 * 60 * 24);
            if (daysSinceDismissed < 7) return;
        }

        // Check for iOS
        const isIOSDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
        setIsIOS(isIOSDevice);

        // Listen for beforeinstallprompt event (Chrome, Edge, etc.)
        const handleBeforeInstall = (e) => {
            e.preventDefault();
            setDeferredPrompt(e);
            setTimeout(() => setShowPrompt(true), 3000);
        };

        window.addEventListener('beforeinstallprompt', handleBeforeInstall);

        // For iOS, show prompt after delay
        if (isIOSDevice) {
            setTimeout(() => setShowPrompt(true), 3000);
        }

        return () => {
            window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
        };
    }, []);

    const handleInstall = async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') {
                setShowPrompt(false);
            }
            setDeferredPrompt(null);
        }
    };

    const handleDismiss = () => {
        setShowPrompt(false);
        localStorage.setItem('installPromptDismissed', new Date().toISOString());
    };

    if (!showPrompt) return null;

    return (
        <div className="fixed bottom-20 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 animate-slide-up">
            <div className="glass-strong rounded-2xl p-5 border border-primary/30 shadow-2xl">
                <button 
                    onClick={handleDismiss}
                    className="absolute top-3 right-3 text-white/50 hover:text-white transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>
                
                <div className="flex items-start gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0">
                        <Smartphone className="w-7 h-7 text-white" />
                    </div>
                    
                    <div className="flex-1 pr-6">
                        <h3 className="font-bold text-lg mb-1">Instalează Zektrix</h3>
                        <p className="text-sm text-muted-foreground mb-3">
                            {isIOS 
                                ? 'Apasă pe butonul Share și apoi "Add to Home Screen"'
                                : 'Adaugă aplicația pe ecranul principal pentru acces rapid!'}
                        </p>
                        
                        {!isIOS && (
                            <Button 
                                onClick={handleInstall}
                                className="btn-primary text-sm py-2 px-4"
                            >
                                <Download className="w-4 h-4 mr-2" />
                                Instalează Acum
                            </Button>
                        )}
                        
                        {isIOS && (
                            <div className="flex items-center gap-2 text-xs text-primary">
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M16 5l-1.42 1.42-1.59-1.59V16h-2V4.83l-1.59 1.59L8 5l4-4 4 4zm4 5v11c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2V10c0-1.1.9-2 2-2h3v2H6v11h12V10h-3V8h3c1.1 0 2 .9 2 2z"/>
                                </svg>
                                <span>Apasă Share → Add to Home Screen</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InstallPrompt;
