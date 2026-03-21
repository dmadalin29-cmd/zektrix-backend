import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import InstallPrompt from '../components/InstallPrompt';
import CookieConsent from '../components/CookieConsent';
import axios from 'axios';

import { ArrowRight, Zap, ChevronRight, MessageCircle, Radio, Users, Trophy, Ticket, Sparkles, Star, Crown, Clock, Flame } from 'lucide-react';
import CountdownTimer from '../components/CountdownTimer';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FAKE_NAMES = [
    'Andrei M.', 'Maria P.', 'Alexandru D.', 'Elena S.', 'Mihai C.', 
    'Ana R.', 'Ion V.', 'Cristina B.', 'George T.', 'Ioana L.',
    'Adrian N.', 'Laura G.', 'Daniel F.', 'Simona H.', 'Florin A.',
    'Diana M.', 'Bogdan I.', 'Raluca E.', 'Stefan O.', 'Alina D.',
    'Vlad C.', 'Andreea P.', 'Razvan S.', 'Monica T.', 'Cosmin B.'
];

const TikTokIcon = () => (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
    </svg>
);

const ActivityTicker = ({ activities, competitions }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const mixedActivities = useMemo(() => {
        const mixed = [...activities];
        if (competitions.length > 0) {
            for (let i = 0; i < 20; i++) {
                const rn = FAKE_NAMES[Math.floor(Math.random() * FAKE_NAMES.length)];
                const rc = competitions[Math.floor(Math.random() * competitions.length)];
                mixed.push({ type: 'purchase', username: rn, message: `a rezervat loc la ${rc.title?.substring(0, 30)}`, fake: true });
            }
        }
        return mixed.sort(() => Math.random() - 0.5);
    }, [activities, competitions]);

    useEffect(() => {
        if (mixedActivities.length === 0) return;
        const interval = setInterval(() => setCurrentIndex(p => (p + 1) % mixedActivities.length), 3500);
        return () => clearInterval(interval);
    }, [mixedActivities.length]);

    if (mixedActivities.length === 0) return null;
    const current = mixedActivities[currentIndex];

    return (
        <div className="bg-white/[0.03] backdrop-blur-sm border-b border-white/[0.06]">
            <div className="max-w-7xl mx-auto px-4 py-2">
                <div className="flex items-center justify-center gap-2 text-sm overflow-hidden">
                    {current?.type === 'winner' ? (
                        <Trophy className="w-4 h-4 text-amber-400 animate-bounce flex-shrink-0" />
                    ) : (
                        <Sparkles className="w-4 h-4 text-violet-400 animate-pulse flex-shrink-0" />
                    )}
                    <span className="font-bold text-white truncate">{current?.username}</span>
                    <span className="text-[#A39EBD] truncate">{current?.message}</span>
                </div>
            </div>
        </div>
    );
};

