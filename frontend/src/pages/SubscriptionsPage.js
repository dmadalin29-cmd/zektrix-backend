import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useSearchParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';
import {
    Crown, Zap, Star, CheckCircle2, Clock, Ticket, Gift, Shield,
    CreditCard, Wallet, ArrowRight, Sparkles, XCircle, RefreshCw,
    CalendarDays, Layers, ChevronRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PLAN_FEATURES = {
    sub_25: { icon: Star, color: 'from-blue-500 to-cyan-500', accent: 'blue', tickets: 2, popular: false },
    sub_50: { icon: Crown, color: 'from-violet-500 to-purple-500', accent: 'violet', tickets: 5, popular: true },
    sub_100: { icon: Zap, color: 'from-amber-500 to-orange-500', accent: 'amber', tickets: 12, popular: false },
};

export default function SubscriptionsPage() {
    const { user, token, isAuthenticated } = useAuth();
    const { isRomanian } = useLanguage();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const headers = { Authorization: `Bearer ${token}` };

    const [plans, setPlans] = useState([]);
    const [mySub, setMySub] = useState(null);
    const [myTickets, setMyTickets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [purchasing, setPurchasing] = useState(null);
    const [walletBalance, setWalletBalance] = useState(0);
    const [showTickets, setShowTickets] = useState(false);
    const [cancelling, setCancelling] = useState(false);

    const fetchAll = useCallback(async () => {
        setLoading(true);
        try {
            const [plansRes, ...rest] = await Promise.all([
                axios.get(`${API}/subscriptions/plans`),
                ...(token ? [
                    axios.get(`${API}/subscriptions/my`, { headers }),
                    axios.get(`${API}/subscriptions/my/tickets`, { headers }),
                    axios.get(`${API}/wallet/balance`, { headers }),
                ] : [])
            ]);
            setPlans(plansRes.data || []);
            if (token) {
                setMySub(rest[0]?.data?.subscription || null);
                setMyTickets(rest[1]?.data || []);
                setWalletBalance(rest[2]?.data?.balance || 0);
            }
        } catch (e) { console.error(e); }
        setLoading(false);
    }, [token]);

    useEffect(() => {
        fetchAll();
        const ps = searchParams.get('payment');
        if (ps === 'success') { toast.success(isRomanian ? 'Abonament activat cu succes!' : 'Subscription activated!'); fetchAll(); }
        if (ps === 'failed') toast.error(isRomanian ? 'Plata a esuat.' : 'Payment failed.');
        if (ps === 'cancel') toast.info(isRomanian ? 'Plata anulata.' : 'Payment cancelled.');
    }, [fetchAll, searchParams, isRomanian]);

    const handlePurchase = async (planId, method) => {
        if (!isAuthenticated) { navigate('/login'); return; }
        setPurchasing(planId);
        try {
            const { data } = await axios.post(`${API}/subscriptions/purchase`, {
                plan_id: planId,
                payment_method: method
            }, { headers });
            if (data.checkout_url) {
                window.location.href = data.checkout_url;
            } else {
                toast.success(isRomanian ? 'Abonament activat! Biletele se distribuie...' : 'Subscription activated! Tickets being distributed...');
                fetchAll();
            }
        } catch (e) {
            toast.error(e.response?.data?.detail || 'Error');
        }
        setPurchasing(null);
    };

    const handleCancel = async () => {
        setCancelling(true);
        try {
            await axios.post(`${API}/subscriptions/cancel`, {}, { headers });
            toast.success(isRomanian ? 'Reinnoirea automata a fost anulata.' : 'Auto-renewal cancelled.');
            fetchAll();
        } catch (e) {
            toast.error(e.response?.data?.detail || 'Error');
        }
        setCancelling(false);
    };

    const isActive = mySub && mySub.status === 'active';
    const daysLeft = isActive ? Math.max(0, Math.ceil((new Date(mySub.expires_at) - new Date()) / (1000 * 60 * 60 * 24))) : 0;

    if (loading) {
        return (
            <div className="min-h-screen">
                <Navbar />
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="w-8 h-8 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen" data-testid="subscriptions-page">
            <Navbar />
            <div className="max-w-6xl mx-auto px-4 pt-24 pb-20">

                {/* Hero Header */}
                <div className="text-center mb-12">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 mb-4">
                        <Crown className="w-4 h-4 text-violet-400" />
                        <span className="text-sm text-violet-300 font-medium">
                            {isRomanian ? 'Abonamente Premium' : 'Premium Subscriptions'}
                        </span>
                    </div>
                    <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
                        {isRomanian ? 'Aboneaza-te si nu rata nicio competitie' : 'Subscribe & never miss a competition'}
                    </h1>
                    <p className="text-base sm:text-lg text-gray-400 max-w-2xl mx-auto">
                        {isRomanian
                            ? 'Abonamentul de 30 de zile iti ofera bilete gratuite la toate competitiile active. Primesti automat bilete si la competitiile noi lansate!'
                            : 'The 30-day subscription gives you free entries to all active competitions. You automatically receive tickets for newly launched competitions too!'
                        }
                    </p>
                </div>

                {/* Active Subscription Banner */}
                {isActive && (
                    <div className="relative overflow-hidden rounded-3xl p-6 mb-10" style={{
                        background: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(16,185,129,0.1))',
                        border: '1px solid rgba(139,92,246,0.25)'
                    }} data-testid="active-sub-banner">
                        <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-500/5 rounded-full blur-3xl" />
                        <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                            <div className="flex items-center gap-4">
                                <div className="w-14 h-14 rounded-2xl bg-emerald-500/15 flex items-center justify-center">
                                    <CheckCircle2 className="w-7 h-7 text-emerald-400" />
                                </div>
                                <div>
                                    <p className="text-sm text-emerald-400 font-semibold">{isRomanian ? 'Abonament Activ' : 'Active Subscription'}</p>
                                    <h3 className="text-xl font-bold text-white">{mySub.plan_name}</h3>
                                    <p className="text-sm text-gray-400">
                                        {mySub.entries_per_competition} {isRomanian ? 'bilete/competitie' : 'tickets/competition'} | {daysLeft} {isRomanian ? 'zile ramase' : 'days left'}
                                        {mySub.auto_renew && <span className="text-violet-400 ml-2">| Auto-reinnoire activa</span>}
                                    </p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <Button onClick={() => setShowTickets(!showTickets)} variant="outline" className="border-white/10 text-white hover:bg-white/5 rounded-xl gap-2" data-testid="view-sub-tickets">
                                    <Ticket className="w-4 h-4" /> {myTickets.length} {isRomanian ? 'bilete' : 'tickets'}
                                </Button>
                                {mySub.auto_renew && (
                                    <Button onClick={handleCancel} disabled={cancelling} variant="outline" className="border-red-500/20 text-red-400 hover:bg-red-500/10 rounded-xl gap-2" data-testid="cancel-sub-btn">
                                        {cancelling ? <RefreshCw className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                                        {isRomanian ? 'Anuleaza reinnoirea' : 'Cancel renewal'}
                                    </Button>
                                )}
                            </div>
                        </div>

                        {/* Tickets list */}
                        {showTickets && myTickets.length > 0 && (
                            <div className="mt-4 rounded-2xl bg-black/20 border border-white/[0.06] overflow-hidden">
                                <div className="p-3 border-b border-white/[0.06]">
                                    <p className="text-sm text-gray-400 font-medium">{isRomanian ? 'Bilete primite din abonament' : 'Tickets from subscription'}</p>
                                </div>
                                <div className="divide-y divide-white/[0.04] max-h-64 overflow-y-auto">
                                    {myTickets.map((t, i) => (
                                        <div key={i} className="flex items-center justify-between px-4 py-2.5 hover:bg-white/[0.02]">
                                            <div className="flex items-center gap-2 min-w-0">
                                                <Ticket className="w-4 h-4 text-violet-400 shrink-0" />
                                                <span className="text-sm text-white truncate">{t.competition_title}</span>
                                            </div>
                                            <span className="text-xs text-gray-500 shrink-0 ml-2">#{t.ticket_number}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Plans Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-12">
                    {plans.map((plan) => {
                        const meta = PLAN_FEATURES[plan.plan_id] || PLAN_FEATURES.sub_25;
                        const Icon = meta.icon;
                        const isCurrentPlan = isActive && mySub?.plan_id === plan.plan_id;
                        const canAfford = walletBalance >= plan.price;

                        return (
                            <div key={plan.plan_id}
                                className={`relative rounded-3xl overflow-hidden transition-all duration-300 hover:scale-[1.02] ${
                                    meta.popular ? 'ring-2 ring-violet-500/40' : ''
                                }`}
                                style={{
                                    background: 'linear-gradient(180deg, rgba(15,10,30,0.95) 0%, rgba(8,4,18,0.98) 100%)',
                                    border: '1px solid rgba(139,92,246,0.12)'
                                }}
                                data-testid={`plan-card-${plan.plan_id}`}
                            >
                                {meta.popular && (
                                    <div className="absolute top-0 left-0 right-0 bg-gradient-to-r from-violet-600 to-purple-600 text-center py-1.5">
                                        <span className="text-xs text-white font-bold tracking-wider uppercase">
                                            {isRomanian ? 'Cel Mai Popular' : 'Most Popular'}
                                        </span>
                                    </div>
                                )}

                                <div className={`p-6 ${meta.popular ? 'pt-10' : ''}`}>
                                    {/* Plan header */}
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${meta.color} flex items-center justify-center opacity-80`}>
                                            <Icon className="w-6 h-6 text-white" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                                            <p className="text-xs text-gray-500">{plan.duration_days} {isRomanian ? 'zile' : 'days'}</p>
                                        </div>
                                    </div>

                                    {/* Price */}
                                    <div className="mb-6">
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-4xl font-bold text-white">£{plan.price}</span>
                                            <span className="text-sm text-gray-500">/ {isRomanian ? 'luna' : 'month'}</span>
                                        </div>
                                    </div>

                                    {/* Key benefit */}
                                    <div className="mb-6 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                                        <div className="flex items-center gap-2 mb-1">
                                            <Ticket className="w-4 h-4 text-violet-400" />
                                            <span className="text-sm font-semibold text-white">
                                                {plan.entries_per_competition} {isRomanian ? 'bilete' : 'entries'}
                                            </span>
                                        </div>
                                        <p className="text-xs text-gray-400">
                                            {isRomanian
                                                ? 'la fiecare competitie activa in 30 de zile'
                                                : 'to each active competition within 30 days'}
                                        </p>
                                    </div>

                                    {/* Features */}
                                    <div className="space-y-2.5 mb-6">
                                        {[
                                            isRomanian ? 'Bilete automate la competitii noi' : 'Auto tickets for new competitions',
                                            isRomanian ? 'Premii: masini, cash, electronice' : 'Prizes: cars, cash, electronics',
                                            isRomanian ? 'Reinoire automata din wallet' : 'Auto-renewal from wallet',
                                            isRomanian ? 'Anuleaza oricand' : 'Cancel anytime',
                                        ].map((feat, i) => (
                                            <div key={i} className="flex items-center gap-2">
                                                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                                                <span className="text-sm text-gray-300">{feat}</span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Exclusion note */}
                                    <div className="mb-5 px-3 py-2 rounded-lg bg-amber-500/5 border border-amber-500/10">
                                        <p className="text-[11px] text-amber-400/70">
                                            {isRomanian
                                                ? 'Exclus: Competitii cu pret bilet > £3.99'
                                                : 'Excluded: Competitions with entry price > £3.99'}
                                        </p>
                                    </div>

                                    {/* Buttons */}
                                    {isCurrentPlan ? (
                                        <div className="flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                                            <span className="text-sm font-semibold text-emerald-300">
                                                {isRomanian ? 'Planul Tau Actual' : 'Your Current Plan'}
                                            </span>
                                        </div>
                                    ) : isActive ? (
                                        <div className="text-center py-3 text-sm text-gray-500">
                                            {isRomanian ? 'Ai deja un abonament activ' : 'You already have an active subscription'}
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            <Button
                                                onClick={() => handlePurchase(plan.plan_id, 'wallet')}
                                                disabled={purchasing === plan.plan_id || !canAfford}
                                                className={`w-full h-11 rounded-xl font-semibold text-sm gap-2 ${
                                                    canAfford
                                                        ? 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white'
                                                        : 'bg-white/5 text-gray-500 cursor-not-allowed'
                                                }`}
                                                data-testid={`buy-${plan.plan_id}-wallet`}
                                            >
                                                {purchasing === plan.plan_id
                                                    ? <RefreshCw className="w-4 h-4 animate-spin" />
                                                    : <Wallet className="w-4 h-4" />
                                                }
                                                {canAfford
                                                    ? (isRomanian ? `Plateste din Wallet (£${walletBalance.toFixed(2)})` : `Pay from Wallet (£${walletBalance.toFixed(2)})`)
                                                    : (isRomanian ? `Wallet insuficient (£${walletBalance.toFixed(2)})` : `Wallet insufficient (£${walletBalance.toFixed(2)})`)
                                                }
                                            </Button>
                                            <Button
                                                onClick={() => handlePurchase(plan.plan_id, 'viva')}
                                                disabled={purchasing === plan.plan_id}
                                                variant="outline"
                                                className="w-full h-11 rounded-xl font-semibold text-sm gap-2 border-white/10 text-white hover:bg-white/5"
                                                data-testid={`buy-${plan.plan_id}-card`}
                                            >
                                                <CreditCard className="w-4 h-4" />
                                                {isRomanian ? 'Plateste cu Cardul' : 'Pay with Card'}
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* How it works */}
                <div className="rounded-3xl p-6 sm:p-8" style={{
                    background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                    border: '1px solid rgba(139,92,246,0.1)'
                }}>
                    <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-violet-400" />
                        {isRomanian ? 'Cum Functioneaza?' : 'How Does it Work?'}
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                            {
                                icon: CreditCard, color: 'violet',
                                title: isRomanian ? '1. Alege un Plan' : '1. Choose a Plan',
                                desc: isRomanian ? 'Selecteaza planul care ti se potriveste si plateste din wallet sau cu cardul.' : 'Select the plan that suits you and pay from wallet or card.'
                            },
                            {
                                icon: Ticket, color: 'emerald',
                                title: isRomanian ? '2. Primesti Bilete' : '2. Get Tickets',
                                desc: isRomanian ? 'Primesti automat bilete la toate competitiile active (pret ≤ £3.99).' : 'Automatically receive tickets to all active competitions (price ≤ £3.99).'
                            },
                            {
                                icon: Layers, color: 'orange',
                                title: isRomanian ? '3. Competitii Noi' : '3. New Competitions',
                                desc: isRomanian ? 'Cand se lanseaza o competitie noua, primesti biletele automat fara sa faci nimic.' : 'When a new competition launches, you get tickets automatically.'
                            },
                            {
                                icon: CalendarDays, color: 'blue',
                                title: isRomanian ? '4. Reinoire Automata' : '4. Auto-Renewal',
                                desc: isRomanian ? 'Abonamentul se reinnoieste automat din wallet. Anuleaza oricand vrei.' : 'Subscription auto-renews from wallet. Cancel anytime.'
                            },
                        ].map((step, i) => {
                            const Icon = step.icon;
                            return (
                                <div key={i} className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
                                    <Icon className={`w-6 h-6 text-${step.color}-400 mb-3`} />
                                    <h4 className="text-sm font-semibold text-white mb-1">{step.title}</h4>
                                    <p className="text-xs text-gray-500 leading-relaxed">{step.desc}</p>
                                </div>
                            );
                        })}
                    </div>

                    <div className="mt-6 p-3 rounded-xl bg-amber-500/5 border border-amber-500/10">
                        <p className="text-xs text-amber-400/80">
                            <strong>{isRomanian ? 'Excludere:' : 'Exclusion:'}</strong>{' '}
                            {isRomanian
                                ? 'Competitiile cu pret bilet mai mare de £3.99 sunt excluse din beneficiile abonamentului. Biletele de abonament nu vor fi emise pentru astfel de competitii.'
                                : 'Competitions where the entry price exceeds £3.99 per entry are excluded from subscription benefits.'}
                        </p>
                    </div>
                </div>
            </div>
            <Footer />
        </div>
    );
}
