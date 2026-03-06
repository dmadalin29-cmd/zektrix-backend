import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Bell, BellOff, BellRing, Check, X, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const NotificationBell = () => {
    const { user, token } = useAuth();
    const { isRomanian } = useLanguage();
    const [isSubscribed, setIsSubscribed] = useState(false);
    const [showDialog, setShowDialog] = useState(false);
    const [loading, setLoading] = useState(false);
    const [notifications, setNotifications] = useState([]);

    useEffect(() => {
        if (user && token) {
            checkSubscriptionStatus();
            setupWebSocketNotifications();
        }
    }, [user, token]);

    const checkSubscriptionStatus = async () => {
        try {
            const response = await axios.get(`${API}/api/notifications/status`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setIsSubscribed(response.data.subscribed);
        } catch (error) {
            console.error('Failed to check notification status');
        }
    };

    const setupWebSocketNotifications = () => {
        // Connect to WebSocket for real-time notifications
        const wsUrl = API.replace('https://', 'wss://').replace('http://', 'ws://');
        const ws = new WebSocket(`${wsUrl}/ws`);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'competition_alert') {
                    // Show browser notification if permitted
                    showBrowserNotification(data);
                    // Add to in-app notifications
                    setNotifications(prev => [{
                        id: Date.now(),
                        title: data.title,
                        message: data.message,
                        timestamp: new Date()
                    }, ...prev.slice(0, 9)]);
                }
            } catch (e) {
                console.error('WebSocket message error:', e);
            }
        };

        return () => ws.close();
    };

    const showBrowserNotification = (data) => {
        if (Notification.permission === 'granted') {
            new Notification(`🔥 ${data.title}`, {
                body: data.message,
                icon: '/favicon.png',
                badge: '/favicon.png',
                tag: `competition-${data.competition_id}`
            });
        }
    };

    const requestPermissionAndSubscribe = async () => {
        setLoading(true);
        try {
            // Request browser notification permission
            const permission = await Notification.requestPermission();
            
            if (permission !== 'granted') {
                toast.error(isRomanian 
                    ? 'Te rugăm să permiți notificările din setările browserului' 
                    : 'Please allow notifications in browser settings'
                );
                setLoading(false);
                return;
            }

            // Subscribe to backend
            await axios.post(`${API}/api/notifications/subscribe`, {
                endpoint: 'browser-notification',
                keys: { permission: 'granted' }
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });

            setIsSubscribed(true);
            setShowDialog(false);
            toast.success(isRomanian 
                ? '🔔 Notificări activate! Vei primi alerte când competițiile sunt aproape sold out.' 
                : '🔔 Notifications enabled! You\'ll get alerts when competitions are almost sold out.'
            );
        } catch (error) {
            toast.error(isRomanian ? 'Eroare la activare notificări' : 'Failed to enable notifications');
        } finally {
            setLoading(false);
        }
    };

    const unsubscribe = async () => {
        setLoading(true);
        try {
            await axios.delete(`${API}/api/notifications/unsubscribe`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setIsSubscribed(false);
            toast.success(isRomanian ? 'Notificări dezactivate' : 'Notifications disabled');
        } catch (error) {
            toast.error(isRomanian ? 'Eroare la dezactivare' : 'Failed to disable notifications');
        } finally {
            setLoading(false);
        }
    };

    if (!user) return null;

    return (
        <>
            <Button
                variant="ghost"
                size="icon"
                className={`relative ${isSubscribed ? 'text-secondary' : 'text-muted-foreground'}`}
                onClick={() => setShowDialog(true)}
                data-testid="notification-bell"
            >
                {isSubscribed ? (
                    <BellRing className="w-5 h-5" />
                ) : (
                    <Bell className="w-5 h-5" />
                )}
                {notifications.length > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-secondary text-xs rounded-full flex items-center justify-center text-black font-bold">
                        {notifications.length}
                    </span>
                )}
            </Button>

            <Dialog open={showDialog} onOpenChange={setShowDialog}>
                <DialogContent className="glass border-white/10 max-w-md">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Bell className="w-5 h-5 text-primary" />
                            {isRomanian ? 'Notificări Push' : 'Push Notifications'}
                        </DialogTitle>
                        <DialogDescription>
                            {isRomanian 
                                ? 'Primește alerte când competițiile sunt aproape sold out (80%)' 
                                : 'Get alerts when competitions are almost sold out (80%)'
                            }
                        </DialogDescription>
                    </DialogHeader>

                    <div className="py-4 space-y-4">
                        {/* Notification Status */}
                        <div className={`p-4 rounded-xl ${isSubscribed ? 'bg-secondary/20 border border-secondary/30' : 'bg-muted'}`}>
                            <div className="flex items-center gap-3">
                                {isSubscribed ? (
                                    <>
                                        <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
                                            <BellRing className="w-5 h-5 text-secondary" />
                                        </div>
                                        <div className="flex-1">
                                            <p className="font-semibold text-secondary">{isRomanian ? 'Notificări Active' : 'Notifications Active'}</p>
                                            <p className="text-xs text-muted-foreground">{isRomanian ? 'Vei primi alerte automat' : 'You\'ll receive alerts automatically'}</p>
                                        </div>
                                        <Check className="w-5 h-5 text-secondary" />
                                    </>
                                ) : (
                                    <>
                                        <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                                            <BellOff className="w-5 h-5 text-muted-foreground" />
                                        </div>
                                        <div className="flex-1">
                                            <p className="font-semibold">{isRomanian ? 'Notificări Dezactivate' : 'Notifications Disabled'}</p>
                                            <p className="text-xs text-muted-foreground">{isRomanian ? 'Activează pentru a primi alerte' : 'Enable to receive alerts'}</p>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* Recent Notifications */}
                        {notifications.length > 0 && (
                            <div className="space-y-2">
                                <p className="text-sm font-medium text-muted-foreground">{isRomanian ? 'Notificări Recente' : 'Recent Notifications'}</p>
                                <div className="space-y-2 max-h-40 overflow-y-auto">
                                    {notifications.map(notif => (
                                        <div key={notif.id} className="p-3 bg-muted rounded-lg text-sm">
                                            <p className="font-medium">{notif.title}</p>
                                            <p className="text-xs text-muted-foreground">{notif.message}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Action Button */}
                        <Button
                            className={`w-full ${isSubscribed ? 'btn-outline' : 'btn-primary'}`}
                            onClick={isSubscribed ? unsubscribe : requestPermissionAndSubscribe}
                            disabled={loading}
                        >
                            {loading ? (
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : isSubscribed ? (
                                <><BellOff className="w-4 h-4 mr-2" /> {isRomanian ? 'Dezactivează Notificările' : 'Disable Notifications'}</>
                            ) : (
                                <><BellRing className="w-4 h-4 mr-2" /> {isRomanian ? 'Activează Notificările' : 'Enable Notifications'}</>
                            )}
                        </Button>

                        <p className="text-xs text-center text-muted-foreground">
                            {isRomanian 
                                ? '💡 Vei primi notificări când o competiție ajunge la 80% vândut' 
                                : '💡 You\'ll be notified when a competition reaches 80% sold'
                            }
                        </p>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
};

export default NotificationBell;
