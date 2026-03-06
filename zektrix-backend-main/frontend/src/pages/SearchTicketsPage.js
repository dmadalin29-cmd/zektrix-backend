import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';
import { Search, Ticket, Loader2, User, ArrowRight, ArrowLeft, Trophy, Hash } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SearchTicketsPage = () => {
    const { t, isRomanian } = useLanguage();
    const [username, setUsername] = useState('');
    const [searching, setSearching] = useState(false);
    const [result, setResult] = useState(null);
    const [searched, setSearched] = useState(false);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!username.trim()) {
            toast.error(t('enter_username'));
            return;
        }

        setSearching(true);
        setSearched(true);
        try {
            const response = await axios.get(`${API}/tickets/search?username=${encodeURIComponent(username)}`);
            setResult(response.data);
        } catch (error) {
            if (error.response?.status === 404) {
                setResult(null);
                toast.error(t('user_not_found'));
            } else {
                toast.error('Search failed');
            }
        } finally {
            setSearching(false);
        }
    };

    const groupedTickets = result?.tickets?.reduce((acc, ticket) => {
        const key = ticket.competition_id;
        if (!acc[key]) {
            acc[key] = { competition_id: ticket.competition_id, competition_title: ticket.competition_title, tickets: [] };
        }
        acc[key].tickets.push(ticket);
        return acc;
    }, {}) || {};

    return (
        <div className="min-h-screen bg-[#030014]" data-testid="search-tickets-page">
            <Navbar />
            
            <main className="pt-24 pb-16">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Back */}
                    <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-8">
                        <ArrowLeft className="w-4 h-4" />
                        <span>{isRomanian ? 'Înapoi' : 'Back'}</span>
                    </Link>

                    {/* Header */}
                    <div className="text-center mb-10">
                        <Badge className="mb-6 px-4 py-2 text-sm font-bold"
                            style={{
                                background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(8, 145, 178, 0.15) 100%)',
                                border: '1px solid rgba(6, 182, 212, 0.4)',
                                color: '#06b6d4'
                            }}>
                            <Search className="w-4 h-4 mr-2" /> {t('public_search')}
                        </Badge>
                        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">
                            <span className="text-white">{isRomanian ? 'Caută ' : 'Find '}</span>
                            <span className="bg-gradient-to-r from-cyan-400 to-violet-500 bg-clip-text text-transparent">
                                {isRomanian ? 'Locuri' : 'Spots'}
                            </span>
                        </h1>
                        <p className="text-gray-400 max-w-xl mx-auto">
                            {t('search_subtitle')}
                        </p>
                    </div>

                    {/* Search Form */}
                    <div className="rounded-2xl p-6 mb-8"
                        style={{
                            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.95) 0%, rgba(10, 6, 20, 0.98) 100%)',
                            border: '1px solid rgba(139, 92, 246, 0.2)'
                        }}>
                        <form onSubmit={handleSearch} className="flex gap-3">
                            <div className="relative flex-1">
                                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-violet-400 z-10" />
                                <Input
                                    type="text"
                                    placeholder={isRomanian ? "Introdu username sau email" : "Enter username or email"}
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="pl-12 h-14 text-lg bg-white/5 border-white/10 rounded-xl focus:border-violet-500"
                                    data-testid="search-username-input"
                                />
                            </div>
                            <Button 
                                type="submit" 
                                className="h-14 px-8 font-bold"
                                style={{ background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)', boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)' }}
                                disabled={searching}
                                data-testid="search-btn"
                            >
                                {searching ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Search className="w-5 h-5 mr-2" /> {t('search')}</>}
                            </Button>
                        </form>
                    </div>

                    {/* Results */}
                    {searching ? (
                        <div className="flex justify-center py-12">
                            <Loader2 className="w-10 h-10 animate-spin text-violet-500" />
                        </div>
                    ) : result ? (
                        <div className="space-y-6">
                            {/* User Info */}
                            <div className="rounded-2xl p-6"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(8, 145, 178, 0.05) 100%)',
                                    border: '1px solid rgba(6, 182, 212, 0.3)'
                                }}>
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
                                        style={{ background: 'linear-gradient(135deg, #06b6d4, #8b5cf6)' }}>
                                        <User className="w-7 h-7 text-white" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold text-white">{result.username}</h2>
                                        <p className="text-gray-400">
                                            {result.tickets.length} {isRomanian ? 'locuri în' : 'spots in'} {Object.keys(groupedTickets).length} {isRomanian ? 'competiții' : 'competitions'}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Tickets */}
                            {Object.keys(groupedTickets).length > 0 ? (
                                <div className="grid md:grid-cols-2 gap-4">
                                    {Object.values(groupedTickets).map((group) => (
                                        <div key={group.competition_id} 
                                            className="rounded-2xl p-5 transition-all duration-300 hover:scale-[1.01]"
                                            style={{
                                                background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.95) 0%, rgba(10, 6, 20, 0.98) 100%)',
                                                border: '1px solid rgba(139, 92, 246, 0.15)'
                                            }}
                                            data-testid={`search-result-${group.competition_id}`}
                                        >
                                            <div className="flex items-center justify-between mb-4">
                                                <h3 className="font-bold text-white">{group.competition_title || 'Competition'}</h3>
                                                <Badge className="bg-violet-500/20 text-violet-400 border-violet-500/30">
                                                    {group.tickets.length} {isRomanian ? 'locuri' : 'spots'}
                                                </Badge>
                                            </div>
                                            <div className="flex flex-wrap gap-2 mb-4">
                                                {group.tickets.sort((a, b) => a.ticket_number - b.ticket_number).map((ticket) => (
                                                    <span key={ticket.ticket_id} 
                                                        className="px-3 py-1.5 rounded-lg font-mono font-bold text-sm text-white"
                                                        style={{ background: 'linear-gradient(135deg, #8b5cf6, #f97316)', boxShadow: '0 0 10px rgba(139, 92, 246, 0.3)' }}>
                                                        #{ticket.ticket_number}
                                                    </span>
                                                ))}
                                            </div>
                                            <Link to={`/competitions/${group.competition_id}`}>
                                                <Button variant="ghost" size="sm" className="text-violet-400 hover:text-violet-300 p-0">
                                                    {t('view_competition')} <ArrowRight className="w-4 h-4 ml-1" />
                                                </Button>
                                            </Link>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="rounded-2xl p-8 text-center"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.95) 0%, rgba(10, 6, 20, 0.98) 100%)',
                                        border: '1px solid rgba(139, 92, 246, 0.15)'
                                    }}>
                                    <Ticket className="w-12 h-12 mx-auto text-gray-600 mb-4" />
                                    <p className="text-gray-500">{t('no_tickets_purchased')}</p>
                                </div>
                            )}
                        </div>
                    ) : searched ? (
                        <div className="rounded-2xl p-8 text-center"
                            style={{
                                background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.95) 0%, rgba(10, 6, 20, 0.98) 100%)',
                                border: '1px solid rgba(139, 92, 246, 0.15)'
                            }}>
                            <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center bg-gray-800">
                                <User className="w-8 h-8 text-gray-500" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">{t('user_not_found')}</h3>
                            <p className="text-gray-500">{t('user_not_found_desc')}</p>
                        </div>
                    ) : null}

                    {/* Info */}
                    <div className="mt-8 grid md:grid-cols-3 gap-3">
                        {[
                            { icon: Search, title: isRomanian ? 'Public' : 'Public', desc: isRomanian ? 'Verifică orice utilizator' : 'Check any user' },
                            { icon: Hash, title: isRomanian ? 'Transparent' : 'Transparent', desc: isRomanian ? 'Locuri vizibile' : 'Visible spots' },
                            { icon: Trophy, title: isRomanian ? 'Verificat' : 'Verified', desc: isRomanian ? 'Date în timp real' : 'Real-time data' }
                        ].map((item, i) => (
                            <div key={i} className="rounded-xl p-4 bg-white/5 border border-white/5 text-center">
                                <item.icon className="w-5 h-5 text-violet-400 mx-auto mb-2" />
                                <h4 className="font-medium text-white text-sm">{item.title}</h4>
                                <p className="text-xs text-gray-500">{item.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default SearchTicketsPage;
