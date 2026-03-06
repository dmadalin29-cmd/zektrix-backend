import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import InstallPrompt from '../components/InstallPrompt';
import CookieConsent from '../components/CookieConsent';
import axios from 'axios';
import { ArrowRight, Zap, ChevronRight, MessageCircle, Radio, Users, Trophy, Ticket, Sparkles, Star } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Fake Romanian names for ticker
const FAKE_NAMES = [
    'Andrei M.', 'Maria P.', 'Alexandru D.', 'Elena S.', 'Mihai C.', 
    'Ana R.', 'Ion V.', 'Cristina B.', 'George T.', 'Ioana L.',
    'Adrian N.', 'Laura G.', 'Daniel F.', 'Simona H.', 'Florin A.',
    'Diana M.', 'Bogdan I.', 'Raluca E.', 'Stefan O.', 'Alina D.',
    'Vlad C.', 'Andreea P.', 'Razvan S.', 'Monica T.', 'Cosmin B.'
];

// TikTok Icon
const TikTokIcon = () => (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
    </svg>
);

// Live Activity Ticker with FAKE + Real data
const ActivityTicker = ({ activities, competitions }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    
    // Generate mixed activities (real + fake)
    const mixedActivities = useMemo(() => {
        const mixed = [...activities];
        
        // Add fake purchases if we have competitions
        if (competitions.length > 0) {
            for (let i = 0; i < 20; i++) {
                const randomName = FAKE_NAMES[Math.floor(Math.random() * FAKE_NAMES.length)];
                const randomComp = competitions[Math.floor(Math.random() * competitions.length)];
                mixed.push({
                    type: 'purchase',
                    username: randomName,
                    message: `a rezervat loc la ${randomComp.title?.substring(0, 30)}`,
                    fake: true
                });
            }
        }
        
        // Shuffle array
        return mixed.sort(() => Math.random() - 0.5);
    }, [activities, competitions]);
    
    useEffect(() => {
        if (mixedActivities.length === 0) return;
        const interval = setInterval(() => {
            setCurrentIndex(prev => (prev + 1) % mixedActivities.length);
        }, 3500);
        return () => clearInterval(interval);
    }, [mixedActivities.length]);
    
    if (mixedActivities.length === 0) return null;
    const current = mixedActivities[currentIndex];
    
    return (
        <div className="bg-gradient-to-r from-violet-600/20 via-purple-600/20 to-violet-600/20 border-b border-violet-500/20">
            <div className="max-w-7xl mx-auto px-4 py-2">
                <div className="flex items-center justify-center gap-2 text-sm overflow-hidden">
                    {current?.type === 'winner' ? (
                        <Trophy className="w-4 h-4 text-yellow-400 animate-bounce flex-shrink-0" />
                    ) : (
                        <Sparkles className="w-4 h-4 text-violet-400 animate-pulse flex-shrink-0" />
                    )}
                    <span className="font-bold text-white truncate">{current?.username}</span>
                    <span className="text-gray-400 truncate">{current?.message}</span>
                    {current?.type === 'winner' && <span className="text-yellow-400 flex-shrink-0">🎉</span>}
                </div>
            </div>
        </div>
    );
};

