import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Badge } from '../components/ui/badge';
import { Loader2, Zap, Monitor, Banknote, Car, Sparkles, Filter, ArrowRight, Ticket, Trophy } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Modern Competition Card
const CompCard = ({ comp, featured = false }) => {
    const progress = (comp.sold_tickets / comp.max_tickets) * 100;
    const remaining = comp.max_tickets - comp.sold_tickets;
    
    return (
        <Link to={`/competitions/${comp.competition_id}`} 
            className={`group block rounded-2xl overflow-hidden transition-all duration-500 hover:scale-[1.02] ${featured ? 'h-full' : ''}`}
            style={{
                background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.95) 0%, rgba(10, 6, 20, 0.98) 100%)',
                border: '1px solid rgba(139, 92, 246, 0.15)',
                boxShadow: featured ? '0 0 40px rgba(139, 92, 246, 0.1)' : 'none'
            }}
            data-testid={`comp-${comp.competition_id}`}
        >
            <div className={`relative ${featured ? 'aspect-[16/10]' : 'aspect-[4/3]'}`}>
                <img 
                    src={comp.image_url || 'https://images.unsplash.com/photo-1621981386829-9b458a2cddde?w=800&q=80'} 
                    alt={comp.title} 
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" 
                    loading="lazy" 
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                
                {/* Badges */}
                <div className="absolute top-3 left-3 flex gap-2">
                    <span className="px-2.5 py-1 bg-violet-600 text-white text-[10px] font-bold rounded-lg shadow-lg">
                        AUTODRAW
                    </span>
                    {comp.is_flash_sale && (
                        <span className="px-2.5 py-1 bg-orange-500 text-white text-[10px] font-bold rounded-lg shadow-lg flex items-center gap-1">
                            <Zap className="w-3 h-3" /> FLASH
                        </span>
                    )}
                </div>
                
                {/* Price Badge */}
                <div className="absolute bottom-3 left-3">
                    <span className="px-3 py-1.5 text-white text-sm font-bold rounded-lg"
                        style={{ background: 'linear-gradient(135deg, #8b5cf6, #f97316)' }}>
                        DE LA RON {comp.ticket_price?.toFixed(2)}
                    </span>
                </div>

                {/* Progress on hover */}
                <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="px-2 py-1 bg-black/70 text-white text-xs font-bold rounded-lg">
                        {progress.toFixed(0)}% vândut
                    </span>
                </div>
            </div>
            
            <div className="p-4">
                <h3 className="font-bold text-white text-lg mb-2 group-hover:text-violet-400 transition-colors line-clamp-2">
                    {comp.title}
                </h3>
                
                {/* Progress Bar */}
                <div className="mb-3">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>Vândute: {comp.sold_tickets}</span>
                        <span>Libere: {remaining}</span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                        <div 
                            className="h-full rounded-full transition-all duration-700"
                            style={{ 
                                width: `${progress}%`, 
                                background: progress > 75 
                                    ? 'linear-gradient(90deg, #ef4444, #f97316, #fbbf24)' 
                                    : 'linear-gradient(90deg, #8b5cf6, #06b6d4)',
                                boxShadow: progress > 75 ? '0 0 10px rgba(239, 68, 68, 0.5)' : '0 0 10px rgba(139, 92, 246, 0.5)'
                            }} 
                        />
                    </div>
                </div>
                
                <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500 capitalize">{comp.category || 'General'}</span>
                    <span className="px-4 py-2 rounded-lg text-white text-xs font-bold transition-all duration-300 group-hover:shadow-lg"
                        style={{ 
                            background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
                            boxShadow: '0 0 15px rgba(139, 92, 246, 0.3)'
                        }}>
                        Participă <ArrowRight className="w-3 h-3 inline ml-1" />
                    </span>
                </div>
            </div>
        </Link>
    );
};

