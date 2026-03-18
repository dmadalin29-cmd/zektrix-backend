import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Bell, BellOff, BellRing, Check, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const NotificationBell = () => {
    const { user, token } = useAuth();
    const { isRomanian } = useLanguage();
    const [isSubscribed, setIsSubscribed] = useState(false);
    const [showDialog, setShowDialog] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (user && token) {
            checkSubscriptionStatus();
        }
    }, [user, token]);

    const checkSubscriptionStatus = async () => {
        try {
            const response = await axios.get(`${API}/notifications/status`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setIsSubscribed(response.data.subscribed);
        } catch (error) {
            console.error('Failed to check notification status');
        }
    };

    const urlBase64ToUint8Array = (base64String) => {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    };

    const requestPermissionAndSubscribe = async () => {
        setLoading(true);
        try {
            if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
                toast.error(isRomanian ? 'Browser-ul nu suporta notificari push' : 'Browser does not support push notifications');
                return;
            }

            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                toast.error(isRomanian 
                    ? 'Permite notificarile din setarile browserului' 
                    : 'Please allow notifications in browser settings'
                );
                return;
            }

            // Get VAPID public key from backend
            const vapidRes = await axios.get(`${API}/push/vapid-key`);
            const vapidKey = vapidRes.data.public_key;
            const applicationServerKey = urlBase64ToUint8Array(vapidKey);

            // Register service worker and subscribe
            const reg = await navigator.serviceWorker.ready;
            
            // Unsubscribe existing
            const existingSub = await reg.pushManager.getSubscription();
            if (existingSub) {
                await existingSub.unsubscribe();
            }

            const subscription = await reg.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            });

            const subJson = subscription.toJSON();

            // Send real subscription to backend
            await axios.post(`${API}/notifications/subscribe`, {
                endpoint: subJson.endpoint,
                keys: subJson.keys
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });

            setIsSubscribed(true);
            setShowDialog(false);
            toast.success(isRomanian 
                ? 'Notificari activate!' 
                : 'Notifications enabled!'
            );
        } catch (error) {
            console.error('Push subscription error:', error);
            toast.error(isRomanian ? 'Eroare la activare notificari' : 'Failed to enable notifications');
        } finally {
            setLoading(false);
        }
    };

    const unsubscribe = async () => {
        setLoading(true);
        try {
            // Unsubscribe from browser push
            const reg = await navigator.serviceWorker.ready;
            const existingSub = await reg.pushManager.getSubscription();
            if (existingSub) {
                await existingSub.unsubscribe();
            }

            await axios.delete(`${API}/notifications/unsubscribe`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setIsSubscribed(false);
            toast.success(isRomanian ? 'Notificari dezactivate' : 'Notifications disabled');
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
            </Button>

            <Dialog open={showDialog} onOpenChange={setShowDialog}>
                <DialogContent className="glass border-white/10">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Bell className="w-5 h-5 text-primary" />
                            {isRomanian ? 'Notificari Push' : 'Push Notifications'}
                        </DialogTitle>
                        <DialogDescription>
                            {isRomanian 
                                ? 'Primeste alerte cand competitiile sunt aproape sold out' 
                                : 'Get alerts when competitions are almost sold out'
                            }
                        </DialogDescription>
                    </DialogHeader>

                    <div className="py-4 space-y-4">
                        <div className={`p-4 rounded-xl ${isSubscribed ? 'bg-secondary/20 border border-secondary/30' : 'bg-muted'}`}>
                            <div className="flex items-center gap-3">
                                {isSubscribed ? (
                                    <>
                                        <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
                                            <BellRing className="w-5 h-5 text-secondary" />
                                        </div>
                                        <div className="flex-1">
                                            <p className="font-semibold text-secondary">{isRomanian ? 'Notificari Active' : 'Notifications Active'}</p>
                                            <p className="text-xs text-muted-foreground">{isRomanian ? 'Vei primi alerte automat' : 'You will receive alerts automatically'}</p>
                                        </div>
                                        <Check className="w-5 h-5 text-secondary" />
                                    </>
                                ) : (
                                    <>
                                        <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                                            <BellOff className="w-5 h-5 text-muted-foreground" />
                                        </div>
                                        <div className="flex-1">
                                            <p className="font-semibold">{isRomanian ? 'Notificari Dezactivate' : 'Notifications Disabled'}</p>
                                            <p className="text-xs text-muted-foreground">{isRomanian ? 'Activeaza pentru a primi alerte' : 'Enable to receive alerts'}</p>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>

                        <Button
                            className={`w-full ${isSubscribed ? 'btn-outline' : 'btn-primary'}`}
                            onClick={isSubscribed ? unsubscribe : requestPermissionAndSubscribe}
                            disabled={loading}
                        >
                            {loading ? (
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : isSubscribed ? (
                                <><BellOff className="w-4 h-4 mr-2" /> {isRomanian ? 'Dezactiveaza' : 'Disable'}</>
                            ) : (
                                <><BellRing className="w-4 h-4 mr-2" /> {isRomanian ? 'Activeaza Notificarile' : 'Enable Notifications'}</>
                            )}
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
};

export default NotificationBell;
