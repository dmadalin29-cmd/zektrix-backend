import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Bell, Check, Gift, Star, Percent, Trophy, Sparkles } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ICON_MAP = {
    loyalty: Star,
    wheel: Gift,
    discount: Percent,
    referral: Trophy,
    win: Trophy,
    default: Sparkles
};

const UserNotificationBell = () => {
    const { token, isAuthenticated } = useAuth();
    const { isRomanian } = useLanguage();
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [open, setOpen] = useState(false);
    const dropdownRef = useRef(null);

    useEffect(() => {
        if (!token || !isAuthenticated) return;
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, [token, isAuthenticated]);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const fetchNotifications = async () => {
        try {
            const { data } = await axios.get(`${API}/notifications/my`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setNotifications(data.notifications || []);
            setUnreadCount(data.unread_count || 0);
        } catch {
            // silent fail
        }
    };

    const markAllRead = async () => {
        try {
            await axios.post(`${API}/notifications/read-all`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setNotifications(prev => prev.map(n => ({ ...n, read: true })));
            setUnreadCount(0);
        } catch {
            // silent fail
        }
    };

    if (!isAuthenticated) return null;

    return (
        <div className="relative" ref={dropdownRef} data-testid="user-notification-bell">
            <button
                onClick={() => {
                    setOpen(prev => !prev);
                    if (!open && unreadCount > 0) markAllRead();
                }}
                className="relative flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-xl text-gray-400 hover:text-white hover:bg-white/[0.06] transition-all duration-200"
                data-testid="user-notif-btn"
            >
                <Bell className="w-[18px] h-[18px]" />
                {unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-violet-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-[#0a0614] animate-pulse" data-testid="notif-badge">
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            {open && (
                <div className="absolute right-0 top-full mt-2 w-80 max-h-96 rounded-2xl overflow-hidden z-50 shadow-2xl"
                    style={{
                        background: 'linear-gradient(135deg, rgba(12, 8, 24, 0.98), rgba(8, 4, 16, 0.99))',
                        border: '1px solid rgba(139, 92, 246, 0.2)',
                        backdropFilter: 'blur(20px)'
                    }}
                    data-testid="notif-dropdown"
                >
                    <div className="flex items-center justify-between p-3 border-b border-white/[0.06]">
                        <h3 className="text-sm font-bold text-white">
                            {isRomanian ? 'Notificari' : 'Notifications'}
                        </h3>
                        {unreadCount > 0 && (
                            <button onClick={markAllRead} className="text-[10px] text-violet-400 hover:text-violet-300 flex items-center gap-1" data-testid="mark-all-read">
                                <Check className="w-3 h-3" />
                                {isRomanian ? 'Citeste tot' : 'Mark all read'}
                            </button>
                        )}
                    </div>

                    <div className="overflow-y-auto max-h-72">
                        {notifications.length === 0 ? (
                            <div className="p-6 text-center">
                                <Bell className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                                <p className="text-xs text-gray-500">
                                    {isRomanian ? 'Nicio notificare' : 'No notifications'}
                                </p>
                            </div>
                        ) : (
                            notifications.slice(0, 20).map((notif) => {
                                const Icon = ICON_MAP[notif.type] || ICON_MAP.default;
                                return (
                                    <div
                                        key={notif.notification_id}
                                        className={`flex items-start gap-3 p-3 border-b border-white/[0.03] transition-colors hover:bg-white/[0.03] ${!notif.read ? 'bg-violet-500/[0.04]' : ''}`}
                                        data-testid={`notif-item-${notif.notification_id}`}
                                    >
                                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${!notif.read ? 'bg-violet-500/20' : 'bg-white/[0.04]'}`}>
                                            <Icon className={`w-4 h-4 ${!notif.read ? 'text-violet-400' : 'text-gray-500'}`} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className={`text-xs font-semibold ${!notif.read ? 'text-white' : 'text-gray-400'}`}>{notif.title}</p>
                                            <p className="text-[11px] text-gray-500 leading-relaxed">{notif.message}</p>
                                            <p className="text-[9px] text-gray-600 mt-1">
                                                {new Date(notif.created_at).toLocaleDateString('ro-RO', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                                            </p>
                                        </div>
                                        {!notif.read && (
                                            <div className="w-2 h-2 rounded-full bg-violet-500 shrink-0 mt-1.5" />
                                        )}
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserNotificationBell;
