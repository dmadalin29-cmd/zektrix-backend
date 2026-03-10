import React, { useState, useEffect } from 'react';
import { Cookie, X, Settings, Check } from 'lucide-react';
import { Button } from './ui/button';

const CookieConsent = () => {
    const [showBanner, setShowBanner] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [preferences, setPreferences] = useState({
        necessary: true,
        analytics: false,
        marketing: false
    });

    useEffect(() => {
        const consent = localStorage.getItem('cookieConsent');
        if (!consent) {
            setTimeout(() => setShowBanner(true), 1500);
        }
    }, []);

    const handleAcceptAll = () => {
        const allAccepted = { necessary: true, analytics: true, marketing: true };
        localStorage.setItem('cookieConsent', JSON.stringify(allAccepted));
        localStorage.setItem('cookieConsentDate', new Date().toISOString());
        setShowBanner(false);
    };

    const handleAcceptSelected = () => {
        localStorage.setItem('cookieConsent', JSON.stringify(preferences));
        localStorage.setItem('cookieConsentDate', new Date().toISOString());
        setShowBanner(false);
        setShowSettings(false);
    };

    const handleRejectAll = () => {
        const onlyNecessary = { necessary: true, analytics: false, marketing: false };
        localStorage.setItem('cookieConsent', JSON.stringify(onlyNecessary));
        localStorage.setItem('cookieConsentDate', new Date().toISOString());
        setShowBanner(false);
    };

    if (!showBanner) return null;

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 p-4">
            <div className="max-w-4xl mx-auto">
                {!showSettings ? (
                    // Main Banner
                    <div className="glass-strong rounded-2xl p-6 border border-white/10 shadow-2xl">
                        <div className="flex items-start gap-4">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center flex-shrink-0">
                                <Cookie className="w-6 h-6 text-primary" />
                            </div>
                            
                            <div className="flex-1">
                                <h3 className="font-bold text-lg mb-2">🍪 Folosim cookie-uri</h3>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Utilizăm cookie-uri pentru a îmbunătăți experiența ta pe site. 
                                    Cookie-urile necesare asigură funcționarea corectă a site-ului, 
                                    în timp ce cele opționale ne ajută să înțelegem cum folosești platforma.
                                </p>
                                
                                <div className="flex flex-wrap gap-3">
                                    <Button 
                                        onClick={handleAcceptAll}
                                        className="btn-primary text-sm py-2"
                                    >
                                        <Check className="w-4 h-4 mr-2" />
                                        Acceptă Toate
                                    </Button>
                                    <Button 
                                        onClick={() => setShowSettings(true)}
                                        variant="outline"
                                        className="btn-outline text-sm py-2"
                                    >
                                        <Settings className="w-4 h-4 mr-2" />
                                        Setări
                                    </Button>
                                    <Button 
                                        onClick={handleRejectAll}
                                        variant="ghost"
                                        className="text-sm text-muted-foreground hover:text-white"
                                    >
                                        Doar Necesare
                                    </Button>
                                </div>
                            </div>
                            
                            <button 
                                onClick={handleRejectAll}
                                className="text-white/50 hover:text-white transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                ) : (
                    // Settings Panel
                    <div className="glass-strong rounded-2xl p-6 border border-white/10 shadow-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-bold text-xl">Setări Cookie-uri</h3>
                            <button 
                                onClick={() => setShowSettings(false)}
                                className="text-white/50 hover:text-white transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        
                        <div className="space-y-4 mb-6">
                            {/* Necessary */}
                            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
                                <div>
                                    <h4 className="font-semibold">Cookie-uri Necesare</h4>
                                    <p className="text-sm text-muted-foreground">
                                        Esențiale pentru funcționarea site-ului
                                    </p>
                                </div>
                                <div className="w-12 h-6 rounded-full bg-green-500/20 flex items-center justify-end px-1">
                                    <div className="w-4 h-4 rounded-full bg-green-500" />
                                </div>
                            </div>
                            
                            {/* Analytics */}
                            <div 
                                className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors"
                                onClick={() => setPreferences(p => ({ ...p, analytics: !p.analytics }))}
                            >
                                <div>
                                    <h4 className="font-semibold">Cookie-uri Analitice</h4>
                                    <p className="text-sm text-muted-foreground">
                                        Ne ajută să înțelegem cum folosești site-ul
                                    </p>
                                </div>
                                <div className={`w-12 h-6 rounded-full flex items-center px-1 transition-colors ${
                                    preferences.analytics ? 'bg-primary/20 justify-end' : 'bg-white/10 justify-start'
                                }`}>
                                    <div className={`w-4 h-4 rounded-full transition-colors ${
                                        preferences.analytics ? 'bg-primary' : 'bg-white/30'
                                    }`} />
                                </div>
                            </div>
                            
                            {/* Marketing */}
                            <div 
                                className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition-colors"
                                onClick={() => setPreferences(p => ({ ...p, marketing: !p.marketing }))}
                            >
                                <div>
                                    <h4 className="font-semibold">Cookie-uri Marketing</h4>
                                    <p className="text-sm text-muted-foreground">
                                        Pentru reclame personalizate
                                    </p>
                                </div>
                                <div className={`w-12 h-6 rounded-full flex items-center px-1 transition-colors ${
                                    preferences.marketing ? 'bg-primary/20 justify-end' : 'bg-white/10 justify-start'
                                }`}>
                                    <div className={`w-4 h-4 rounded-full transition-colors ${
                                        preferences.marketing ? 'bg-primary' : 'bg-white/30'
                                    }`} />
                                </div>
                            </div>
                        </div>
                        
                        <div className="flex gap-3">
                            <Button 
                                onClick={handleAcceptSelected}
                                className="btn-primary flex-1"
                            >
                                Salvează Preferințele
                            </Button>
                            <Button 
                                onClick={handleAcceptAll}
                                variant="outline"
                                className="btn-outline"
                            >
                                Acceptă Toate
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CookieConsent;
