import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';
import { 
    AreaChart, Area, ResponsiveContainer
} from 'recharts';
import { 
    Ticket, History, ArrowRight, Loader2, Trophy, 
    ArrowUpRight, Gift, 
    ChevronRight, Activity, User, Save, Edit3, Bell,
    Copy, Share2, Users, Crown, CheckCircle2, Clock, Sparkles, RefreshCw
} from 'lucide-react';
import { Input } from '../components/ui/input';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Animated Number
const AnimatedNumber = ({ value, prefix = '', suffix = '', decimals = 2 }) => {
    const [display, setDisplay] = useState(0);
    useEffect(() => {
        const duration = 1200;
        const steps = 40;
        const increment = value / steps;
        let current = 0;
        const timer = setInterval(() => {
            current += increment;
            if (current >= value) { setDisplay(value); clearInterval(timer); }
            else setDisplay(current);
        }, duration / steps);
        return () => clearInterval(timer);
    }, [value]);
    return <span>{prefix}{decimals > 0 ? display.toFixed(decimals) : Math.floor(display).toLocaleString('ro-RO')}{suffix}</span>;
};

// Sparkline
const Sparkline = ({ data, color, height = 40 }) => (
    <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.map((v, i) => ({ v, i }))}>
                <defs>
                    <linearGradient id={`spark-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={color} stopOpacity={0.4}/>
                        <stop offset="100%" stopColor={color} stopOpacity={0}/>
                    </linearGradient>
                </defs>
                <Area type="monotone" dataKey="v" stroke={color} strokeWidth={2} fill={`url(#spark-${color.replace('#', '')})`} />
            </AreaChart>
        </ResponsiveContainer>
    </div>
);

// Stat Card
const StatCard = ({ icon: Icon, label, value, gradient, sparkData, onClick, prefix = '' }) => (
    <div 
        onClick={onClick}
        className={`group relative rounded-2xl p-5 transition-all duration-500 hover:scale-[1.02] ${onClick ? 'cursor-pointer' : ''}`}
        style={{
            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
            border: '1px solid rgba(139, 92, 246, 0.15)',
            boxShadow: '0 4px 24px rgba(0, 0, 0, 0.3)'
        }}
    >
        <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"
            style={{ background: `radial-gradient(circle at 50% 50%, ${gradient?.split(' ')[0] || 'rgba(139,92,246,0.15)'}, transparent 70%)` }} />
        <div className="relative z-10">
            <div className="flex items-start justify-between mb-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110`}
                    style={{ background: gradient || 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}>
                    <Icon className="w-6 h-6 text-white" />
                </div>
            </div>
            <p className="text-sm text-gray-400 mb-1 font-medium">{label}</p>
            <p className="text-3xl font-bold text-white tracking-tight">
                <AnimatedNumber value={value} prefix={prefix} decimals={prefix === '£' ? 2 : 0} />
            </p>
            {sparkData && (
                <div className="mt-4 -mx-1">
                    <Sparkline data={sparkData} color={gradient?.includes('emerald') ? '#10b981' : gradient?.includes('orange') ? '#f97316' : '#8b5cf6'} />
                </div>
            )}
        </div>
    </div>
);

// Nav Tab
const NavTab = ({ icon: Icon, label, active, onClick, badge }) => (
    <button
        onClick={onClick}
        className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 whitespace-nowrap
            ${active 
                ? 'text-white' 
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
        style={active ? {
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(124, 58, 237, 0.2) 100%)',
            boxShadow: '0 0 20px rgba(139, 92, 246, 0.3)'
        } : {}}
    >
        <Icon className={`w-4 h-4 ${active ? 'text-violet-400' : ''}`} />
        <span>{label}</span>
        {badge !== undefined && badge > 0 && (
            <span className="px-1.5 py-0.5 bg-violet-500/30 text-violet-300 text-xs font-bold rounded-full min-w-[20px] text-center">
                {badge}
            </span>
        )}
    </button>
);

// Empty State
const EmptyState = ({ icon: Icon, title, description, action, actionLabel }) => (
    <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-20 h-20 rounded-2xl bg-violet-500/10 flex items-center justify-center mb-4">
            <Icon className="w-10 h-10 text-violet-400" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
        <p className="text-gray-500 max-w-md mb-6">{description}</p>
        {action && (
            <Button onClick={action} className="bg-violet-600 hover:bg-violet-500">
                {actionLabel}
            </Button>
        )}
    </div>
);

// Account Tab Component
const AccountTab = ({ user, token, refreshUser, isRomanian }) => {
    const [form, setForm] = useState({
        first_name: user?.first_name || '',
        last_name: user?.last_name || '',
        phone: user?.phone || '',
        username: user?.username || ''
    });
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        try {
            const authToken = token || localStorage.getItem('zektrix_token');
            await axios.put(`${API}/auth/profile`, form, { headers: { Authorization: `Bearer ${authToken}` } });
            toast.success(isRomanian ? 'Profil actualizat cu succes!' : 'Profile updated!');
            if (refreshUser) await refreshUser();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Eroare la salvare');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="rounded-2xl p-6 md:p-8" data-testid="account-tab"
            style={{ background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9), rgba(10, 6, 20, 0.95))', border: '1px solid rgba(139, 92, 246, 0.15)' }}>
            <div className="flex items-center gap-3 mb-8">
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
                    style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}>
                    <User className="w-7 h-7 text-white" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-white">{isRomanian ? 'Contul Meu' : 'My Account'}</h2>
                    <p className="text-sm text-gray-500">{user?.email}</p>
                </div>
            </div>
            <div className="grid md:grid-cols-2 gap-4 mb-6">
                <div>
                    <label className="text-sm text-gray-400 mb-1 block">{isRomanian ? 'Prenume' : 'First Name'}</label>
                    <Input value={form.first_name} onChange={e => setForm(p => ({ ...p, first_name: e.target.value }))}
                        className="bg-white/5 border-white/10" data-testid="account-first-name" />
                </div>
                <div>
                    <label className="text-sm text-gray-400 mb-1 block">{isRomanian ? 'Nume' : 'Last Name'}</label>
                    <Input value={form.last_name} onChange={e => setForm(p => ({ ...p, last_name: e.target.value }))}
                        className="bg-white/5 border-white/10" data-testid="account-last-name" />
                </div>
                <div>
                    <label className="text-sm text-gray-400 mb-1 block">{isRomanian ? 'Utilizator' : 'Username'}</label>
                    <Input value={form.username} onChange={e => setForm(p => ({ ...p, username: e.target.value }))}
                        className="bg-white/5 border-white/10" data-testid="account-username" />
                </div>
                <div>
                    <label className="text-sm text-gray-400 mb-1 block">{isRomanian ? 'Telefon' : 'Phone'}</label>
                    <Input value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))}
                        className="bg-white/5 border-white/10" data-testid="account-phone" />
                </div>
            </div>
            <Button onClick={handleSave} disabled={saving} className="bg-violet-600 hover:bg-violet-500" data-testid="account-save-btn">
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                {isRomanian ? 'Salvează Modificările' : 'Save Changes'}
            </Button>
        </div>
    );
};