// Special Competition Card - STÂNGA cu efecte WOW
const SpecialCompCard = ({ c }) => {
    if (!c) return null;
    const progress = (c.sold_tickets / c.max_tickets) * 100;
    const remaining = c.max_tickets - c.sold_tickets;
    
    return (
        <div className="relative group">
            {/* Glow effects */}
            <div className="absolute -inset-1 bg-gradient-to-r from-yellow-500 via-orange-500 to-red-500 rounded-2xl blur-lg opacity-40 group-hover:opacity-60 transition-opacity animate-pulse" />
            <div className="absolute -inset-0.5 bg-gradient-to-r from-yellow-400 via-orange-400 to-red-400 rounded-2xl opacity-20" />
            
            <Link 
                to={`/competitions/${c.competition_id}`}
                className="relative block bg-gradient-to-br from-[#1a1520] via-[#15121a] to-[#1a1015] rounded-2xl overflow-hidden border border-yellow-500/30 hover:border-yellow-400/50 transition-all"
            >
                {/* Animated particles background */}
                <div className="absolute inset-0 overflow-hidden">
                    <div className="absolute top-10 left-10 w-20 h-20 bg-yellow-500/10 rounded-full blur-xl animate-pulse" />
                    <div className="absolute bottom-10 right-10 w-32 h-32 bg-orange-500/10 rounded-full blur-xl animate-pulse delay-500" />
                </div>
                
                <div className="relative p-6">
                    {/* Header badges */}
                    <div className="flex items-center gap-2 mb-4 flex-wrap">
                        <span className="px-3 py-1 bg-gradient-to-r from-yellow-500 to-orange-500 text-black text-xs font-black rounded-full flex items-center gap-1 animate-pulse">
                            <Sparkles className="w-3 h-3" /> SPECIAL
                        </span>
                        <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs font-bold rounded border border-green-500/30">
                            AUTODRAW
                        </span>
                    </div>
                    
                    {/* Image */}
                    <div className="relative aspect-video rounded-xl overflow-hidden mb-4 border border-yellow-500/20">
                        <img src={c.image_url} alt={c.title} className="w-full h-full object-cover" loading="lazy" />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                        <div className="absolute bottom-3 left-3 right-3">
                            <div className="flex items-end justify-between">
                                <div>
                                    <p className="text-xs text-gray-400">PREMIU</p>
                                    <p className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-orange-400 to-red-400">
                                        {c.prize_value?.toLocaleString() || '10.000'} RON
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-gray-400">PREȚ LOC</p>
                                    <p className="text-2xl font-black text-green-400">{c.ticket_price} RON</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    {/* Title */}
                    <h2 className="text-xl font-black text-white mb-3">{c.title}</h2>
                    
                    {/* Progress */}
                    <div className="mb-4">
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-400">Progres: <span className="text-white font-bold">{progress.toFixed(1)}%</span></span>
                            <span className="text-gray-400">Libere: <span className="text-green-400 font-bold">{remaining.toLocaleString()}</span></span>
                        </div>
                        <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-yellow-500 via-orange-500 to-red-500 rounded-full transition-all duration-500 relative" style={{width: `${Math.max(progress, 2)}%`}}>
                                <div className="absolute inset-0 bg-white/20 animate-pulse" />
                            </div>
                        </div>
                    </div>
                    
                    {/* CTA */}
                    <button className="w-full py-3 bg-gradient-to-r from-yellow-500 via-orange-500 to-red-500 hover:from-yellow-400 hover:via-orange-400 hover:to-red-400 text-black font-black rounded-xl transition-all flex items-center justify-center gap-2">
                        <Star className="w-5 h-5" />
                        REZERVĂ LOC ACUM
                        <ArrowRight className="w-5 h-5" />
                    </button>
                </div>
            </Link>
        </div>
    );
};

