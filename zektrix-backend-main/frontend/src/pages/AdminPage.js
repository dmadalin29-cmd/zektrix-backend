import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';
import { 
    AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line
} from 'recharts';
import { 
    Shield, LayoutDashboard, Trophy, Users, Ticket, Plus, Edit, Trash2, 
    Loader2, Zap, Clock, Search, DollarSign, Award, CheckCircle,
    XCircle, User, RefreshCw, BarChart3, Settings, Wifi, WifiOff, 
    Wand2, MessageCircle, Mail, TrendingUp, Menu, X, ChevronRight,
    ArrowUpRight, ArrowDownRight, Eye, Calendar, Target, Sparkles,
    Activity, CreditCard, ShoppingCart, Bell, Moon, Sun, ChevronDown,
    PieChart as PieIcon, Layers, Hash, Gift, Crown, Flame, Star
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// ============== ANIMATED COMPONENTS ==============

// Animated Counter with easing
const AnimatedNumber = ({ value, prefix = '', suffix = '', decimals = 0 }) => {
    const [display, setDisplay] = useState(0);
    useEffect(() => {
        const duration = 1500;
        const steps = 60;
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

// Sparkline Chart
const Sparkline = ({ data, color, height = 32 }) => (
    <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.map((v, i) => ({ v, i }))}>
                <defs>
                    <linearGradient id={`spark-${color}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={color} stopOpacity={0.4}/>
                        <stop offset="100%" stopColor={color} stopOpacity={0}/>
                    </linearGradient>
                </defs>
                <Area type="monotone" dataKey="v" stroke={color} strokeWidth={2} fill={`url(#spark-${color})`} />
            </AreaChart>
        </ResponsiveContainer>
    </div>
);

// Premium Stat Card
const StatCard = ({ icon: Icon, label, value, change, changeType, gradient, sparkData, loading, onClick }) => (
    <div 
        onClick={onClick}
        className={`group relative rounded-2xl p-5 cursor-pointer transition-all duration-500 hover:scale-[1.02] ${onClick ? 'hover:ring-2 hover:ring-violet-500/50' : ''}`}
        style={{
            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
            border: '1px solid rgba(139, 92, 246, 0.15)',
            boxShadow: '0 4px 24px rgba(0, 0, 0, 0.3)'
        }}
    >
        {/* Glow effect on hover */}
        <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"
            style={{ background: `radial-gradient(circle at 50% 50%, ${gradient?.split(' ')[0] || 'rgba(139,92,246,0.15)'}, transparent 70%)` }} />
        
        {loading ? (
            <div className="space-y-3 relative z-10">
                <div className="h-12 w-12 rounded-xl bg-white/5 animate-pulse" />
                <div className="h-4 w-24 bg-white/5 rounded animate-pulse" />
                <div className="h-8 w-32 bg-white/5 rounded animate-pulse" />
            </div>
        ) : (
            <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`}
                        style={{ background: gradient || 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}>
                        <Icon className="w-6 h-6 text-white" />
                    </div>
                    {change !== undefined && (
                        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold ${changeType === 'up' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                            {changeType === 'up' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                            {change}%
                        </div>
                    )}
                </div>
                <p className="text-sm text-gray-400 mb-1 font-medium">{label}</p>
                <p className="text-3xl font-bold text-white tracking-tight">
                    <AnimatedNumber value={typeof value === 'number' ? value : parseFloat(value) || 0} prefix={label.toLowerCase().includes('venit') ? 'RON ' : ''} />
                </p>
                {sparkData && (
                    <div className="mt-4 -mx-1">
                        <Sparkline data={sparkData} color={gradient?.includes('emerald') ? '#10b981' : gradient?.includes('orange') ? '#f97316' : '#8b5cf6'} />
                    </div>
                )}
            </div>
        )}
    </div>
);

// Sidebar Navigation Item
const NavItem = ({ icon: Icon, label, active, onClick, badge, collapsed }) => (
    <button
        onClick={onClick}
        data-testid={`nav-${label.toLowerCase().replace(/\s+/g, '-')}`}
        className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-300 group relative overflow-hidden
            ${active 
                ? 'text-white' 
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
        style={active ? {
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(124, 58, 237, 0.2) 100%)',
            boxShadow: '0 0 20px rgba(139, 92, 246, 0.3), inset 0 0 20px rgba(139, 92, 246, 0.1)'
        } : {}}
    >
        {/* Active indicator line */}
        {active && <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-violet-500 rounded-r-full" />}
        
        <Icon className={`w-5 h-5 transition-transform duration-300 ${active ? 'text-violet-400' : ''} group-hover:scale-110`} />
        {!collapsed && (
            <>
                <span className="flex-1 text-left">{label}</span>
                {badge !== undefined && badge > 0 && (
                    <span className="px-2 py-0.5 bg-violet-500/30 text-violet-300 text-xs font-bold rounded-full min-w-[24px] text-center">
                        {badge > 99 ? '99+' : badge}
                    </span>
                )}
            </>
        )}
    </button>
);

// Table Skeleton
const TableSkeleton = ({ rows = 5 }) => (
    <div className="space-y-3">
        {[...Array(rows)].map((_, i) => (
            <div key={i} className="h-16 bg-white/5 rounded-xl animate-pulse" style={{ animationDelay: `${i * 100}ms` }} />
        ))}
    </div>
);

// Empty State
const EmptyState = ({ icon: Icon, title, description }) => (
    <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-20 h-20 rounded-2xl bg-violet-500/10 flex items-center justify-center mb-4">
            <Icon className="w-10 h-10 text-violet-400" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
        <p className="text-gray-500 max-w-md">{description}</p>
    </div>
);

// Custom Chart Tooltip
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-[#0a0614]/95 backdrop-blur-xl border border-violet-500/30 rounded-xl p-3 shadow-2xl">
                <p className="text-xs text-gray-400 mb-1">{label}</p>
                <p className="text-lg font-bold text-white">{payload[0].value?.toLocaleString('ro-RO')}</p>
            </div>
        );
    }
    return null;
};

// ============== MAIN COMPONENT ==============

const AdminPage = () => {
    const { user, token, isAdmin } = useAuth();
    const { isRomanian } = useLanguage();
    const navigate = useNavigate();

    // State
    const [tab, setTab] = useState('dashboard');
    const [loading, setLoading] = useState(true);
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [stats, setStats] = useState(null);
    const [comps, setComps] = useState([]);
    const [users, setUsers] = useState([]);
    const [tickets, setTickets] = useState([]);
    const [winners, setWinners] = useState([]);
    const [chatMsgs, setChatMsgs] = useState([]);
    const [liveStatus, setLiveStatus] = useState({ isLive: false, message: '' });

    // Modals
    const [showCompModal, setShowCompModal] = useState(false);
    const [showUserModal, setShowUserModal] = useState(false);
    const [editingComp, setEditingComp] = useState(null);
    const [editingUser, setEditingUser] = useState(null);

    // Forms
    const [compForm, setCompForm] = useState({
        title: '', description: '', ticket_price: '', max_tickets: '', 
        competition_type: 'instant_win', image_url: '', prize_description: '', category: 'general',
        qual_question: '', qual_option1: '', qual_option2: '', qual_correct: '0'
    });
    const [userForm, setUserForm] = useState({ first_name: '', last_name: '', email: '', phone: '', balance: '', new_password: '', role: '' });
    const [ticketSearch, setTicketSearch] = useState('');
    const [ticketCompFilter, setTicketCompFilter] = useState('all');
    const [genAI, setGenAI] = useState(false);

    // Fetch all data
    const fetchAll = useCallback(async () => {
        setLoading(true);
        try {
            const [statsRes, compsRes, usersRes, ticketsRes, winnersRes] = await Promise.all([
                axios.get(`${API}/admin/stats`, { headers: { Authorization: `Bearer ${token}` }}).catch(() => ({ data: {} })),
                axios.get(`${API}/competitions`).catch(() => ({ data: [] })),
                axios.get(`${API}/admin/users`, { headers: { Authorization: `Bearer ${token}` }}).catch(() => ({ data: [] })),
                axios.get(`${API}/admin/tickets`, { headers: { Authorization: `Bearer ${token}` }}).catch(() => ({ data: [] })),
                axios.get(`${API}/winners`).catch(() => ({ data: [] }))
            ]);
            setStats(statsRes.data);
            setComps(compsRes.data);
            setUsers(usersRes.data);
            setTickets(ticketsRes.data);
            setWinners(winnersRes.data);
        } catch (e) { console.error(e); }
        setLoading(false);
    }, [token]);

    useEffect(() => {
        if (!isAdmin) { navigate('/dashboard'); return; }
        fetchAll();
        axios.get(`${API}/settings/tiktok-live`).then(r => setLiveStatus({ isLive: r.data.is_live, message: '', tiktok_url: r.data.tiktok_url })).catch(() => {});
        axios.get(`${API}/admin/chat/messages`, { headers: { Authorization: `Bearer ${token}` }}).then(r => setChatMsgs(r.data)).catch(() => {});
    }, [isAdmin, navigate, fetchAll, token]);

    // Mock chart data for beautiful visualizations
    const chartData = useMemo(() => {
        const days = ['Lun', 'Mar', 'Mie', 'Joi', 'Vin', 'Sâm', 'Dum'];
        return days.map((day, i) => ({
            name: day,
            vanzari: Math.floor(Math.random() * 500 + 200),
            utilizatori: Math.floor(Math.random() * 50 + 20),
            locuri: Math.floor(Math.random() * 300 + 100)
        }));
    }, []);

    const pieData = useMemo(() => [
        { name: 'Tech', value: 35, color: '#8b5cf6' },
        { name: 'Auto', value: 25, color: '#f97316' },
        { name: 'Travel', value: 20, color: '#06b6d4' },
        { name: 'Lifestyle', value: 20, color: '#10b981' }
    ], []);

    const sparkDataSales = useMemo(() => [30, 45, 35, 60, 75, 65, 80, 70, 90, 85, 95, 100], []);
    const sparkDataUsers = useMemo(() => [20, 30, 25, 40, 50, 45, 55, 50, 60, 55, 65, 70], []);
    const sparkDataTickets = useMemo(() => [40, 55, 45, 70, 85, 75, 90, 80, 100, 95, 105, 110], []);

    // AI Generate
    const generateAI = async () => {
        if (!compForm.title) { toast.error('Introdu titlul întâi'); return; }
        setGenAI(true);
        try {
            const r = await axios.post(`${API}/admin/generate-ai-content`, { title: compForm.title }, { headers: { Authorization: `Bearer ${token}` }});
            if (r.data.description) setCompForm(p => ({ ...p, description: r.data.description }));
            if (r.data.qualification_question) {
                const q = r.data.qualification_question;
                setCompForm(p => ({ ...p, qual_question: q.question || '', qual_option1: q.options?.[0] || '', qual_option2: q.options?.[1] || '', qual_correct: '0' }));
            }
            toast.success('✨ Generat cu AI!');
        } catch { toast.error('Eroare AI'); }
        setGenAI(false);
    };

    // Competition CRUD
    const saveComp = async (e) => {
        e.preventDefault();
        const data = {
            title: compForm.title, description: compForm.description,
            ticket_price: parseFloat(compForm.ticket_price), max_tickets: parseInt(compForm.max_tickets),
            competition_type: compForm.competition_type, image_url: compForm.image_url,
            prize_description: compForm.prize_description, category: compForm.category,
            qualification_question: compForm.qual_question ? {
                question: compForm.qual_question,
                options: [compForm.qual_option1, compForm.qual_option2],
                correct_answer: parseInt(compForm.qual_correct)
            } : null
        };
        try {
            if (editingComp) {
                await axios.put(`${API}/admin/competitions/${editingComp.competition_id}`, data, { headers: { Authorization: `Bearer ${token}` }});
                toast.success('Competiție actualizată!');
            } else {
                await axios.post(`${API}/admin/competitions`, data, { headers: { Authorization: `Bearer ${token}` }});
                toast.success('Competiție creată!');
            }
            setShowCompModal(false); setEditingComp(null);
            setCompForm({ title: '', description: '', ticket_price: '', max_tickets: '', competition_type: 'instant_win', image_url: '', prize_description: '', category: 'general', qual_question: '', qual_option1: '', qual_option2: '', qual_correct: '0' });
            fetchAll();
        } catch (e) { toast.error(e.response?.data?.detail || 'Eroare'); }
    };

    const delComp = async (id) => {
        if (!window.confirm('Ștergi competiția?')) return;
        try { await axios.delete(`${API}/admin/competitions/${id}`, { headers: { Authorization: `Bearer ${token}` }}); toast.success('Șters!'); fetchAll(); } catch { toast.error('Eroare'); }
    };

    const editComp = (c) => {
        setEditingComp(c);
        setCompForm({
            title: c.title, description: c.description, ticket_price: c.ticket_price.toString(),
            max_tickets: c.max_tickets.toString(), competition_type: c.competition_type,
            image_url: c.image_url || '', prize_description: c.prize_description || '', category: c.category || 'general',
            qual_question: c.qualification_question?.question || '',
            qual_option1: c.qualification_question?.options?.[0] || '',
            qual_option2: c.qualification_question?.options?.[1] || '',
            qual_correct: (c.qualification_question?.correct_answer || 0).toString()
        });
        setShowCompModal(true);
    };

    // User CRUD
    const saveUser = async (e) => {
        e.preventDefault();
        const data = {};
        if (userForm.first_name) data.first_name = userForm.first_name;
        if (userForm.last_name) data.last_name = userForm.last_name;
        if (userForm.email) data.email = userForm.email;
        if (userForm.phone) data.phone = userForm.phone;
        if (userForm.balance) data.balance = parseFloat(userForm.balance);
        if (userForm.new_password) data.new_password = userForm.new_password;
        if (userForm.role) data.role = userForm.role;
        try {
            await axios.put(`${API}/admin/users/${editingUser.user_id}`, data, { headers: { Authorization: `Bearer ${token}` }});
            toast.success('Utilizator actualizat!'); setShowUserModal(false); fetchAll();
        } catch (e) { toast.error(e.response?.data?.detail || 'Eroare'); }
    };

    const blockUser = async (u) => {
        if (!window.confirm(`${u.is_blocked ? 'Deblochezi' : 'Blochezi'} ${u.username}?`)) return;
        try { await axios.put(`${API}/admin/users/${u.user_id}`, { is_blocked: !u.is_blocked }, { headers: { Authorization: `Bearer ${token}` }}); toast.success(u.is_blocked ? 'Deblocat!' : 'Blocat!'); fetchAll(); } catch { toast.error('Eroare'); }
    };

    const delUser = async (u) => {
        if (!window.confirm(`Ștergi permanent ${u.username}?`)) return;
        try { await axios.delete(`${API}/admin/users/${u.user_id}`, { headers: { Authorization: `Bearer ${token}` }}); toast.success('Șters!'); fetchAll(); } catch { toast.error('Eroare'); }
    };

    const editUser = (u) => {
        setEditingUser(u);
        setUserForm({ first_name: u.first_name || '', last_name: u.last_name || '', email: u.email || '', phone: u.phone || '', balance: (u.balance || 0).toString(), new_password: '', role: u.role || 'user' });
        setShowUserModal(true);
    };

    const toggleLive = async () => {
        try { await axios.post(`${API}/admin/settings/tiktok-live?is_live=${!liveStatus.isLive}`, {}, { headers: { Authorization: `Bearer ${token}` }}); setLiveStatus(p => ({ ...p, isLive: !p.isLive })); toast.success(!liveStatus.isLive ? '🔴 LIVE!' : 'Oprit'); } catch { toast.error('Eroare'); }
    };

    const endComp = async (c) => {
        const ticketNum = window.prompt(`Numărul locului câștigător pentru "${c.title}":`);
        if (!ticketNum) return;
        try { await axios.post(`${API}/admin/competitions/${c.competition_id}/end`, { winning_ticket: parseInt(ticketNum) }, { headers: { Authorization: `Bearer ${token}` }}); toast.success('Premiant anunțat!'); fetchAll(); } catch (e) { toast.error(e.response?.data?.detail || 'Eroare'); }
    };

    const filteredTickets = tickets.filter(t => {
        // Filter by competition
        if (ticketCompFilter !== 'all' && t.competition_id !== ticketCompFilter) return false;
        // Filter by search (username, email, full_name, or ticket number)
        if (ticketSearch) {
            const searchTrimmed = ticketSearch.trim();
            // If search is purely numeric, search ONLY by ticket number
            if (/^\d+$/.test(searchTrimmed)) {
                const searchNum = parseInt(searchTrimmed);
                if (t.ticket_number !== searchNum) return false;
            } else {
                // Otherwise search by user info
                const searchLower = searchTrimmed.toLowerCase();
                const matchesUser = t.username?.toLowerCase().includes(searchLower) || 
                                   t.email?.toLowerCase().includes(searchLower) || 
                                   t.full_name?.toLowerCase().includes(searchLower);
                if (!matchesUser) return false;
            }
        }
        return true;
    });

    const sidebarItems = [
        { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { id: 'comps', icon: Trophy, label: 'Competiții', badge: comps.length },
        { id: 'users', icon: Users, label: 'Utilizatori', badge: users.length },
        { id: 'tickets', icon: Ticket, label: 'Locuri', badge: tickets.length },
        { id: 'winners', icon: Crown, label: 'Premianți', badge: winners.length },
        { id: 'analytics', icon: BarChart3, label: 'Analitics' },
        { id: 'settings', icon: Settings, label: 'Setări' },
        { id: 'chat', icon: MessageCircle, label: 'Chat', badge: chatMsgs.length },
    ];

    return (
        <div className="min-h-screen bg-[#030014] flex" data-testid="admin-page">
            {/* ============== SIDEBAR ============== */}
            <aside 
                className={`fixed lg:sticky top-0 left-0 z-50 h-screen transition-all duration-500 ease-out
                    ${sidebarCollapsed ? 'w-20' : 'w-72'} 
                    ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
                style={{
                    background: 'linear-gradient(180deg, rgba(10, 6, 20, 0.98) 0%, rgba(5, 3, 15, 0.99) 100%)',
                    borderRight: '1px solid rgba(139, 92, 246, 0.1)',
                    boxShadow: '4px 0 24px rgba(0, 0, 0, 0.5)'
                }}
            >
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="p-4 border-b border-white/5">
                        <Link to="/" className="flex items-center gap-3 group">
                            <div className="w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-300 group-hover:scale-110"
                                style={{ background: 'linear-gradient(135deg, #8b5cf6 0%, #f97316 100%)', boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)' }}>
                                <Shield className="w-6 h-6 text-white" />
                            </div>
                            {!sidebarCollapsed && (
                                <div className="overflow-hidden">
                                    <h1 className="font-bold text-white text-lg tracking-tight">Zektrix</h1>
                                    <p className="text-xs text-violet-400 font-medium">Admin Panel</p>
                                </div>
                            )}
                        </Link>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                        {sidebarItems.map(item => (
                            <NavItem 
                                key={item.id} 
                                {...item} 
                                active={tab === item.id} 
                                onClick={() => { setTab(item.id); setMobileMenuOpen(false); }}
                                collapsed={sidebarCollapsed}
                            />
                        ))}
                    </nav>

                    {/* LIVE Status Toggle */}
                    <div className="p-3 border-t border-white/5">
                        <button
                            onClick={toggleLive}
                            data-testid="live-toggle"
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${liveStatus.isLive ? 'bg-red-500/20' : 'bg-white/5 hover:bg-white/10'}`}
                        >
                            {liveStatus.isLive ? (
                                <Wifi className="w-5 h-5 text-red-400 animate-pulse" />
                            ) : (
                                <WifiOff className="w-5 h-5 text-gray-500" />
                            )}
                            {!sidebarCollapsed && (
                                <span className={`text-sm font-medium ${liveStatus.isLive ? 'text-red-400' : 'text-gray-400'}`}>
                                    {liveStatus.isLive ? 'LIVE ACUM' : 'Offline'}
                                </span>
                            )}
                            {liveStatus.isLive && <span className="ml-auto w-2 h-2 bg-red-500 rounded-full animate-ping" />}
                        </button>
                    </div>

                    {/* User Profile */}
                    <div className="p-3 border-t border-white/5">
                        <div className="flex items-center gap-3 px-3 py-2">
                            <div className="w-10 h-10 rounded-full flex items-center justify-center"
                                style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(249, 115, 22, 0.3))' }}>
                                <User className="w-5 h-5 text-violet-300" />
                            </div>
                            {!sidebarCollapsed && (
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-white truncate">{user?.username}</p>
                                    <p className="text-xs text-gray-500">Administrator</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Collapse Toggle */}
                    <button
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                        className="hidden lg:flex absolute -right-3 top-20 w-6 h-6 bg-violet-600 rounded-full items-center justify-center shadow-lg hover:bg-violet-500 transition-colors"
                    >
                        <ChevronRight className={`w-4 h-4 text-white transition-transform duration-300 ${sidebarCollapsed ? '' : 'rotate-180'}`} />
                    </button>
                </div>
            </aside>

            {/* Mobile Overlay */}
            {mobileMenuOpen && <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden" onClick={() => setMobileMenuOpen(false)} />}

            {/* ============== MAIN CONTENT ============== */}
            <main className="flex-1 min-w-0 lg:ml-0">
                {/* Header */}
                <header className="sticky top-0 z-30 backdrop-blur-xl border-b border-white/5"
                    style={{ background: 'rgba(3, 0, 20, 0.8)' }}>
                    <div className="flex items-center justify-between px-4 lg:px-6 py-4">
                        <div className="flex items-center gap-4">
                            <button 
                                onClick={() => setMobileMenuOpen(!mobileMenuOpen)} 
                                className="lg:hidden p-2 rounded-xl hover:bg-white/5 transition-colors"
                                data-testid="mobile-menu-btn"
                            >
                                <Menu className="w-6 h-6 text-gray-400" />
                            </button>
                            <div>
                                <h1 className="text-xl lg:text-2xl font-bold text-white capitalize tracking-tight">
                                    {tab === 'comps' ? 'Competiții' : tab === 'analytics' ? 'Analytics' : tab}
                                </h1>
                                <p className="text-xs lg:text-sm text-gray-500">
                                    {new Date().toLocaleDateString('ro-RO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 lg:gap-3">
                            <Button 
                                variant="ghost" 
                                size="sm" 
                                onClick={fetchAll} 
                                className="text-gray-400 hover:text-white hover:bg-white/5"
                                data-testid="refresh-btn"
                            >
                                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            </Button>
                            <Button variant="ghost" size="sm" className="relative text-gray-400 hover:text-white hover:bg-white/5">
                                <Bell className="w-4 h-4" />
                                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-violet-500 rounded-full" />
                            </Button>
                        </div>
                    </div>
                </header>

                {/* Content Container */}
                <div className="p-4 lg:p-6">
                    
                    {/* ============== DASHBOARD TAB ============== */}
                    {tab === 'dashboard' && (
                        <div className="space-y-6">
                            {/* Main Stats Grid */}
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
                                <StatCard 
                                    icon={Trophy} 
                                    label="Competiții Active" 
                                    value={stats?.active_competitions || 0} 
                                    change={12} 
                                    changeType="up" 
                                    gradient="linear-gradient(135deg, #8b5cf6, #7c3aed)" 
                                    sparkData={sparkDataSales}
                                    loading={loading}
                                    onClick={() => setTab('comps')}
                                />
                                <StatCard 
                                    icon={Users} 
                                    label="Total Utilizatori" 
                                    value={stats?.total_users || 0} 
                                    change={8} 
                                    changeType="up" 
                                    gradient="linear-gradient(135deg, #06b6d4, #0891b2)" 
                                    sparkData={sparkDataUsers}
                                    loading={loading}
                                    onClick={() => setTab('users')}
                                />
                                <StatCard 
                                    icon={Ticket} 
                                    label="Locuri Vândute" 
                                    value={stats?.total_tickets || 0} 
                                    change={24} 
                                    changeType="up" 
                                    gradient="linear-gradient(135deg, #10b981, #059669)" 
                                    sparkData={sparkDataTickets}
                                    loading={loading}
                                    onClick={() => setTab('tickets')}
                                />
                                <StatCard 
                                    icon={DollarSign} 
                                    label="Venit Total (RON)" 
                                    value={stats?.total_revenue || 0} 
                                    change={18} 
                                    changeType="up" 
                                    gradient="linear-gradient(135deg, #f97316, #ea580c)" 
                                    loading={loading}
                                />
                            </div>

                            {/* Charts Row */}
                            <div className="grid lg:grid-cols-3 gap-4 lg:gap-6">
                                {/* Main Area Chart */}
                                <div className="lg:col-span-2 rounded-2xl p-5 lg:p-6"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                        border: '1px solid rgba(139, 92, 246, 0.15)'
                                    }}>
                                    <div className="flex items-center justify-between mb-6">
                                        <div>
                                            <h3 className="text-lg font-bold text-white">Vânzări Săptămânale</h3>
                                            <p className="text-sm text-gray-500">Ultima săptămână</p>
                                        </div>
                                        <div className="flex items-center gap-4 text-xs">
                                            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-violet-500" /> Vânzări</span>
                                            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-cyan-500" /> Utilizatori</span>
                                        </div>
                                    </div>
                                    <div className="h-64 lg:h-72">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={chartData}>
                                                <defs>
                                                    <linearGradient id="colorVanzari" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                                                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                                                    </linearGradient>
                                                    <linearGradient id="colorUtilizatori" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                                                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                                                <YAxis stroke="#6b7280" fontSize={12} />
                                                <Tooltip content={<CustomTooltip />} />
                                                <Area type="monotone" dataKey="vanzari" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorVanzari)" />
                                                <Area type="monotone" dataKey="utilizatori" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#colorUtilizatori)" />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* Pie Chart */}
                                <div className="rounded-2xl p-5 lg:p-6"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                        border: '1px solid rgba(139, 92, 246, 0.15)'
                                    }}>
                                    <h3 className="text-lg font-bold text-white mb-2">Categorii</h3>
                                    <p className="text-sm text-gray-500 mb-4">Distribuție competiții</p>
                                    <div className="h-48">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie
                                                    data={pieData}
                                                    cx="50%"
                                                    cy="50%"
                                                    innerRadius={50}
                                                    outerRadius={70}
                                                    paddingAngle={4}
                                                    dataKey="value"
                                                >
                                                    {pieData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                                    ))}
                                                </Pie>
                                                <Tooltip content={<CustomTooltip />} />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 mt-4">
                                        {pieData.map((item, i) => (
                                            <div key={i} className="flex items-center gap-2">
                                                <span className="w-3 h-3 rounded-full" style={{ background: item.color }} />
                                                <span className="text-xs text-gray-400">{item.name}</span>
                                                <span className="text-xs font-bold text-white ml-auto">{item.value}%</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Recent Activity Grid */}
                            <div className="grid lg:grid-cols-2 gap-4 lg:gap-6">
                                {/* Recent Competitions */}
                                <div className="rounded-2xl p-5 lg:p-6"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                        border: '1px solid rgba(139, 92, 246, 0.15)'
                                    }}>
                                    <div className="flex items-center justify-between mb-5">
                                        <h3 className="font-bold text-white flex items-center gap-2">
                                            <Trophy className="w-5 h-5 text-violet-400" /> Competiții Recente
                                        </h3>
                                        <Button variant="ghost" size="sm" onClick={() => setTab('comps')} className="text-violet-400 hover:text-violet-300 text-xs">
                                            Vezi toate <ChevronRight className="w-4 h-4 ml-1" />
                                        </Button>
                                    </div>
                                    <div className="space-y-3">
                                        {loading ? <TableSkeleton rows={4} /> : comps.slice(0, 4).map(c => {
                                            const pct = Math.round((c.sold_tickets / c.max_tickets) * 100);
                                            return (
                                                <div key={c.competition_id} 
                                                    className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all duration-300 cursor-pointer group" 
                                                    onClick={() => editComp(c)}
                                                >
                                                    <img src={c.image_url || 'https://images.unsplash.com/photo-1557683316-973673baf926?w=100'} alt="" className="w-12 h-12 rounded-lg object-cover" />
                                                    <div className="flex-1 min-w-0">
                                                        <p className="font-medium text-white truncate text-sm">{c.title}</p>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                                <div className="h-full rounded-full transition-all duration-500" 
                                                                    style={{ 
                                                                        width: `${pct}%`, 
                                                                        background: pct > 75 ? 'linear-gradient(90deg, #ef4444, #f97316)' : 'linear-gradient(90deg, #8b5cf6, #06b6d4)' 
                                                                    }} />
                                                            </div>
                                                            <span className="text-xs font-bold text-gray-400">{pct}%</span>
                                                        </div>
                                                    </div>
                                                    <div className="text-right opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <Edit className="w-4 h-4 text-violet-400" />
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* Recent Users */}
                                <div className="rounded-2xl p-5 lg:p-6"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                        border: '1px solid rgba(139, 92, 246, 0.15)'
                                    }}>
                                    <div className="flex items-center justify-between mb-5">
                                        <h3 className="font-bold text-white flex items-center gap-2">
                                            <Users className="w-5 h-5 text-cyan-400" /> Utilizatori Recenți
                                        </h3>
                                        <Button variant="ghost" size="sm" onClick={() => setTab('users')} className="text-violet-400 hover:text-violet-300 text-xs">
                                            Vezi toți <ChevronRight className="w-4 h-4 ml-1" />
                                        </Button>
                                    </div>
                                    <div className="space-y-3">
                                        {loading ? <TableSkeleton rows={4} /> : users.slice(0, 4).map(u => (
                                            <div key={u.user_id} 
                                                className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all duration-300 cursor-pointer" 
                                                onClick={() => editUser(u)}
                                            >
                                                <div className="w-10 h-10 rounded-full flex items-center justify-center"
                                                    style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(6, 182, 212, 0.3))' }}>
                                                    <User className="w-5 h-5 text-violet-300" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="font-medium text-white truncate text-sm">{u.first_name || u.username} {u.last_name || ''}</p>
                                                    <p className="text-xs text-gray-500 truncate">{u.email}</p>
                                                </div>
                                                <Badge className={`text-xs ${u.is_blocked ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                                                    {u.is_blocked ? 'Blocat' : 'Activ'}
                                                </Badge>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Quick Stats Row */}
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
                                <StatCard icon={Crown} label="Premianți" value={stats?.total_winners || 0} gradient="linear-gradient(135deg, #fbbf24, #f59e0b)" loading={loading} onClick={() => setTab('winners')} />
                                <StatCard icon={Activity} label="Tranzacții" value={stats?.total_transactions || 0} gradient="linear-gradient(135deg, #ec4899, #db2777)" loading={loading} />
                                <StatCard icon={Target} label="Conversie %" value={75} gradient="linear-gradient(135deg, #14b8a6, #0d9488)" loading={loading} />
                                <StatCard icon={Flame} label="Flash Sales" value={comps.filter(c => c.is_flash_sale).length} gradient="linear-gradient(135deg, #ef4444, #dc2626)" loading={loading} />
                            </div>
                        </div>
                    )}

                    {/* ============== COMPETITIONS TAB ============== */}
                    {tab === 'comps' && (
                        <div className="space-y-4">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                                <div className="flex items-center gap-3">
                                    <Badge className="bg-violet-500/20 text-violet-400 px-3 py-1.5">{comps.length} Competiții</Badge>
                                    <Badge className="bg-emerald-500/20 text-emerald-400 px-3 py-1.5">{comps.filter(c => c.status === 'active').length} Active</Badge>
                                </div>
                                <Button 
                                    onClick={() => { setEditingComp(null); setCompForm({ title: '', description: '', ticket_price: '', max_tickets: '', competition_type: 'instant_win', image_url: '', prize_description: '', category: 'general', qual_question: '', qual_option1: '', qual_option2: '', qual_correct: '0' }); setShowCompModal(true); }} 
                                    className="bg-violet-600 hover:bg-violet-500 shadow-lg shadow-violet-500/25"
                                    data-testid="add-competition-btn"
                                >
                                    <Plus className="w-4 h-4 mr-2" /> Adaugă Competiție
                                </Button>
                            </div>
                            <div className="space-y-3">
                                {loading ? <TableSkeleton rows={6} /> : comps.length === 0 ? (
                                    <EmptyState icon={Trophy} title="Nicio competiție" description="Adaugă prima ta competiție pentru a începe!" />
                                ) : comps.map(c => {
                                    const pct = Math.round((c.sold_tickets / c.max_tickets) * 100);
                                    return (
                                        <div key={c.competition_id} 
                                            className="group rounded-2xl p-4 lg:p-5 transition-all duration-300 hover:scale-[1.01]"
                                            style={{
                                                background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                                border: '1px solid rgba(139, 92, 246, 0.15)'
                                            }}
                                        >
                                            <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                                                <img src={c.image_url || 'https://images.unsplash.com/photo-1557683316-973673baf926?w=200'} alt="" className="w-full lg:w-24 h-32 lg:h-24 rounded-xl object-cover" />
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex flex-wrap items-center gap-2 mb-2">
                                                        <h3 className="font-bold text-white text-lg">{c.title}</h3>
                                                        <Badge className={c.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-500/20 text-gray-400'}>{c.status}</Badge>
                                                        {c.is_flash_sale && <Badge className="bg-orange-500/20 text-orange-400"><Zap className="w-3 h-3 mr-1" />Flash</Badge>}
                                                    </div>
                                                    <p className="text-sm text-gray-500 mb-3">{c.category} • {c.sold_tickets}/{c.max_tickets} locuri</p>
                                                    <div className="flex items-center gap-3">
                                                        <div className="flex-1 h-2.5 bg-white/10 rounded-full overflow-hidden">
                                                            <div className="h-full rounded-full transition-all duration-700" 
                                                                style={{ 
                                                                    width: `${pct}%`, 
                                                                    background: pct > 75 ? 'linear-gradient(90deg, #ef4444, #f97316, #fbbf24)' : 'linear-gradient(90deg, #8b5cf6, #06b6d4)',
                                                                    boxShadow: pct > 75 ? '0 0 10px rgba(239, 68, 68, 0.5)' : '0 0 10px rgba(139, 92, 246, 0.5)'
                                                                }} />
                                                        </div>
                                                        <span className={`text-sm font-bold ${pct > 75 ? 'text-orange-400' : 'text-violet-400'}`}>{pct}%</span>
                                                    </div>
                                                </div>
                                                <div className="flex lg:flex-col items-center lg:items-end gap-3">
                                                    <div className="text-left lg:text-right">
                                                        <p className="text-2xl font-bold text-white">RON {c.ticket_price}</p>
                                                        <p className="text-xs text-gray-500">per loc</p>
                                                    </div>
                                                    <div className="flex gap-2 ml-auto lg:ml-0">
                                                        <Button variant="ghost" size="sm" onClick={() => editComp(c)} className="hover:bg-violet-500/20 text-violet-400"><Edit className="w-4 h-4" /></Button>
                                                        {c.status === 'active' && <Button variant="ghost" size="sm" onClick={() => endComp(c)} className="hover:bg-yellow-500/20 text-yellow-400"><Crown className="w-4 h-4" /></Button>}
                                                        <Button variant="ghost" size="sm" onClick={() => delComp(c.competition_id)} className="hover:bg-red-500/20 text-red-400"><Trash2 className="w-4 h-4" /></Button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* ============== USERS TAB ============== */}
                    {tab === 'users' && (
                        <div className="space-y-4">
                            <div className="flex items-center gap-3 mb-4">
                                <Badge className="bg-cyan-500/20 text-cyan-400 px-3 py-1.5">{users.length} Utilizatori</Badge>
                                <Badge className="bg-emerald-500/20 text-emerald-400 px-3 py-1.5">{users.filter(u => !u.is_blocked).length} Activi</Badge>
                                <Badge className="bg-red-500/20 text-red-400 px-3 py-1.5">{users.filter(u => u.is_blocked).length} Blocați</Badge>
                            </div>
                            <div className="space-y-3">
                                {loading ? <TableSkeleton rows={8} /> : users.length === 0 ? (
                                    <EmptyState icon={Users} title="Niciun utilizator" description="Utilizatorii vor apărea aici după înregistrare." />
                                ) : users.map(u => (
                                    <div key={u.user_id} 
                                        className={`group rounded-xl p-4 transition-all duration-300 hover:scale-[1.01] ${u.is_blocked ? 'opacity-60' : ''}`}
                                        style={{
                                            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                            border: `1px solid ${u.is_blocked ? 'rgba(239, 68, 68, 0.2)' : 'rgba(139, 92, 246, 0.15)'}`
                                        }}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-12 h-12 rounded-full flex items-center justify-center"
                                                style={{ background: u.is_blocked ? 'rgba(239, 68, 68, 0.2)' : 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(6, 182, 212, 0.3))' }}>
                                                <User className={`w-6 h-6 ${u.is_blocked ? 'text-red-400' : 'text-violet-300'}`} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="font-bold text-white">{u.first_name || ''} {u.last_name || ''} <span className="text-gray-500 font-normal">@{u.username}</span></p>
                                                <p className="text-sm text-gray-500">{u.email} {u.phone && `• ${u.phone}`}</p>
                                            </div>
                                            <div className="text-right mr-4 hidden sm:block">
                                                <p className="text-lg font-bold text-emerald-400">RON {(u.balance || 0).toFixed(2)}</p>
                                                <Badge className={`text-xs ${u.is_blocked ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                                                    {u.is_blocked ? <><XCircle className="w-3 h-3 mr-1" />Blocat</> : <><CheckCircle className="w-3 h-3 mr-1" />Activ</>}
                                                </Badge>
                                            </div>
                                            <div className="flex gap-1 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity">
                                                <Button variant="ghost" size="sm" onClick={() => editUser(u)} className="hover:bg-violet-500/20"><Edit className="w-4 h-4 text-violet-400" /></Button>
                                                {u.role !== 'admin' && (
                                                    <>
                                                        <Button variant="ghost" size="sm" onClick={() => blockUser(u)} className={u.is_blocked ? 'hover:bg-emerald-500/20 text-emerald-400' : 'hover:bg-yellow-500/20 text-yellow-400'}>
                                                            {u.is_blocked ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                                                        </Button>
                                                        <Button variant="ghost" size="sm" onClick={() => delUser(u)} className="hover:bg-red-500/20 text-red-400"><Trash2 className="w-4 h-4" /></Button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ============== TICKETS TAB ============== */}
                    {tab === 'tickets' && (
                        <div className="space-y-4">
                            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                                <Badge className="bg-emerald-500/20 text-emerald-400 px-3 py-1.5">{filteredTickets.length} / {tickets.length} Locuri</Badge>
                                
                                {/* Competition Filter Dropdown */}
                                <select
                                    value={ticketCompFilter}
                                    onChange={e => setTicketCompFilter(e.target.value)}
                                    className="px-4 py-2 rounded-xl bg-white/5 border border-violet-500/30 text-white focus:border-violet-500 focus:outline-none cursor-pointer"
                                    data-testid="ticket-comp-filter"
                                >
                                    <option value="all" className="bg-[#0a0515] text-white">🎯 Toate Competițiile</option>
                                    {comps.map(c => (
                                        <option key={c.competition_id} value={c.competition_id} className="bg-[#0a0515] text-white">
                                            {c.title} ({tickets.filter(t => t.competition_id === c.competition_id).length} locuri)
                                        </option>
                                    ))}
                                </select>
                                
                                <div className="relative flex-1 max-w-md">
                                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <Input 
                                        placeholder="Caută după nume, email sau număr loc..." 
                                        value={ticketSearch} 
                                        onChange={e => setTicketSearch(e.target.value)} 
                                        className="pl-12 bg-white/5 border-white/10 focus:border-violet-500"
                                        data-testid="ticket-search"
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                {loading ? <TableSkeleton rows={10} /> : filteredTickets.length === 0 ? (
                                    <EmptyState icon={Ticket} title="Niciun loc" description={ticketCompFilter !== 'all' ? "Nu există locuri pentru această competiție." : "Locurile vândute vor apărea aici."} />
                                ) : filteredTickets.slice(0, 50).map(t => (
                                    <div key={t.ticket_id} 
                                        className="rounded-xl p-4 transition-all duration-300 hover:bg-white/5"
                                        style={{
                                            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.8) 0%, rgba(10, 6, 20, 0.9) 100%)',
                                            border: '1px solid rgba(139, 92, 246, 0.1)'
                                        }}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-16 h-16 rounded-xl flex flex-col items-center justify-center font-mono font-bold"
                                                style={{ background: 'linear-gradient(135deg, #8b5cf6, #f97316)', boxShadow: '0 0 20px rgba(139, 92, 246, 0.3)' }}>
                                                <span className="text-xs text-white/70">LOC</span>
                                                <span className="text-xl text-white">#{t.ticket_number}</span>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="font-bold text-white text-lg">{t.competition_title || t.competition_id}</p>
                                                <p className="text-sm text-violet-400 font-medium">{t.full_name || t.username || 'Unknown'}</p>
                                                <p className="text-xs text-gray-500">{t.email || 'N/A'} • {t.phone || 'Fara telefon'}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-sm text-gray-400">{t.purchased_at ? new Date(t.purchased_at).toLocaleDateString('ro-RO') : 'N/A'}</p>
                                                <p className="text-xs text-gray-500">{t.purchased_at ? new Date(t.purchased_at).toLocaleTimeString('ro-RO', {hour: '2-digit', minute: '2-digit'}) : ''}</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ============== WINNERS TAB ============== */}
                    {tab === 'winners' && (
                        <div className="space-y-4">
                            <Badge className="bg-yellow-500/20 text-yellow-400 px-3 py-1.5">{winners.length} Premianți</Badge>
                            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {loading ? [...Array(6)].map((_, i) => <div key={i} className="h-48 bg-white/5 rounded-2xl animate-pulse" />) : winners.length === 0 ? (
                                    <div className="col-span-full">
                                        <EmptyState icon={Crown} title="Niciun premiant" description="Premiții vor apărea aici după extrageri." />
                                    </div>
                                ) : winners.map(w => (
                                    <div key={w.winner_id} 
                                        className="rounded-2xl p-6 transition-all duration-500 hover:scale-[1.02]"
                                        style={{
                                            background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(249, 115, 22, 0.1) 100%)',
                                            border: '1px solid rgba(251, 191, 36, 0.3)',
                                            boxShadow: '0 0 30px rgba(251, 191, 36, 0.1)'
                                        }}
                                    >
                                        <div className="flex items-center gap-4 mb-4">
                                            <div className="w-14 h-14 rounded-full flex items-center justify-center"
                                                style={{ background: 'linear-gradient(135deg, #fbbf24, #f59e0b)', boxShadow: '0 0 20px rgba(251, 191, 36, 0.4)' }}>
                                                <Crown className="w-7 h-7 text-white" />
                                            </div>
                                            <div>
                                                <p className="font-bold text-white text-lg">{w.username}</p>
                                                <p className="text-sm text-yellow-400 font-mono">Loc #{w.winning_ticket}</p>
                                            </div>
                                        </div>
                                        <p className="text-gray-400 mb-3">{w.competition_title}</p>
                                        <p className="text-xs text-gray-500 flex items-center gap-1"><Calendar className="w-3 h-3" />{new Date(w.won_at).toLocaleDateString('ro-RO')}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ============== ANALYTICS TAB ============== */}
                    {tab === 'analytics' && (
                        <div className="space-y-6">
                            <div className="grid lg:grid-cols-2 gap-6">
                                {/* Revenue Chart */}
                                <div className="rounded-2xl p-6"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                        border: '1px solid rgba(139, 92, 246, 0.15)'
                                    }}>
                                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                        <TrendingUp className="w-5 h-5 text-emerald-400" /> Venituri
                                    </h3>
                                    <div className="h-64">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={chartData}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                                                <YAxis stroke="#6b7280" fontSize={12} />
                                                <Tooltip content={<CustomTooltip />} />
                                                <Bar dataKey="vanzari" fill="url(#barGradient)" radius={[4, 4, 0, 0]} />
                                                <defs>
                                                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="0%" stopColor="#8b5cf6" />
                                                        <stop offset="100%" stopColor="#7c3aed" />
                                                    </linearGradient>
                                                </defs>
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>

                                {/* User Growth */}
                                <div className="rounded-2xl p-6"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                        border: '1px solid rgba(139, 92, 246, 0.15)'
                                    }}>
                                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                        <Users className="w-5 h-5 text-cyan-400" /> Creștere Utilizatori
                                    </h3>
                                    <div className="h-64">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={chartData}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                                                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                                                <YAxis stroke="#6b7280" fontSize={12} />
                                                <Tooltip content={<CustomTooltip />} />
                                                <Line type="monotone" dataKey="utilizatori" stroke="#06b6d4" strokeWidth={3} dot={{ fill: '#06b6d4', strokeWidth: 2 }} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            </div>

                            {/* Performance Metrics */}
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                <StatCard icon={Eye} label="Vizualizări" value={12453} change={15} changeType="up" gradient="linear-gradient(135deg, #8b5cf6, #7c3aed)" loading={loading} />
                                <StatCard icon={ShoppingCart} label="Comenzi" value={847} change={22} changeType="up" gradient="linear-gradient(135deg, #10b981, #059669)" loading={loading} />
                                <StatCard icon={CreditCard} label="Plăți Procesate" value={623} change={18} changeType="up" gradient="linear-gradient(135deg, #f97316, #ea580c)" loading={loading} />
                                <StatCard icon={Star} label="Rating Mediu" value={4.8} gradient="linear-gradient(135deg, #fbbf24, #f59e0b)" loading={loading} />
                            </div>
                        </div>
                    )}

                    {/* ============== SETTINGS TAB ============== */}
                    {tab === 'settings' && (
                        <div className="space-y-6 max-w-4xl">
                            {/* Live Status */}
                            <div className="rounded-2xl p-6"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                    border: '1px solid rgba(139, 92, 246, 0.15)'
                                }}>
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${liveStatus.isLive ? 'bg-red-500/20' : 'bg-gray-500/20'}`}>
                                            {liveStatus.isLive ? <Wifi className="w-7 h-7 text-red-500 animate-pulse" /> : <WifiOff className="w-7 h-7 text-gray-500" />}
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold text-white">TikTok LIVE</h3>
                                            <p className="text-sm text-gray-500">{liveStatus.isLive ? 'Ești live acum!' : 'Nu ești live'}</p>
                                        </div>
                                    </div>
                                    <Button 
                                        onClick={toggleLive} 
                                        size="lg" 
                                        className={liveStatus.isLive ? 'bg-red-600 hover:bg-red-500' : 'bg-violet-600 hover:bg-violet-500'}
                                        data-testid="toggle-live-btn"
                                    >
                                        {liveStatus.isLive ? 'Oprește LIVE' : 'Pornește LIVE'}
                                    </Button>
                                </div>
                                <div>
                                    <Label className="text-gray-400">Mesaj pentru utilizatori</Label>
                                    <div className="flex gap-2 mt-2">
                                        <Input value={liveStatus.message} onChange={e => setLiveStatus(p => ({ ...p, message: e.target.value }))} className="bg-white/5 border-white/10" placeholder="Ex: Suntem LIVE pe TikTok!" />
                                        <Button variant="outline" onClick={() => axios.put(`${API}/admin/live-status`, liveStatus, { headers: { Authorization: `Bearer ${token}` }}).then(() => toast.success('Salvat!'))}>Salvează</Button>
                                    </div>
                                </div>
                            </div>

                            {/* Email Bot */}
                            <div className="rounded-2xl p-6"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                    border: '1px solid rgba(139, 92, 246, 0.15)'
                                }}>
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="w-14 h-14 rounded-2xl bg-violet-500/20 flex items-center justify-center">
                                        <Mail className="w-7 h-7 text-violet-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-white">Bot Email Notificări</h3>
                                        <p className="text-sm text-gray-500">Trimite emailuri automate către utilizatori</p>
                                    </div>
                                </div>
                                <div className="grid md:grid-cols-2 gap-4">
                                    <div className="p-5 rounded-xl"
                                        style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1))', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
                                        <div className="flex items-center gap-2 mb-3">
                                            <Sparkles className="w-5 h-5 text-violet-400" />
                                            <h4 className="font-semibold text-white">Digest Zilnic</h4>
                                        </div>
                                        <p className="text-sm text-gray-400 mb-4">Trimite email cu competiții noi și aproape terminate.</p>
                                        <Button 
                                            onClick={() => axios.post(`${API}/admin/send-daily-digest`, {}, { headers: { Authorization: `Bearer ${token}` }}).then(r => toast.success(r.data.message)).catch(() => toast.error('Eroare'))} 
                                            className="w-full bg-violet-600 hover:bg-violet-500"
                                            data-testid="send-digest-btn"
                                        >
                                            Trimite Digest
                                        </Button>
                                    </div>
                                    <div className="p-5 rounded-xl"
                                        style={{ background: 'linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(234, 88, 12, 0.1))', border: '1px solid rgba(249, 115, 22, 0.2)' }}>
                                        <div className="flex items-center gap-2 mb-3">
                                            <Zap className="w-5 h-5 text-orange-400" />
                                            <h4 className="font-semibold text-white">Notificare 75%+</h4>
                                        </div>
                                        <p className="text-sm text-gray-400 mb-4">Trimite notificare când competiția depășește 75%.</p>
                                        <Select onValueChange={id => id && axios.post(`${API}/admin/notify-75-percent/${id}`, {}, { headers: { Authorization: `Bearer ${token}` }}).then(r => toast.success(r.data.message)).catch(() => toast.error('Eroare'))}>
                                            <SelectTrigger className="bg-white/5 border-white/10"><SelectValue placeholder="Alege competiția" /></SelectTrigger>
                                            <SelectContent>
                                                {comps.map(c => <SelectItem key={c.competition_id} value={c.competition_id}>{c.title} ({Math.round((c.sold_tickets/c.max_tickets)*100)}%)</SelectItem>)}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ============== CHAT TAB ============== */}
                    {tab === 'chat' && (
                        <div className="space-y-4">
                            <div className="flex items-center gap-3 mb-4">
                                <Badge className="bg-violet-500/20 text-violet-400 px-3 py-1.5">{chatMsgs.length} Mesaje</Badge>
                                <Badge className="bg-yellow-500/20 text-yellow-400 px-3 py-1.5">{chatMsgs.filter(m => m.status === 'pending').length} Nerezolvate</Badge>
                            </div>
                            <div className="space-y-3">
                                {chatMsgs.length === 0 ? (
                                    <EmptyState icon={MessageCircle} title="Niciun mesaj" description="Mesajele de la utilizatori vor apărea aici." />
                                ) : chatMsgs.map((m) => (
                                    <div key={m.message_id} 
                                        className={`rounded-2xl p-5 transition-all ${m.status === 'replied' ? 'opacity-70' : ''}`}
                                        style={{
                                            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                            border: m.status === 'pending' ? '1px solid rgba(251, 191, 36, 0.3)' : '1px solid rgba(139, 92, 246, 0.15)'
                                        }}
                                    >
                                        <div className="flex items-start gap-4">
                                            <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                                                style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(6, 182, 212, 0.3))' }}>
                                                <User className="w-6 h-6 text-violet-300" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <p className="font-bold text-white">{m.username}</p>
                                                    <Badge className={m.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-emerald-500/20 text-emerald-400'}>
                                                        {m.status === 'pending' ? 'Așteaptă răspuns' : 'Răspuns trimis'}
                                                    </Badge>
                                                </div>
                                                <p className="text-xs text-gray-500 mb-3">{new Date(m.created_at).toLocaleString('ro-RO')}</p>
                                                <div className="p-3 rounded-xl bg-white/5 mb-3">
                                                    <p className="text-gray-300">{m.message}</p>
                                                </div>
                                                {m.admin_reply && (
                                                    <div className="p-3 rounded-xl mb-3"
                                                        style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05))', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                                                        <p className="text-xs text-emerald-400 mb-1">Răspunsul tău:</p>
                                                        <p className="text-gray-300">{m.admin_reply}</p>
                                                    </div>
                                                )}
                                                {m.status === 'pending' && (
                                                    <div className="flex gap-2">
                                                        <Input 
                                                            id={`reply-${m.message_id}`}
                                                            placeholder="Scrie răspunsul..." 
                                                            className="bg-white/5 border-white/10 flex-1"
                                                        />
                                                        <Button 
                                                            onClick={async () => {
                                                                const input = document.getElementById(`reply-${m.message_id}`);
                                                                const reply = input?.value;
                                                                if (!reply) { toast.error('Scrie un răspuns'); return; }
                                                                try {
                                                                    await axios.post(`${API}/admin/chat/reply`, { message_id: m.message_id, reply }, { headers: { Authorization: `Bearer ${token}` }});
                                                                    toast.success('Răspuns trimis!');
                                                                    fetchAll();
                                                                } catch { toast.error('Eroare'); }
                                                            }}
                                                            className="bg-violet-600 hover:bg-violet-500"
                                                        >
                                                            Trimite
                                                        </Button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </main>

            {/* ============== COMPETITION MODAL ============== */}
            <Dialog open={showCompModal} onOpenChange={setShowCompModal}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto"
                    style={{ background: 'linear-gradient(135deg, rgba(10, 6, 20, 0.98) 0%, rgba(5, 3, 15, 0.99) 100%)', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
                    <DialogHeader>
                        <DialogTitle className="text-white text-xl">{editingComp ? 'Editează Competiția' : 'Competiție Nouă'}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={saveComp} className="space-y-4">
                        <div className="grid md:grid-cols-2 gap-4">
                            <div>
                                <Label className="text-gray-400">Titlu</Label>
                                <Input value={compForm.title} onChange={e => setCompForm(p => ({ ...p, title: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" required />
                            </div>
                            <div>
                                <Label className="text-gray-400">Categorie</Label>
                                <Select value={compForm.category} onValueChange={v => setCompForm(p => ({ ...p, category: v }))}>
                                    <SelectTrigger className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="general">General</SelectItem>
                                        <SelectItem value="tech">Tech</SelectItem>
                                        <SelectItem value="auto">Auto</SelectItem>
                                        <SelectItem value="travel">Travel</SelectItem>
                                        <SelectItem value="lifestyle">Lifestyle</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <Label className="text-gray-400">Descriere</Label>
                                <Button type="button" variant="ghost" size="sm" onClick={generateAI} disabled={genAI} className="text-violet-400 hover:text-violet-300">
                                    {genAI ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Wand2 className="w-4 h-4 mr-1" /> Generează cu AI</>}
                                </Button>
                            </div>
                            <Textarea value={compForm.description} onChange={e => setCompForm(p => ({ ...p, description: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" rows={3} />
                        </div>
                        <div className="grid md:grid-cols-3 gap-4">
                            <div>
                                <Label className="text-gray-400">Preț (RON)</Label>
                                <Input type="number" step="0.01" value={compForm.ticket_price} onChange={e => setCompForm(p => ({ ...p, ticket_price: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" required />
                            </div>
                            <div>
                                <Label className="text-gray-400">Max Locuri</Label>
                                <Input type="number" value={compForm.max_tickets} onChange={e => setCompForm(p => ({ ...p, max_tickets: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" required />
                            </div>
                            <div>
                                <Label className="text-gray-400">Tip</Label>
                                <Select value={compForm.competition_type} onValueChange={v => setCompForm(p => ({ ...p, competition_type: v }))}>
                                    <SelectTrigger className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="instant_win">Instant</SelectItem>
                                        <SelectItem value="draw">Extragere</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div>
                            <Label className="text-gray-400">URL Imagine</Label>
                            <Input value={compForm.image_url} onChange={e => setCompForm(p => ({ ...p, image_url: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" placeholder="https://..." />
                        </div>
                        <div>
                            <Label className="text-gray-400">Descriere Premiu</Label>
                            <Input value={compForm.prize_description} onChange={e => setCompForm(p => ({ ...p, prize_description: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" />
                        </div>
                        <div className="border-t border-white/10 pt-4">
                            <Label className="text-violet-400 mb-2 block font-semibold">Întrebare Calificare</Label>
                            <Input value={compForm.qual_question} onChange={e => setCompForm(p => ({ ...p, qual_question: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500 mb-2" placeholder="Întrebarea..." />
                            <div className="grid grid-cols-2 gap-2">
                                <Input value={compForm.qual_option1} onChange={e => setCompForm(p => ({ ...p, qual_option1: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" placeholder="Răspuns corect" />
                                <Input value={compForm.qual_option2} onChange={e => setCompForm(p => ({ ...p, qual_option2: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" placeholder="Răspuns greșit" />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={() => setShowCompModal(false)}>Anulează</Button>
                            <Button type="submit" className="bg-violet-600 hover:bg-violet-500">{editingComp ? 'Actualizează' : 'Creează'}</Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>

            {/* ============== USER MODAL ============== */}
            <Dialog open={showUserModal} onOpenChange={setShowUserModal}>
                <DialogContent className="max-w-md"
                    style={{ background: 'linear-gradient(135deg, rgba(10, 6, 20, 0.98) 0%, rgba(5, 3, 15, 0.99) 100%)', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
                    <DialogHeader>
                        <DialogTitle className="text-white">Editează: {editingUser?.username}</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={saveUser} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <Label className="text-gray-400">Prenume</Label>
                                <Input value={userForm.first_name} onChange={e => setUserForm(p => ({ ...p, first_name: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" />
                            </div>
                            <div>
                                <Label className="text-gray-400">Nume</Label>
                                <Input value={userForm.last_name} onChange={e => setUserForm(p => ({ ...p, last_name: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" />
                            </div>
                        </div>
                        <div>
                            <Label className="text-gray-400">Email</Label>
                            <Input type="email" value={userForm.email} onChange={e => setUserForm(p => ({ ...p, email: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" />
                        </div>
                        <div>
                            <Label className="text-gray-400">Telefon</Label>
                            <Input value={userForm.phone} onChange={e => setUserForm(p => ({ ...p, phone: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" />
                        </div>
                        <div>
                            <Label className="text-gray-400">Sold (RON)</Label>
                            <Input type="number" step="0.01" value={userForm.balance} onChange={e => setUserForm(p => ({ ...p, balance: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" />
                        </div>
                        <div>
                            <Label className="text-gray-400">Parolă Nouă</Label>
                            <Input type="password" value={userForm.new_password} onChange={e => setUserForm(p => ({ ...p, new_password: e.target.value }))} className="bg-white/5 border-white/10 focus:border-violet-500" placeholder="Lasă gol pentru a păstra" />
                        </div>
                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={() => setShowUserModal(false)}>Anulează</Button>
                            <Button type="submit" className="bg-violet-600 hover:bg-violet-500">Actualizează</Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default AdminPage;