const DashboardPage = () => {
    const { user, token, refreshUser } = useAuth();
    const { t, isRomanian } = useLanguage();
    const navigate = useNavigate();
    const location = useLocation();

    const getActiveTab = () => {
        if (location.pathname.includes('/account')) return 'account';
        if (location.pathname.includes('/locs')) return 'locs';
        if (location.pathname.includes('/history')) return 'history';
        if (location.pathname.includes('/referral')) return 'referral';
        return 'overview';
    };

    const [activeTab, setActiveTab] = useState(getActiveTab());
    const [locs, setLocs] = useState([]);
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [pushSubscribed, setPushSubscribed] = useState(null);

    // Check push status
    useEffect(() => {
        if (token) {
            axios.get(`${API}/push/status`, { headers: { Authorization: `Bearer ${token}` } })
                .then(r => setPushSubscribed(r.data.subscribed))
                .catch(() => setPushSubscribed(false));
        }
    }, [token]);

    const handlePushSubscribe = async () => {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            toast.error(isRomanian ? 'Browser-ul nu suportă notificări push' : 'Browser does not support push notifications');
            return;
        }
        try {
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') { toast.error(isRomanian ? 'Permite notificările din setările browser-ului' : 'Allow notifications in browser settings'); return; }
            const vapidRes = await axios.get(`${API}/push/vapid-key`);
            const key = vapidRes.data.public_key;
            const padding = '='.repeat((4 - key.length % 4) % 4);
            const base64 = (key + padding).replace(/-/g, '+').replace(/_/g, '/');
            const rawData = window.atob(base64);
            const arr = new Uint8Array(rawData.length);
            for (let i = 0; i < rawData.length; ++i) arr[i] = rawData.charCodeAt(i);
            const reg = await navigator.serviceWorker.ready;
            const old = await reg.pushManager.getSubscription();
            if (old) await old.unsubscribe();
            const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: arr });
            const j = sub.toJSON();
            await axios.post(`${API}/push/subscribe`, { endpoint: j.endpoint, keys: j.keys }, { headers: { Authorization: `Bearer ${token}` } });
            setPushSubscribed(true);
            toast.success(isRomanian ? 'Notificări activate!' : 'Notifications enabled!');
        } catch (e) {
            toast.error(isRomanian ? 'Eroare la activare notificări' : 'Error enabling notifications');
        }
    };

    // Fetch on mount and when token changes
    useEffect(() => { 
        const authToken = token || localStorage.getItem('zektrix_token');
        if (authToken) {
            fetchData();
        } else {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => { setActiveTab(getActiveTab()); }, [location.pathname]);

    const fetchData = async () => {
        try {
            const authToken = token || localStorage.getItem('zektrix_token');
            
            if (!authToken) {
                toast.error('Nu ești autentificat. Te rugăm să te loghezi.');
                setLoading(false);
                return;
            }
            const headers = { Authorization: `Bearer ${authToken}` };
            
            // Fetch locs and transactions
            const [locsRes, txnRes] = await Promise.all([
                axios.get(`${API}/tickets/my`, { headers }),
                axios.get(`${API}/wallet/transactions`, { headers }).catch(() => ({ data: [] }))
            ]);
            setLocs(locsRes.data || []);
            setTransactions(txnRes.data || []);
        } catch (error) {
            console.error('Fetch error:', error);
            if (error.response && (error.response.status === 401 || error.response.status === 403)) {
                localStorage.removeItem('zektrix_token');
                localStorage.removeItem('zektrix_user');
                toast.error('Sesiunea a expirat. Te rugăm să te autentifici din nou.');
                navigate('/login');
                return;
            }
            if (error.message === 'Network Error') {
                toast.error('Eroare de conexiune. Verifică conexiunea la internet.');
            } else {
                const errorMsg = error.response?.data?.detail || error.message || 'Eroare necunoscută';
                toast.error(`Eroare: ${errorMsg}`);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleTabChange = (value) => {
        setActiveTab(value);
        const routes = { overview: '/dashboard', locs: '/dashboard/locs', history: '/dashboard/history', referral: '/dashboard/referral', account: '/dashboard/account' };
        navigate(routes[value] || '/dashboard');
    };

    const groupedLocs = locs.reduce((acc, loc) => {
        const key = loc.competition_id;
        if (!acc[key]) acc[key] = { competition_id: loc.competition_id, competition_title: loc.competition_title, locs: [] };
        acc[key].locs.push(loc);
        return acc;
    }, {});

    const recentTransactions = transactions.slice(0, 5);
    const sparkData = useMemo(() => [20, 35, 25, 45, 55, 40, 60, 50, 70, 65, 80, 75], []);

    const navItems = [
        { id: 'overview', icon: Activity, label: isRomanian ? 'Prezentare' : 'Overview' },
        { id: 'locs', icon: Ticket, label: isRomanian ? 'Locurile Mele' : 'My Locs', badge: locs.length },
        { id: 'history', icon: History, label: isRomanian ? 'Istoric' : 'History' },
        { id: 'referral', icon: Gift, label: 'Referral' },
        { id: 'account', icon: User, label: isRomanian ? 'Contul Meu' : 'My Account' },
    ];

    return (
        <div className="min-h-screen" data-testid="dashboard-page">
            <Navbar />
            
            <main className="pt-24 pb-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-8">
                        <div>
                            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                                {t('welcome')}, <span className="bg-gradient-to-r from-[#A666FF] to-[#FF5E00] bg-clip-text text-transparent">{user?.first_name || user?.username}</span>
                            </h1>
                            <p className="text-gray-500">{t('dashboard_subtitle')}</p>
                        </div>
                    </div>

                    {/* Navigation Tabs */}
                    <div className="flex gap-2 mb-8 overflow-x-auto pb-2 hide-scrollbar">
                        {navItems.map(item => (
                            <NavTab 
                                key={item.id}
                                {...item}
                                active={activeTab === item.id}
                                onClick={() => handleTabChange(item.id)}
                            />
                        ))}
                    </div>

                    {/* Content */}
                    <div className="space-y-6">
                        {/* Overview Tab */}
                        {activeTab === 'overview' && (
                            <>
                                {/* Stats Grid */}
                                <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                                    <StatCard 
                                        icon={Ticket} 
                                        label="Total Locuri" 
                                        value={locs.length} 
                                        gradient="linear-gradient(135deg, #8b5cf6, #7c3aed)" 
                                        sparkData={sparkData}
                                        onClick={() => handleTabChange('locs')}
                                    />
                                    <StatCard 
                                        icon={Trophy} 
                                        label={isRomanian ? 'Competiții' : 'Competitions'} 
                                        value={Object.keys(groupedLocs).length} 
                                        gradient="linear-gradient(135deg, #f97316, #ea580c)" 
                                    />
                                    <StatCard 
                                        icon={History} 
                                        label={isRomanian ? 'Tranzacții' : 'Transactions'} 
                                        value={transactions.length} 
                                        gradient="linear-gradient(135deg, #06b6d4, #0891b2)" 
                                        onClick={() => handleTabChange('history')}
                                    />
                                </div>

                                {/* Push Notification Banner */}
                                {pushSubscribed === false && (
                                    <div className="rounded-2xl p-4 flex items-center justify-between"
                                        style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                                                <Bell className="w-5 h-5 text-emerald-400" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-semibold text-white">{isRomanian ? 'Activează Notificările' : 'Enable Notifications'}</p>
                                                <p className="text-xs text-gray-400">{isRomanian ? 'Fii primul care află când câștigi sau când se apropie extragerea' : 'Be the first to know when you win or a draw is near'}</p>
                                            </div>
                                        </div>
                                        <Button onClick={handlePushSubscribe} size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white" data-testid="dashboard-push-subscribe">
                                            <Bell className="w-4 h-4 mr-1" /> {isRomanian ? 'Activează' : 'Enable'}
                                        </Button>
                                    </div>
                                )}

                                {/* Quick Actions */}
                                <div className="grid md:grid-cols-2 gap-4">
                                    <Link to="/competitions" className="group">
                                        <div className="rounded-2xl p-6 transition-all duration-300 hover:scale-[1.02]"
                                            style={{
                                                background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                                border: '1px solid rgba(139, 92, 246, 0.15)'
                                            }}>
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <h3 className="font-bold text-white text-lg mb-1">{isRomanian ? 'Vezi Competițiile' : 'Browse Competitions'}</h3>
                                                    <p className="text-sm text-gray-500">{isRomanian ? 'Participă la competiții și poți primi premii' : 'Enter exciting competitions and win prizes'}</p>
                                                </div>
                                                <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center group-hover:bg-violet-500/30 transition-colors">
                                                    <ArrowRight className="w-6 h-6 text-violet-400" />
                                                </div>
                                            </div>
                                        </div>
                                    </Link>
                                    <Link to="/winners" className="group">
                                        <div className="rounded-2xl p-6 transition-all duration-300 hover:scale-[1.02]"
                                            style={{
                                                background: 'linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(234, 88, 12, 0.05) 100%)',
                                                border: '1px solid rgba(249, 115, 22, 0.2)'
                                            }}>
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <h3 className="font-bold text-white text-lg mb-1">{isRomanian ? 'Vezi Premianții' : 'View Winners'}</h3>
                                                    <p className="text-sm text-gray-500">{isRomanian ? 'Descoperă cine a primit premii' : 'See who won prizes'}</p>
                                                </div>
                                                <div className="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center group-hover:bg-orange-500/30 transition-colors">
                                                    <Trophy className="w-6 h-6 text-orange-400" />
                                                </div>
                                            </div>
                                        </div>
                                    </Link>
                                </div>

                                {/* Recent Activity */}
                                {recentTransactions.length > 0 && (
                                    <div className="rounded-2xl p-6"
                                        style={{
                                            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                            border: '1px solid rgba(139, 92, 246, 0.15)'
                                        }}>
                                        <div className="flex items-center justify-between mb-5">
                                            <h3 className="font-bold text-white text-lg">{isRomanian ? 'Activitate Recentă' : 'Recent Activity'}</h3>
                                            <Button variant="ghost" size="sm" onClick={() => handleTabChange('history')} className="text-violet-400 hover:text-violet-300">
                                                {isRomanian ? 'Vezi Tot' : 'View All'} <ChevronRight className="w-4 h-4 ml-1" />
                                            </Button>
                                        </div>
                                        <div className="space-y-3">
                                            {recentTransactions.map((txn) => (
                                                <div key={txn.transaction_id} className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                                                    <div className="flex items-center gap-3">
                                                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                                                            txn.amount > 0 ? 'bg-emerald-500/20' : 'bg-violet-500/20'
                                                        }`}>
                                                            {txn.amount > 0 ? (
                                                                <ArrowUpRight className="w-5 h-5 text-emerald-400" />
                                                            ) : (
                                                            <Ticket className="w-5 h-5 text-violet-400" />
                                                            )}
                                                        </div>
                                                        <div>
                                                            <p className="text-sm font-medium text-white">{txn.description}</p>
                                                            <p className="text-xs text-gray-500">
                                                                {new Date(txn.created_at).toLocaleDateString('ro-RO')}
                                                            </p>
                                                        </div>
                                                    </div>
                                                    <span className={`font-bold ${txn.amount > 0 ? 'text-emerald-400' : 'text-violet-400'}`}>
                                                        {txn.amount > 0 ? '+' : ''}£{Math.abs(txn.amount).toFixed(2)}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}

                        {/* Locs Tab */}
                        {activeTab === 'locs' && (
                            loading ? (
                                <div className="flex justify-center py-12">
                                    <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
                                </div>
                            ) : Object.keys(groupedLocs).length > 0 ? (
                                <div className="grid md:grid-cols-2 gap-4">
                                    {Object.values(groupedLocs).map((group) => (
                                        <div key={group.competition_id} 
                                            className="rounded-2xl p-5 transition-all duration-300 hover:scale-[1.01]"
                                            style={{
                                                background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                                border: '1px solid rgba(139, 92, 246, 0.15)'
                                            }}
                                            data-testid={`locs-group-${group.competition_id}`}
                                        >
                                            <div className="flex items-center justify-between mb-4">
                                                <h3 className="font-bold text-white">{group.competition_title || 'Competition'}</h3>
                                                <Badge className="bg-violet-500/20 text-violet-400 border-violet-500/30">
                                                    {group.locs.length} {group.locs.length === 1 ? (isRomanian ? 'loc' : 'spot') : (isRomanian ? 'locuri' : 'spots')}
                                                </Badge>
                                            </div>
                                            <div className="flex flex-wrap gap-2 mb-4">
                                                {group.locs.sort((a, b) => a.ticket_number - b.ticket_number).map((loc) => (
                                                    <span key={loc.ticket_id} 
                                                        className="px-3 py-1.5 rounded-lg font-mono font-bold text-sm"
                                                        style={{
                                                            background: 'linear-gradient(135deg, #8b5cf6, #f97316)',
                                                            boxShadow: '0 0 15px rgba(139, 92, 246, 0.3)'
                                                        }}>
                                                        #{loc.ticket_number}
                                                    </span>
                                                ))}
                                            </div>
                                            <Link to={`/competitions/${group.competition_id}`}>
                                                <Button variant="ghost" size="sm" className="text-violet-400 hover:text-violet-300 p-0">
                                                    {isRomanian ? 'Vezi Competiția' : 'View Competition'} <ArrowRight className="w-4 h-4 ml-1" />
                                                </Button>
                                            </Link>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <EmptyState 
                                    icon={Ticket} 
                                    title={isRomanian ? 'Niciun Loc' : 'No Locs Yet'}
                                    description={isRomanian ? 'Cumpără locuri pentru a participa la competiții' : 'Purchase locs to enter competitions'}
                                    action={() => navigate('/competitions')}
                                    actionLabel={isRomanian ? 'Vezi Competițiile' : 'Browse Competitions'}
                                />
                            )
                        )}

                        {/* History Tab */}
                        {activeTab === 'history' && (
                            loading ? (
                                <div className="flex justify-center py-12">
                                    <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
                                </div>
                            ) : transactions.length > 0 ? (
                                <div className="rounded-2xl overflow-hidden"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                        border: '1px solid rgba(139, 92, 246, 0.15)'
                                    }}>
                                    <div className="overflow-x-auto">
                                        <table className="w-full">
                                            <thead>
                                                <tr className="border-b border-white/10">
                                                    <th className="text-left text-xs font-bold uppercase tracking-wider text-violet-400 py-4 px-5">{isRomanian ? 'Data' : 'Date'}</th>
                                                    <th className="text-left text-xs font-bold uppercase tracking-wider text-violet-400 py-4 px-5">{isRomanian ? 'Tip' : 'Type'}</th>
                                                    <th className="text-left text-xs font-bold uppercase tracking-wider text-violet-400 py-4 px-5">{isRomanian ? 'Descriere' : 'Description'}</th>
                                                    <th className="text-left text-xs font-bold uppercase tracking-wider text-violet-400 py-4 px-5">{isRomanian ? 'Status' : 'Status'}</th>
                                                    <th className="text-right text-xs font-bold uppercase tracking-wider text-violet-400 py-4 px-5">{isRomanian ? 'Sumă' : 'Amount'}</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {transactions.map((txn) => (
                                                    <tr key={txn.transaction_id} className="border-b border-white/5 hover:bg-white/5 transition-colors" data-testid={`txn-${txn.transaction_id}`}>
                                                        <td className="py-4 px-5 text-sm text-gray-300">
                                                            {new Date(txn.created_at).toLocaleDateString('ro-RO')}
                                                        </td>
                                                        <td className="py-4 px-5">
                                                            <Badge className="bg-violet-500/20 text-violet-400 border-violet-500/30 capitalize">
                                                                {txn.transaction_type.replace('_', ' ')}
                                                            </Badge>
                                                        </td>
                                                        <td className="py-4 px-5 text-sm text-gray-400">{txn.description}</td>
                                                        <td className="py-4 px-5">
                                                            <Badge className={
                                                                txn.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                                                                txn.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
                                                                'bg-red-500/20 text-red-400 border-red-500/30'
                                                            }>
                                                                {txn.status}
                                                            </Badge>
                                                        </td>
                                                        <td className={`py-4 px-5 text-right font-bold ${txn.amount > 0 ? 'text-emerald-400' : 'text-violet-400'}`}>
                                                            {txn.amount > 0 ? '+' : ''}£{Math.abs(txn.amount).toFixed(2)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ) : (
                                <EmptyState 
                                    icon={History} 
                                    title={isRomanian ? 'Niciun Istoric' : 'No Transaction History'}
                                    description={isRomanian ? 'Istoricul tranzacțiilor va apărea aici' : 'Your transaction history will appear here'}
                                />
                            )
                        )}

                        {/* Referral Tab */}
                        {activeTab === 'referral' && <ReferralTab user={user} token={token} isRomanian={isRomanian} />}

                        {/* Account Tab */}
                        {activeTab === 'account' && <AccountTab user={user} token={token} refreshUser={refreshUser} isRomanian={isRomanian} />}
                    </div>
                </div>
            </main>
        </div>
    );
};

const ReferralTab = ({ user, token, isRomanian }) => {
    const [referralData, setReferralData] = React.useState(null);
    const [leaderboard, setLeaderboard] = React.useState([]);
    const [customCode, setCustomCode] = React.useState('');
    const [editingCode, setEditingCode] = React.useState(false);
    const [saving, setSaving] = React.useState(false);
    const [loading, setLoading] = React.useState(true);
    const headers = { Authorization: `Bearer ${token}` };

    React.useEffect(() => {
        if (!token) return;
        setLoading(true);
        Promise.all([
            axios.get(`${API}/referral/my`, { headers }),
            axios.get(`${API}/referral/leaderboard`)
        ]).then(([refRes, lbRes]) => {
            setReferralData(refRes.data);
            setCustomCode(refRes.data.referral_code || '');
            setLeaderboard(lbRes.data || []);
        }).catch(() => {}).finally(() => setLoading(false));
    }, [token]);

    const handleCustomize = async () => {
        if (!customCode.trim()) return;
        setSaving(true);
        try {
            const { data } = await axios.post(`${API}/referral/customize`, { code: customCode }, { headers });
            setReferralData(p => ({ ...p, referral_code: data.referral_code, referral_link: data.referral_link }));
            setEditingCode(false);
            toast.success(isRomanian ? 'Cod actualizat!' : 'Code updated!');
        } catch (e) {
            toast.error(e.response?.data?.detail || 'Error');
        }
        setSaving(false);
    };

    const copyLink = () => {
        navigator.clipboard.writeText(referralData?.referral_link || `https://zektrix.uk?ref=${user?.referral_code}`);
        toast.success(isRomanian ? 'Link copiat!' : 'Link copied!');
    };

    const shareWhatsApp = () => {
        const text = isRomanian
            ? `Hai pe Zektrix UK! Castiga premii incredibile. Foloseste codul meu ${referralData?.referral_code} si primesti £2 bonus! ${referralData?.referral_link}`
            : `Join Zektrix UK! Win amazing prizes. Use my code ${referralData?.referral_code} and get £2 bonus! ${referralData?.referral_link}`;
        window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
    };

    if (loading) return <div className="flex justify-center p-12"><div className="w-8 h-8 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" /></div>;

    return (
        <div className="space-y-5" data-testid="referral-tab">
            {/* Hero Card */}
            <div className="relative overflow-hidden rounded-3xl p-6" style={{
                background: 'linear-gradient(135deg, rgba(139,92,246,0.12) 0%, rgba(249,115,22,0.08) 50%, rgba(139,92,246,0.06) 100%)',
                border: '1px solid rgba(139,92,246,0.2)'
            }}>
                <div className="absolute top-0 right-0 w-48 h-48 bg-violet-500/5 rounded-full blur-3xl" />
                <div className="relative">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#8B3DFF] to-[#FF5E00] flex items-center justify-center shadow-[0_0_20px_rgba(139,61,255,0.3)]">
                            <Gift className="w-7 h-7 text-white" />
                        </div>
                        <div>
                            <h2 className="text-xl font-black text-white tracking-tight">{isRomanian ? 'Invita Prieteni' : 'Invite Friends'}</h2>
                            <p className="text-sm text-[#A39EBD]">{isRomanian ? 'Tu primesti £3, prietenul £2' : 'You get £3, friend gets £2'}</p>
                        </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-3 gap-3 mb-5">
                        <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-center">
                            <Users className="w-4 h-4 text-violet-400 mx-auto mb-1" />
                            <p className="text-lg font-bold text-white">{referralData?.total_invited || 0}</p>
                            <p className="text-[10px] text-[#6E6987]">{isRomanian ? 'Invitati' : 'Invited'}</p>
                        </div>
                        <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-center">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                            <p className="text-lg font-bold text-emerald-400">{referralData?.total_completed || 0}</p>
                            <p className="text-[10px] text-[#6E6987]">{isRomanian ? 'Finalizati' : 'Completed'}</p>
                        </div>
                        <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-center">
                            <Sparkles className="w-4 h-4 text-amber-400 mx-auto mb-1" />
                            <p className="text-lg font-bold text-amber-400">£{(referralData?.total_earnings || 0).toFixed(2)}</p>
                            <p className="text-[10px] text-[#6E6987]">{isRomanian ? 'Castigat' : 'Earned'}</p>
                        </div>
                    </div>

                    {/* Referral Code */}
                    <div className="p-4 rounded-2xl bg-white/[0.04] border border-white/[0.06] mb-4">
                        <p className="text-xs text-[#6E6987] mb-2">{isRomanian ? 'Codul Tau de Referral' : 'Your Referral Code'}</p>
                        {editingCode ? (
                            <div className="flex gap-2">
                                <Input value={customCode} onChange={e => setCustomCode(e.target.value.toUpperCase())}
                                    className="bg-white/[0.06] border-white/[0.1] text-white font-mono text-lg h-10 uppercase" maxLength={15}
                                    placeholder="CODTAU" data-testid="custom-code-input" />
                                <Button onClick={handleCustomize} disabled={saving} size="sm"
                                    className="bg-[#8B3DFF] hover:bg-[#A666FF] text-white" data-testid="save-code-btn">
                                    {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                </Button>
                                <Button onClick={() => setEditingCode(false)} size="sm" variant="ghost" className="text-gray-400">
                                    <span className="text-xs">{isRomanian ? 'Anuleaza' : 'Cancel'}</span>
                                </Button>
                            </div>
                        ) : (
                            <div className="flex items-center justify-between">
                                <span className="text-2xl font-mono font-black text-[#A666FF] tracking-wider" data-testid="referral-code-display">
                                    {referralData?.referral_code || 'ZEKTRIX'}
                                </span>
                                <Button onClick={() => setEditingCode(true)} variant="ghost" size="sm" className="text-[#6E6987] hover:text-white gap-1" data-testid="edit-code-btn">
                                    <Edit3 className="w-3.5 h-3.5" /> {isRomanian ? 'Personalizeaza' : 'Customize'}
                                </Button>
                            </div>
                        )}
                    </div>

                    {/* Share Buttons */}
                    <div className="grid grid-cols-2 gap-2">
                        <Button onClick={copyLink} className="bg-[#8B3DFF] hover:bg-[#A666FF] text-white rounded-xl gap-2 h-11" data-testid="copy-ref-link">
                            <Copy className="w-4 h-4" /> {isRomanian ? 'Copiaza Link' : 'Copy Link'}
                        </Button>
                        <Button onClick={shareWhatsApp} className="bg-[#25D366] hover:bg-[#22c55e] text-white rounded-xl gap-2 h-11" data-testid="share-whatsapp">
                            <Share2 className="w-4 h-4" /> WhatsApp
                        </Button>
                    </div>
                </div>
            </div>

            {/* How it works */}
            <div className="rounded-2xl p-5" style={{
                background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                border: '1px solid rgba(139,92,246,0.1)'
            }}>
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#A666FF]" /> {isRomanian ? 'Cum Functioneaza' : 'How It Works'}
                </h3>
                <div className="space-y-3">
                    {[
                        { step: '1', text: isRomanian ? 'Trimite link-ul tau de referral prietenilor' : 'Send your referral link to friends', icon: Share2 },
                        { step: '2', text: isRomanian ? 'Prietenul se inregistreaza cu codul tau' : 'Friend signs up with your code', icon: User },
                        { step: '3', text: isRomanian ? 'Cand prietenul cumpara primul bilet, amandoi primiti credit!' : 'When friend buys first ticket, both get credit!', icon: Gift },
                    ].map((s, i) => {
                        const Icon = s.icon;
                        return (
                            <div key={i} className="flex items-center gap-3 p-2.5 rounded-xl bg-white/[0.02]">
                                <div className="w-8 h-8 rounded-lg bg-[#8B3DFF]/15 flex items-center justify-center shrink-0">
                                    <Icon className="w-4 h-4 text-[#A666FF]" />
                                </div>
                                <p className="text-sm text-[#A39EBD]"><span className="text-white font-semibold">{s.step}.</span> {s.text}</p>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Invited Friends List */}
            {referralData?.invited_list?.length > 0 && (
                <div className="rounded-2xl overflow-hidden" style={{
                    background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                    border: '1px solid rgba(139,92,246,0.1)'
                }}>
                    <div className="p-4 border-b border-white/[0.06]">
                        <h3 className="text-sm font-bold text-white">{isRomanian ? 'Prieteni Invitati' : 'Invited Friends'}</h3>
                    </div>
                    <div className="divide-y divide-white/[0.04]">
                        {referralData.invited_list.map((f, i) => (
                            <div key={i} className="flex items-center gap-3 p-3">
                                <div className="w-8 h-8 rounded-lg bg-white/[0.04] flex items-center justify-center">
                                    <User className="w-4 h-4 text-gray-400" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-white truncate">{f.username}</p>
                                    <p className="text-[10px] text-[#6E6987]">{new Date(f.created_at).toLocaleDateString('ro-RO')}</p>
                                </div>
                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                    f.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                                }`}>
                                    {f.status === 'completed' ? (isRomanian ? 'Finalizat' : 'Completed') : (isRomanian ? 'In asteptare' : 'Pending')}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Leaderboard */}
            {leaderboard.length > 0 && (
                <div className="rounded-2xl overflow-hidden" style={{
                    background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                    border: '1px solid rgba(139,92,246,0.1)'
                }}>
                    <div className="p-4 border-b border-white/[0.06]">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <Crown className="w-4 h-4 text-amber-400" /> {isRomanian ? 'Top Invitatii' : 'Top Referrers'}
                        </h3>
                    </div>
                    <div className="divide-y divide-white/[0.04]">
                        {leaderboard.slice(0, 10).map((entry, i) => (
                            <div key={i} className="flex items-center gap-3 p-3">
                                <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
                                    i === 0 ? 'bg-amber-500/20 text-amber-400' :
                                    i === 1 ? 'bg-gray-400/20 text-gray-300' :
                                    i === 2 ? 'bg-orange-500/20 text-orange-400' :
                                    'bg-white/[0.04] text-[#6E6987]'
                                }`}>{entry.rank}</span>
                                <div className="flex-1">
                                    <p className="text-sm text-white font-medium">{entry.username}</p>
                                </div>
                                <span className="text-sm font-bold text-[#A666FF]">{entry.referrals} {isRomanian ? 'ref' : 'refs'}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default DashboardPage;