const SpecialCompCard = ({ c }) => {
    if (!c) return null;
    const progress = (c.sold_tickets / c.max_tickets) * 100;
    const remaining = c.max_tickets - c.sold_tickets;
    const isHot = progress >= 70;
    const isAlmostGone = progress >= 90;

    return (
        <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-amber-500/30 via-orange-500/30 to-red-500/30 rounded-3xl blur-xl opacity-40 group-hover:opacity-60 transition-opacity duration-500" />
            <Link to={`/competitions/${c.competition_id}`}
                className="relative block bg-white/[0.04] backdrop-blur-sm rounded-3xl overflow-hidden border border-amber-500/20 hover:border-amber-400/40 transition-all duration-300 hover:-translate-y-1"
                data-testid="special-comp-card"
            >
                <div className="relative p-6">
                    <div className="flex items-center gap-2 mb-4 flex-wrap">
                        <span className="px-3 py-1.5 bg-gradient-to-r from-amber-500 to-orange-500 text-black text-xs font-black rounded-full flex items-center gap-1.5 shadow-[0_0_20px_rgba(245,158,11,0.4)]">
                            <Sparkles className="w-3 h-3" /> SPECIAL
                        </span>
                        {isAlmostGone && (
                            <span className="px-2.5 py-1 bg-red-500/20 text-red-400 text-xs font-bold rounded-full border border-red-500/30 flex items-center gap-1 animate-pulse">
                                <Flame className="w-3 h-3" /> ULTIMELE LOCURI
                            </span>
                        )}
                        {!isAlmostGone && isHot && (
                            <span className="px-2.5 py-1 bg-orange-500/20 text-orange-400 text-xs font-bold rounded-full border border-orange-500/30 flex items-center gap-1">
                                <Flame className="w-3 h-3" /> SE VINDE REPEDE
                            </span>
                        )}
                        {c.competition_type === 'instant_win' && (
                            <span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/20">AUTODRAW</span>
                        )}
                        {c.competition_type === 'draw' && (
                            <span className="px-2 py-1 bg-violet-500/10 text-violet-400 text-xs font-bold rounded-full border border-violet-500/20">DRAW</span>
                        )}
                    </div>

                    <div className="relative aspect-video rounded-2xl overflow-hidden mb-4 border border-white/[0.06]">
                        <img src={c.image_url} alt={c.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" loading="lazy" />
                        <div className="absolute inset-0 bg-gradient-to-t from-[#060311]/90 via-transparent to-transparent" />
                        <div className="absolute bottom-3 left-4 right-4">
                            <div className="flex items-end justify-between">
                                <div>
                                    <p className="text-xs text-[#A39EBD]">PREMIU</p>
                                    <p className="text-3xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-amber-300 via-orange-400 to-red-400">
                                        {c.prize_value?.toLocaleString() || '10,000'} £
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-[#A39EBD]">PRET LOC</p>
                                    <p className="text-2xl font-black text-emerald-400">{(c.is_free || c.ticket_price === 0) ? 'GRATUIT' : `£${c.ticket_price}`}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <h2 className="text-xl font-black tracking-tight text-white mb-3">{c.title}</h2>

                    {c.draw_date && (
                        <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                            <Clock className="w-4 h-4 text-amber-400" />
                            <span className="text-xs text-[#A39EBD]">Se termina in:</span>
                            <CountdownTimer targetDate={c.draw_date} compact />
                        </div>
                    )}

                    <div className="mb-4">
                        <div className="flex justify-between text-sm mb-1.5">
                            <span className="text-[#A39EBD]">Progres: <span className={`font-semibold ${isAlmostGone ? 'text-red-400' : isHot ? 'text-orange-400' : 'text-white'}`}>{progress.toFixed(1)}%</span></span>
                            <span className="text-[#A39EBD]">Libere: <span className={`font-semibold ${isAlmostGone ? 'text-red-400' : 'text-emerald-400'}`}>{remaining.toLocaleString()}</span></span>
                        </div>
                        <div className="h-2.5 bg-white/[0.06] rounded-full overflow-hidden">
                            <div className={`h-full rounded-full transition-all duration-500 relative ${isAlmostGone ? 'bg-gradient-to-r from-red-500 to-red-400' : isHot ? 'bg-gradient-to-r from-orange-500 to-red-500' : 'bg-gradient-to-r from-amber-500 via-orange-500 to-red-500'}`} style={{width: `${Math.max(progress, 2)}%`}}>
                                {isHot && <div className="absolute inset-0 bg-white/20 animate-pulse rounded-full" />}
                            </div>
                        </div>
                    </div>

                    <button className="w-full py-3.5 bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 hover:from-amber-400 hover:via-orange-400 hover:to-red-400 text-black font-black rounded-full transition-all duration-300 flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(255,94,0,0.3)] hover:shadow-[0_0_30px_rgba(255,94,0,0.5)] hover:scale-[1.02]">
                        <Star className="w-5 h-5" /> REZERVA LOC ACUM <ArrowRight className="w-5 h-5" />
                    </button>
                </div>
            </Link>
        </div>
    );
};

const FeaturedCard = ({ c }) => {
    if (!c) return null;
    const progress = (c.sold_tickets / c.max_tickets) * 100;
    const remaining = c.max_tickets - c.sold_tickets;
    const isHot = progress >= 70;
    const isAlmostGone = progress >= 90;

    return (
        <div>
            <Link to={`/competitions/${c.competition_id}`}
                className="block relative bg-white/[0.04] backdrop-blur-sm rounded-3xl overflow-hidden border border-violet-500/15 hover:border-violet-400/30 transition-all duration-300 group h-full hover:-translate-y-1"
                data-testid="featured-comp-card"
            >
                <div className="relative h-full flex flex-col">
                    <div className="relative flex-1 min-h-[250px]">
                        <img src={c.image_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&q=80'} alt={c.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" loading="lazy" />
                        <div className="absolute inset-0 bg-gradient-to-t from-[#060311] via-[#060311]/30 to-transparent" />
                        <div className="absolute top-3 left-3 flex gap-2 flex-wrap">
                            <span className="px-3 py-1.5 bg-[#8B3DFF] text-white text-xs font-bold rounded-full shadow-[0_0_15px_rgba(139,61,255,0.4)]">OFERTA RECOMANDATA</span>
                            {isAlmostGone && (
                                <span className="px-2.5 py-1 bg-red-500/90 text-white text-xs font-bold rounded-full flex items-center gap-1 animate-pulse">
                                    <Flame className="w-3 h-3" /> ULTIMELE LOCURI
                                </span>
                            )}
                            {!isAlmostGone && isHot && (
                                <span className="px-2.5 py-1 bg-orange-500/90 text-white text-xs font-bold rounded-full flex items-center gap-1">
                                    <Flame className="w-3 h-3" /> SE VINDE REPEDE
                                </span>
                            )}
                            {c.competition_type === 'instant_win' && (
                                <span className="px-2 py-1 bg-emerald-500/10 backdrop-blur-sm text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/20">AUTODRAW</span>
                            )}
                        </div>
                    </div>
                    <div className="p-5">
                        <h2 className="text-xl font-black tracking-tight text-white mb-3">{c.title}</h2>
                        {c.draw_date && (
                            <div className="flex items-center gap-2 mb-3 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.06] w-fit">
                                <Clock className="w-3.5 h-3.5 text-violet-400" />
                                <CountdownTimer targetDate={c.draw_date} compact />
                            </div>
                        )}
                        <div className="mb-3">
                            <div className="flex justify-between text-xs mb-1.5">
                                <span className="text-[#A39EBD]">Progres: <span className={`font-semibold ${isAlmostGone ? 'text-red-400' : isHot ? 'text-orange-400' : 'text-white'}`}>{progress.toFixed(1)}%</span></span>
                                <span className="text-[#A39EBD]">Libere: <span className={`font-semibold ${isAlmostGone ? 'text-red-400' : 'text-violet-400'}`}>{remaining.toLocaleString()}</span></span>
                            </div>
                            <div className="h-2 bg-white/[0.06] rounded-full overflow-hidden">
                                <div className={`h-full rounded-full transition-all ${isAlmostGone ? 'bg-gradient-to-r from-red-500 to-red-400' : isHot ? 'bg-gradient-to-r from-orange-500 to-red-500' : 'bg-gradient-to-r from-violet-500 to-[#FF5E00]'}`} style={{width: `${Math.max(progress, 2)}%`}}>
                                    {isHot && <div className="absolute inset-0 bg-white/20 animate-pulse rounded-full" />}
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-xs text-[#6E6987]">PRET LOC</p>
                                <p className="text-xl font-bold text-violet-400">{(c.is_free || c.ticket_price === 0) ? <span className="text-emerald-400">GRATUIT</span> : `£${c.ticket_price?.toFixed(2)}`}</p>
                            </div>
                            <span className="px-5 py-2.5 bg-gradient-to-r from-[#8B3DFF] to-[#A666FF] hover:from-[#A666FF] hover:to-[#8B3DFF] text-white font-bold rounded-full transition-all duration-300 flex items-center gap-2 shadow-[0_0_15px_rgba(139,61,255,0.3)]">
                                Participa <ArrowRight className="w-4 h-4" />
                            </span>
                        </div>
                    </div>
                </div>
            </Link>
        </div>
    );
};

const CompCard = ({ c, index }) => {
    const progress = (c.sold_tickets / c.max_tickets) * 100;
    const remaining = c.max_tickets - c.sold_tickets;
    const isHot = progress >= 70;
    const isAlmostGone = progress >= 90;

    return (
        <div>
            <Link to={`/competitions/${c.competition_id}`}
                className="group block bg-white/[0.03] backdrop-blur-xl rounded-2xl overflow-hidden border border-white/[0.06] hover:border-violet-500/25 transition-all duration-300 hover:-translate-y-1"
                data-testid={`comp-card-${c.competition_id}`}
            >
                <div className="relative aspect-[4/3] overflow-hidden">
                    <img src={c.image_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80'} alt={c.title} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" loading="lazy" />
                    <div className="absolute top-2.5 left-2.5 flex gap-1.5 flex-wrap">
                        {c.competition_type === 'instant_win' && (
                            <span className="px-2 py-1 bg-emerald-500/80 backdrop-blur-sm text-white text-[10px] font-bold rounded-full">AUTODRAW</span>
                        )}
                        {c.competition_type === 'draw' && (
                            <span className="px-2 py-1 bg-violet-500/80 backdrop-blur-sm text-white text-[10px] font-bold rounded-full">DRAW</span>
                        )}
                        {isAlmostGone && (
                            <span className="px-2 py-1 bg-red-500/90 backdrop-blur-sm text-white text-[10px] font-bold rounded-full animate-pulse flex items-center gap-1">
                                <Flame className="w-2.5 h-2.5" /> ULTIMELE LOCURI
                            </span>
                        )}
                        {!isAlmostGone && isHot && (
                            <span className="px-2 py-1 bg-orange-500/90 backdrop-blur-sm text-white text-[10px] font-bold rounded-full flex items-center gap-1">
                                <Flame className="w-2.5 h-2.5" /> HOT
                            </span>
                        )}
                    </div>
                    <div className="absolute bottom-2.5 left-2.5">
                        <span className="px-2.5 py-1 bg-[#8B3DFF]/90 backdrop-blur-sm text-white text-xs font-bold rounded-full">{(c.is_free || c.ticket_price === 0) ? 'GRATUIT' : `£${c.ticket_price?.toFixed(2)}`}</span>
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-t from-[#060311]/60 via-transparent to-transparent" />
                </div>
                <div className="p-4">
                    <h3 className="font-bold text-white text-sm mb-2 truncate tracking-tight">{c.title}</h3>
                    {c.draw_date && (
                        <div className="flex items-center gap-1.5 mb-2 text-[10px]">
                            <Clock className="w-3 h-3 text-violet-400" />
                            <CountdownTimer targetDate={c.draw_date} compact />
                        </div>
                    )}
                    <div>
                        <div className="flex justify-between text-[10px] mb-1">
                            <span className={`${isAlmostGone ? 'text-red-400 font-bold' : isHot ? 'text-orange-400 font-semibold' : 'text-[#6E6987]'}`}>{progress.toFixed(0)}% vandut</span>
                            <span className={`${isAlmostGone ? 'text-red-400' : 'text-[#6E6987]'}`}>{remaining.toLocaleString()} libere</span>
                        </div>
                        <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${isAlmostGone ? 'bg-gradient-to-r from-red-500 to-red-400' : isHot ? 'bg-gradient-to-r from-orange-500 to-red-500' : 'bg-gradient-to-r from-violet-500 to-[#FF5E00]'}`} style={{width: `${Math.max(progress, 3)}%`}} />
                        </div>
                    </div>
                </div>
            </Link>
        </div>
    );
};

const StatCard = ({ icon: Icon, label, value, gradient }) => (
    <div className="flex items-center gap-3 p-3.5 bg-white/[0.03] backdrop-blur-xl rounded-2xl border border-white/[0.06] hover:border-white/[0.12] transition-all duration-300">
        <div className={`w-10 h-10 rounded-xl ${gradient} flex items-center justify-center shadow-lg`}>
            <Icon className="w-5 h-5 text-white" strokeWidth={1.5} />
        </div>
        <div>
            <p className="text-[10px] text-[#6E6987] uppercase tracking-wider">{label}</p>
            <p className="text-lg font-bold text-white tracking-tight">{value}</p>
        </div>
    </div>
);

const HomePage = () => {
    const { isRomanian } = useLanguage();
    const [comps, setComps] = useState([]);
    const [tiktokLive, setTiktokLive] = useState({ is_live: false, tiktok_url: 'https://www.tiktok.com/@zektrix.uk' });
    const [stats, setStats] = useState({ winners: 0, users: 0, tickets: 0 });
    const [activities, setActivities] = useState([]);
    const [featuredComp, setFeaturedComp] = useState(null);
    const [reviews, setReviews] = useState([]);

    useEffect(() => {
        Promise.all([
            axios.get(`${API}/competitions?status=active`).catch(() => ({ data: [] })),
            axios.get(`${API}/settings/tiktok-live`).catch(() => ({ data: { is_live: false, tiktok_url: 'https://www.tiktok.com/@zektrix.uk' } })),
            axios.get(`${API}/stats`).catch(() => ({ data: { winners: 0, users: 0, tickets: 0 } })),
            axios.get(`${API}/activity/recent`).catch(() => ({ data: [] })),
            axios.get(`${API}/settings/featured-competition`).catch(() => ({ data: {} })),
            axios.get(`${API}/reviews?limit=6`).catch(() => ({ data: [] })),
        ]).then(([compsRes, tiktokRes, statsRes, actRes, featRes, reviewsRes]) => {
            setComps(compsRes.data);
            setTiktokLive(tiktokRes.data);
            setStats(statsRes.data);
            setActivities(actRes.data);
            setFeaturedComp(featRes.data?.competition || null);
            setReviews(reviewsRes.data || []);
        });
    }, []);

    const specialComp = comps.find(c => c.is_permanent || c.title?.includes('Speciala'));
    const displayFeatured = featuredComp || comps.find(c => (c.category === 'cars' || c.category === 'auto') && c.competition_id !== specialComp?.competition_id) || comps.find(c => c.competition_id !== specialComp?.competition_id);
    const otherComps = comps.filter(c => c.competition_id !== specialComp?.competition_id && c.competition_id !== displayFeatured?.competition_id);

    return (
        <div className="min-h-screen" data-testid="home-page">
            <Navbar />

            <div className="pt-24">
                <ActivityTicker activities={activities} competitions={comps} />
            </div>

            <main className="pb-12">
                {/* Hero Section */}
                <section className="py-8 md:py-12">
                    <div className="max-w-7xl mx-auto px-4">
                        <div className="grid lg:grid-cols-2 gap-6 items-stretch">
                            <SpecialCompCard c={specialComp} />
                            <FeaturedCard c={displayFeatured} />
                        </div>
                    </div>
                </section>

                {/* Subscription CTA */}
                <section className="py-4">
                    <div className="max-w-7xl mx-auto px-4">
                        <Link to="/subscriptions" className="block" data-testid="home-sub-cta">
                            <div
                                className="relative overflow-hidden rounded-2xl p-5 bg-gradient-to-r from-[#8B3DFF]/10 via-[#FF5E00]/5 to-[#8B3DFF]/10 border border-[#8B3DFF]/20 hover:border-[#8B3DFF]/40 transition-all duration-300 group"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-[#8B3DFF]/20 flex items-center justify-center">
                                            <Crown className="w-5 h-5 text-[#A666FF]" />
                                        </div>
                                        <div>
                                            <p className="text-white font-bold text-sm tracking-tight">
                                                {isRomanian ? 'Abonamente Premium' : 'Premium Subscriptions'}
                                            </p>
                                            <p className="text-[#A39EBD] text-xs">
                                                {isRomanian ? 'De la £25/luna — bilete automate la toate competitiile' : 'From £25/mo — auto tickets to all competitions'}
                                            </p>
                                        </div>
                                    </div>
                                    <ArrowRight className="w-5 h-5 text-[#A666FF] group-hover:translate-x-1 transition-transform duration-300" />
                                </div>
                            </div>
                        </Link>
                    </div>
                </section>

                {/* Stats & Social */}
                <section className="py-4">
                    <div className="max-w-7xl mx-auto px-4">
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                            <StatCard icon={Trophy} label="Castigatori" value={stats.winners || 0} gradient="bg-gradient-to-br from-amber-500 to-amber-600" />
                            <StatCard icon={Users} label="Utilizatori" value={stats.users || 0} gradient="bg-gradient-to-br from-violet-500 to-violet-600" />
                            <StatCard icon={Ticket} label="Locuri Rezervate" value={stats.tickets || 0} gradient="bg-gradient-to-br from-orange-500 to-orange-600" />

                            <a href="https://wa.me/40730268067" target="_blank" rel="noopener noreferrer"
                                className="flex items-center gap-2.5 p-3.5 bg-white/[0.03] backdrop-blur-xl rounded-2xl border border-white/[0.06] hover:border-emerald-500/25 transition-all duration-300">
                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg">
                                    <MessageCircle className="w-5 h-5 text-white" strokeWidth={1.5} />
                                </div>
                                <div>
                                    <p className="text-[10px] text-[#6E6987] uppercase tracking-wider">COMUNITATE</p>
                                    <p className="text-white text-xs font-semibold">WhatsApp</p>
                                </div>
                            </a>

                            <a href={tiktokLive.tiktok_url} target="_blank" rel="noopener noreferrer"
                                className={`flex items-center gap-2.5 p-3.5 bg-white/[0.03] backdrop-blur-xl rounded-2xl border transition-all duration-300 relative overflow-hidden ${
                                    tiktokLive.is_live ? 'border-red-500/40 shadow-[0_0_20px_rgba(239,68,68,0.15)]' : 'border-white/[0.06] hover:border-pink-500/25'
                                }`}
                            >
                                {tiktokLive.is_live && <div className="absolute inset-0 bg-gradient-to-r from-red-500/5 to-pink-500/5 animate-pulse" />}
                                <div className={`relative w-10 h-10 rounded-xl flex items-center justify-center shadow-lg ${
                                    tiktokLive.is_live ? 'bg-gradient-to-br from-red-500 to-pink-500 animate-pulse' : 'bg-gradient-to-br from-[#25F4EE] via-[#FE2C55] to-[#000000]'
                                }`}>
                                    {tiktokLive.is_live ? <Radio className="w-5 h-5 text-white" /> : <TikTokIcon />}
                                </div>
                                <div className="relative">
                                    {tiktokLive.is_live ? (
                                        <>
                                            <div className="flex items-center gap-1">
                                                <span className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                                                <p className="text-[10px] text-red-400 font-bold uppercase tracking-wider">LIVE ACUM</p>
                                            </div>
                                            <p className="text-white text-xs font-bold">Urmareste!</p>
                                        </>
                                    ) : (
                                        <>
                                            <p className="text-[10px] text-[#6E6987] uppercase tracking-wider">URMARESTE</p>
                                            <p className="text-white text-xs font-semibold">TikTok</p>
                                        </>
                                    )}
                                </div>
                            </a>
                        </div>
                    </div>
                </section>

                {/* Other Competitions */}
                <section className="py-8">
                    <div className="max-w-7xl mx-auto px-4">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-black text-white tracking-tight">{isRomanian ? 'Alte Competitii' : 'Other Competitions'}</h2>
                            <Link to="/competitions" className="text-[#A666FF] text-sm font-medium flex items-center gap-1 hover:text-[#8B3DFF] transition-colors duration-200">
                                {isRomanian ? 'Vezi toate' : 'View all'} <ChevronRight className="w-4 h-4" />
                            </Link>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {otherComps.slice(0, 8).map((c, i) => <CompCard key={c.competition_id} c={c} index={i} />)}
                        </div>
                    </div>
                </section>
                {/* Reviews / Testimonials */}
                {reviews.length > 0 && (
                    <section className="py-8">
                        <div className="max-w-7xl mx-auto px-4">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-2">
                                    <Star className="w-5 h-5 text-amber-400" />
                                    <h2 className="text-xl font-black text-white tracking-tight">{isRomanian ? 'Ce Spun Castigatorii' : 'What Winners Say'}</h2>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {reviews.map((review) => (
                                    <div key={review.review_id}
                                        className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06] hover:border-violet-500/20 transition-all duration-300"
                                        data-testid={`review-${review.review_id}`}
                                    >
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/30 to-orange-500/30 border border-white/10 flex items-center justify-center overflow-hidden">
                                                {review.picture ? (
                                                    <img src={review.picture} alt="" className="w-full h-full object-cover" />
                                                ) : (
                                                    <span className="text-xs font-bold text-white">{review.username?.charAt(0)?.toUpperCase() || 'U'}</span>
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-bold text-white truncate">{review.username}</p>
                                                <p className="text-[10px] text-gray-500 truncate">{review.competition_title || review.prize_description}</p>
                                            </div>
                                        </div>
                                        <div className="flex gap-0.5 mb-2">
                                            {[1, 2, 3, 4, 5].map(s => (
                                                <Star key={s} className={`w-3.5 h-3.5 ${s <= review.rating ? 'text-amber-400 fill-amber-400' : 'text-gray-700'}`} />
                                            ))}
                                        </div>
                                        <p className="text-sm text-gray-400 leading-relaxed line-clamp-3">{review.text}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </section>
                )}
            </main>
            <Footer />
            <InstallPrompt />
            <CookieConsent />
        </div>
    );
};

export default HomePage;