// Featured Card - Cars (DREAPTA) cu Progress Bar
const FeaturedCard = ({ c }) => {
    if (!c) return null;
    const progress = (c.sold_tickets / c.max_tickets) * 100;
    const remaining = c.max_tickets - c.sold_tickets;
    
    return (
        <Link to={`/competitions/${c.competition_id}`} className="block relative bg-gradient-to-br from-[#1a1625] to-[#12111a] rounded-2xl overflow-hidden border border-violet-500/20 hover:border-violet-400/40 transition-all group h-full">
            <div className="absolute inset-0 bg-gradient-to-br from-violet-600/5 to-orange-500/5" />
            <div className="relative h-full flex flex-col">
                <div className="relative flex-1 min-h-[250px]">
                    <img src={c.image_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&q=80'} alt={c.title} className="w-full h-full object-cover" loading="lazy" />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0a0614] via-transparent to-transparent" />
                    <div className="absolute top-3 left-3 flex gap-2">
                        <span className="px-2 py-1 bg-violet-600 text-white text-xs font-bold rounded">FEATURED</span>
                    </div>
                </div>
                <div className="p-5">
                    <h2 className="text-xl font-black text-white mb-3">{c.title}</h2>
                    
                    {/* Progress Bar */}
                    <div className="mb-3">
                        <div className="flex justify-between text-xs mb-1">
                            <span className="text-gray-400">Progres: <span className="text-white font-bold">{progress.toFixed(1)}%</span></span>
                            <span className="text-gray-400">Libere: <span className="text-violet-400 font-bold">{remaining.toLocaleString()}</span></span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-violet-500 to-orange-500 rounded-full transition-all" style={{width: `${Math.max(progress, 2)}%`}} />
                        </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs text-gray-500">PREȚ LOC</p>
                            <p className="text-xl font-bold text-violet-400">RON {c.ticket_price?.toFixed(2)}</p>
                        </div>
                        <span className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white font-bold rounded-lg transition-colors flex items-center gap-2">
                            Participă <ArrowRight className="w-4 h-4" />
                        </span>
                    </div>
                </div>
            </div>
        </Link>
    );
};

// Competition Card - Grid cu Progress Bar
const CompCard = ({ c }) => {
    const progress = (c.sold_tickets / c.max_tickets) * 100;
    const remaining = c.max_tickets - c.sold_tickets;
    
    return (
        <Link to={`/competitions/${c.competition_id}`} className="group block bg-[#12111a] rounded-xl overflow-hidden border border-white/5 hover:border-violet-500/30 transition-all">
            <div className="relative aspect-[4/3]">
                <img src={c.image_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80'} alt={c.title} className="w-full h-full object-cover" loading="lazy" />
                <div className="absolute top-2 left-2">
                    <span className="px-2 py-0.5 bg-violet-600 text-white text-[10px] font-bold rounded">AUTODRAW</span>
                </div>
                <div className="absolute bottom-2 left-2">
                    <span className="px-2 py-1 bg-violet-600 text-white text-xs font-bold rounded">RON {c.ticket_price?.toFixed(2)}</span>
                </div>
            </div>
            <div className="p-3">
                <h3 className="font-bold text-white text-sm mb-2 truncate">{c.title}</h3>
                {/* Progress Bar */}
                <div className="mb-2">
                    <div className="flex justify-between text-[10px] mb-1">
                        <span className="text-gray-500">{progress.toFixed(0)}%</span>
                        <span className="text-gray-500">{remaining.toLocaleString()} libere</span>
                    </div>
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-violet-500 to-orange-500 rounded-full" style={{width: `${Math.max(progress, 3)}%`}} />
                    </div>
                </div>
            </div>
        </Link>
    );
};

// Stats Card
const StatCard = ({ icon: Icon, label, value, color }) => (
    <div className="flex items-center gap-3 p-3 bg-[#12111a] rounded-xl border border-white/5">
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}>
            <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-lg font-bold text-white">{value}</p>
        </div>
    </div>
);

const HomePage = () => {
    const { isRomanian } = useLanguage();
    const [comps, setComps] = useState([]);
    const [tiktokLive, setTiktokLive] = useState({ is_live: false, tiktok_url: 'https://www.tiktok.com/@zektrix.uk' });
    const [stats, setStats] = useState({ winners: 0, users: 0, tickets: 0 });
    const [activities, setActivities] = useState([]);

    useEffect(() => {
        axios.get(`${API}/competitions?status=active`).then(r => setComps(r.data)).catch(() => {});
        axios.get(`${API}/settings/tiktok-live`).then(r => setTiktokLive(r.data)).catch(() => {});
        axios.get(`${API}/stats`).then(r => setStats(r.data)).catch(() => {});
        axios.get(`${API}/activity/recent`).then(r => setActivities(r.data)).catch(() => {});
    }, []);

    // Find permanent/special competition and featured car competition
    const specialComp = comps.find(c => c.is_permanent || c.title?.includes('Specială'));
    const carComp = comps.find(c => (c.category === 'cars' || c.category === 'auto') && c.competition_id !== specialComp?.competition_id) || comps.find(c => c.competition_id !== specialComp?.competition_id);
    const otherComps = comps.filter(c => c.competition_id !== specialComp?.competition_id && c.competition_id !== carComp?.competition_id);

    return (
        <div className="min-h-screen bg-[#0a0614]">
            <Navbar />
            
            {/* Activity Ticker */}
            <div className="pt-16">
                <ActivityTicker activities={activities} competitions={comps} />
            </div>
            
            <main className="pb-8">
                {/* Hero Section */}
                <section className="py-8 md:py-12">
                    <div className="max-w-7xl mx-auto px-4">
                        <div className="grid lg:grid-cols-2 gap-6 items-stretch">
                            {/* LEFT - Competiția Specială */}
                            <SpecialCompCard c={specialComp} />
                            
                            {/* RIGHT - Car Competition */}
                            <FeaturedCard c={carComp} />
                        </div>
                    </div>
                </section>

                {/* Stats & Social */}
                <section className="py-4">
                    <div className="max-w-7xl mx-auto px-4">
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                            <StatCard icon={Trophy} label="Câștigători" value={stats.winners || 0} color="bg-yellow-500" />
                            <StatCard icon={Users} label="Utilizatori" value={stats.users || 0} color="bg-violet-500" />
                            <StatCard icon={Ticket} label="Locuri Rezervate" value={stats.tickets || 0} color="bg-orange-500" />
                            
                            {/* WhatsApp */}
                            <a href="https://wa.me/40730268067" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 p-3 bg-[#12111a] rounded-xl border border-white/5 hover:border-green-500/30 transition-colors">
                                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
                                    <MessageCircle className="w-5 h-5 text-white"/>
                                </div>
                                <div>
                                    <p className="text-[9px] text-gray-500">COMUNITATE</p>
                                    <p className="text-white text-xs font-semibold">WhatsApp</p>
                                </div>
                            </a>
                            
                            {/* TikTok */}
                            <a 
                                href={tiktokLive.tiktok_url} 
                                target="_blank" 
                                rel="noopener noreferrer" 
                                className={`flex items-center gap-2 p-3 bg-[#12111a] rounded-xl border transition-all relative overflow-hidden ${
                                    tiktokLive.is_live ? 'border-red-500/50 shadow-lg shadow-red-500/20' : 'border-white/5 hover:border-pink-500/30'
                                }`}
                            >
                                {tiktokLive.is_live && <div className="absolute inset-0 bg-gradient-to-r from-red-500/10 to-pink-500/10 animate-pulse" />}
                                <div className={`relative w-10 h-10 rounded-lg flex items-center justify-center ${
                                    tiktokLive.is_live ? 'bg-gradient-to-br from-red-500 to-pink-500 animate-pulse' : 'bg-gradient-to-br from-[#25F4EE] via-[#FE2C55] to-[#000000]'
                                }`}>
                                    {tiktokLive.is_live ? <Radio className="w-5 h-5 text-white" /> : <TikTokIcon />}
                                </div>
                                <div className="relative">
                                    {tiktokLive.is_live ? (
                                        <>
                                            <div className="flex items-center gap-1">
                                                <span className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                                                <p className="text-[9px] text-red-400 font-bold">LIVE ACUM</p>
                                            </div>
                                            <p className="text-white text-xs font-bold">Urmărește!</p>
                                        </>
                                    ) : (
                                        <>
                                            <p className="text-[9px] text-gray-500">URMĂREȘTE</p>
                                            <p className="text-white text-xs font-semibold">TikTok</p>
                                        </>
                                    )}
                                </div>
                            </a>
                        </div>
                    </div>
                </section>

                {/* Other Competitions */}
                <section className="py-6">
                    <div className="max-w-7xl mx-auto px-4">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-black text-white">Alte Competiții</h2>
                            <Link to="/competitions" className="text-violet-400 text-sm font-medium flex items-center gap-1 hover:text-violet-300">
                                Vezi toate <ChevronRight className="w-4 h-4" />
                            </Link>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {otherComps.slice(0, 8).map(c => <CompCard key={c.competition_id} c={c} />)}
                        </div>
                    </div>
                </section>
            </main>
            <Footer />
            <InstallPrompt />
            <CookieConsent />
        </div>
    );
};

export default HomePage;
