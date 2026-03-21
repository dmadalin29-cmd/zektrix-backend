import { useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
}

const PushManager = () => {
    const { token, isAuthenticated } = useAuth();
    const attempted = useRef(false);

    useEffect(() => {
        if (!isAuthenticated || !token || attempted.current) return;
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
        // Don't auto-prompt on iOS if not in standalone mode
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone;
        if (isIOS && !isStandalone) return;

        attempted.current = true;

        const trySubscribe = async () => {
            try {
                // Check if already have permission
                if (Notification.permission === 'denied') return;

                // Check if already subscribed on server
                const { data: status } = await axios.get(`${API}/push/status`, {
                    headers: { Authorization: `Bearer ${token}` }
                });

                // Check if this device is already subscribed
                const reg = await navigator.serviceWorker.ready;
                const existingSub = await reg.pushManager.getSubscription();
                if (existingSub && status.subscribed) return; // Already set up

                // If we have permission already, subscribe silently
                if (Notification.permission === 'granted') {
                    await subscribePush(reg, token);
                    return;
                }

                // Wait a bit before asking (don't interrupt user immediately)
                setTimeout(async () => {
                    const permission = await Notification.requestPermission();
                    if (permission === 'granted') {
                        const freshReg = await navigator.serviceWorker.ready;
                        await subscribePush(freshReg, token);
                    }
                }, 5000);
            } catch (e) {
                console.warn('Push auto-subscribe failed:', e);
            }
        };

        trySubscribe();
    }, [isAuthenticated, token]);

    return null;
};

async function subscribePush(reg, token) {
    try {
        const { data: vapidData } = await axios.get(`${API}/push/vapid-key`);
        const applicationServerKey = urlBase64ToUint8Array(vapidData.public_key);

        // Unsubscribe existing if any (to refresh)
        const existingSub = await reg.pushManager.getSubscription();
        if (existingSub) {
            await existingSub.unsubscribe();
        }

        const subscription = await reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey
        });

        const subJson = subscription.toJSON();
        await axios.post(`${API}/push/subscribe`, {
            endpoint: subJson.endpoint,
            keys: subJson.keys
        }, {
            headers: { Authorization: `Bearer ${token}` }
        });

        console.log('Push notification subscription successful');
    } catch (e) {
        console.error('Push subscribe error:', e);
    }
}

export default PushManager;