const CompetitionsPage = () => {
    const { isRomanian } = useLanguage();
    const [competitions, setCompetitions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeFilter, setActiveFilter] = useState('all');

    useEffect(() => {
        fetchCompetitions();
    }, []);

    const fetchCompetitions = async () => {
        try {
            const response = await axios.get(`${API}/competitions`);
            setCompetitions(response.data);
        } catch (error) {
            console.error('Failed to fetch competitions:', error);
        } finally {
            setLoading(false);
        }
    };

    const categories = [
        { id: 'all', label: isRomanian ? 'Toate' : 'All', icon: Sparkles },
        { id: 'instant_wins', label: isRomanian ? 'Instant' : 'Instant', icon: Zap },
        { id: 'cash', label: isRomanian ? 'Cash' : 'Cash', icon: Banknote },
        { id: 'tech', label: isRomanian ? 'Tech' : 'Tech', icon: Monitor },
        { id: 'cars', label: isRomanian ? 'Auto' : 'Cars', icon: Car },
    ];

    const filteredCompetitions = useMemo(() => {
        if (activeFilter === 'all') return competitions;
        if (activeFilter === 'instant_wins') {
            return competitions.filter(c => c.competition_type === 'instant_win');
        }
        return competitions.filter(c => c.category === activeFilter);
    }, [competitions, activeFilter]);

    const featuredCompetition = filteredCompetitions[0];
    const regularCompetitions = filteredCompetitions.slice(1);

    return (
        <div className="min-h-screen bg-[#030014]" data-testid="competitions-page">
            <Navbar />

            <main className="pt-24 pb-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="text-center mb-10">
                        <Badge className="mb-6 px-4 py-2 text-sm font-bold"
                            style={{
                                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(124, 58, 237, 0.15) 100%)',
                                border: '1px solid rgba(139, 92, 246, 0.4)',
                                color: '#a78bfa'
                            }}>
                            <Sparkles className="w-4 h-4 mr-2" />
                            {isRomanian ? 'Competiții Active' : 'Live Competitions'}
                        </Badge>
                        <h1 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight mb-4">
                            <span className="text-white">{isRomanian ? 'Descoperă ' : 'Discover '}</span>
                            <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-orange-400 bg-clip-text text-transparent">
                                {isRomanian ? 'Premii Incredibile' : 'Amazing Prizes'}
                            </span>
                        </h1>
                        <p className="text-gray-400 max-w-2xl mx-auto text-lg">
                            {isRomanian 
                                ? 'Alege competiția ta și intră în cursa pentru premii extraordinare!'
                                : 'Choose your competition and enter the race for extraordinary prizes!'
                            }
                        </p>
                    </div>

                    {/* Category Filters */}
                    <div className="flex flex-wrap gap-2 justify-center mb-10">
                        {categories.map((cat) => (
                            <button
                                key={cat.id}
                                onClick={() => setActiveFilter(cat.id)}
                                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-300"
                                style={{
                                    background: activeFilter === cat.id 
                                        ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(124, 58, 237, 0.2) 100%)'
                                        : 'rgba(255,255,255,0.05)',
                                    border: activeFilter === cat.id 
                                        ? '1px solid rgba(139, 92, 246, 0.5)'
                                        : '1px solid rgba(255,255,255,0.1)',
                                    color: activeFilter === cat.id ? '#a78bfa' : '#9ca3af',
                                    boxShadow: activeFilter === cat.id ? '0 0 20px rgba(139, 92, 246, 0.3)' : 'none'
                                }}
                                data-testid={`filter-${cat.id}`}
                            >
                                <cat.icon className="w-4 h-4" />
                                {cat.label}
                            </button>
                        ))}
                    </div>

                    {/* Loading State */}
                    {loading ? (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-10 h-10 animate-spin text-violet-500" />
                        </div>
                    ) : filteredCompetitions.length === 0 ? (
                        <div className="text-center py-20">
                            <div className="w-20 h-20 rounded-2xl mx-auto mb-6 flex items-center justify-center"
                                style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(124, 58, 237, 0.15))', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
                                <Filter className="w-10 h-10 text-violet-400" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">
                                {isRomanian ? 'Nicio competiție găsită' : 'No competitions found'}
                            </h3>
                            <p className="text-gray-500">
                                {isRomanian ? 'Încearcă alt filtru' : 'Try another filter'}
                            </p>
                        </div>
                    ) : (
                        <>
                            {/* Grid Layout */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                                {/* Featured Competition */}
                                {featuredCompetition && (
                                    <div className="md:col-span-2 lg:col-span-2">
                                        <CompCard comp={featuredCompetition} featured />
                                    </div>
                                )}
                                
                                {/* Regular Competitions */}
                                {regularCompetitions.map((comp) => (
                                    <CompCard key={comp.competition_id} comp={comp} />
                                ))}
                            </div>

                            {/* Stats Bar */}
                            <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-3">
                                {[
                                    { icon: Trophy, value: competitions.filter(c => c.status === 'active').length, label: isRomanian ? 'Competiții Active' : 'Active', color: '#8b5cf6' },
                                    { icon: Ticket, value: competitions.reduce((sum, c) => sum + c.sold_tickets, 0), label: isRomanian ? 'Locuri Vândute' : 'Spots Sold', color: '#06b6d4' },
                                    { icon: Banknote, value: `RON ${Math.min(...competitions.filter(c => c.status === 'active').map(c => c.ticket_price) || [0]).toFixed(0)}`, label: isRomanian ? 'Preț Minim' : 'From', color: '#10b981' },
                                    { icon: Zap, value: competitions.filter(c => c.competition_type === 'instant_win').length, label: isRomanian ? 'Instant Wins' : 'Instant Wins', color: '#f97316' },
                                ].map((stat, i) => (
                                    <div key={i} className="rounded-xl p-4 text-center"
                                        style={{
                                            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                            border: '1px solid rgba(139, 92, 246, 0.15)'
                                        }}>
                                        <stat.icon className="w-5 h-5 mx-auto mb-2" style={{ color: stat.color }} />
                                        <p className="text-2xl font-bold text-white">{stat.value}</p>
                                        <p className="text-xs text-gray-500">{stat.label}</p>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default CompetitionsPage;
