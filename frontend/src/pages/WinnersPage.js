import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Badge } from '../components/ui/badge';
import axios from 'axios';
import { Trophy, Loader2, Zap, Clock, Star, Crown, Sparkles, Calendar, Ticket, Award } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const WinnersPage = () => {
    const { t, isRomanian } = useLanguage();
    const [winners, setWinners] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchWinners();
    }, []);

    const fetchWinners = async () => {
        try {
            const response = await axios.get(`${API}/winners`);
            setWinners(response.data);
        } catch (error) {
            console.error('Failed to fetch winners:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#030014]" data-testid="winners-page">
            <Navbar />
            
            <main className="pt-24 pb-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="text-center mb-12">
                        <Badge className="mb-6 px-4 py-2 text-sm font-bold"
                            style={{
                                background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2) 0%, rgba(249, 115, 22, 0.15) 100%)',
                                border: '1px solid rgba(251, 191, 36, 0.4)',
                                color: '#fbbf24'
                            }}>
                            <Crown className="w-4 h-4 mr-2" /> {t('verified_winners')}
                        </Badge>
                        <h1 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight mb-4">
                            <span className="text-white">{isRomanian ? 'Câștigătorii ' : 'Our '}</span>
                            <span className="bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
                                {isRomanian ? 'Noștri' : 'Winners'}
                            </span>
                        </h1>
                        <p className="text-gray-400 max-w-2xl mx-auto text-lg">
                            {t('winners_subtitle')}
                        </p>
                    </div>

                    {/* Stats Bar */}
                    <div className="grid grid-cols-3 gap-4 mb-12 max-w-2xl mx-auto">
                        <div className="rounded-xl p-4 text-center"
                            style={{ background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(249, 115, 22, 0.05) 100%)', border: '1px solid rgba(251, 191, 36, 0.2)' }}>
                            <Trophy className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
                            <p className="text-2xl font-bold text-white">{winners.length}</p>
                            <p className="text-xs text-gray-500">{isRomanian ? 'Total Câștigători' : 'Total Winners'}</p>
                        </div>
                        <div className="rounded-xl p-4 text-center"
                            style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%)', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
                            <Zap className="w-6 h-6 text-violet-400 mx-auto mb-2" />
                            <p className="text-2xl font-bold text-white">{winners.filter(w => w.is_automatic).length}</p>
                            <p className="text-xs text-gray-500">{isRomanian ? 'Instant Wins' : 'Instant Wins'}</p>
                        </div>
                        <div className="rounded-xl p-4 text-center"
                            style={{ background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(8, 145, 178, 0.05) 100%)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                            <Award className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
                            <p className="text-2xl font-bold text-white">{winners.filter(w => !w.is_automatic).length}</p>
                            <p className="text-xs text-gray-500">{isRomanian ? 'Live Draws' : 'Live Draws'}</p>
                        </div>
                    </div>

                    {loading ? (
                        <div className="flex items-center justify-center py-16">
                            <Loader2 className="w-10 h-10 animate-spin text-violet-500" />
                        </div>
                    ) : winners.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                            {winners.map((winner, index) => (
                                <div 
                                    key={winner.winner_id} 
                                    className="group rounded-2xl p-6 transition-all duration-500 hover:scale-[1.02]"
                                    style={{
                                        background: index === 0 
                                            ? 'linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(249, 115, 22, 0.1) 100%)'
                                            : 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                        border: index === 0 
                                            ? '1px solid rgba(251, 191, 36, 0.4)'
                                            : '1px solid rgba(139, 92, 246, 0.15)',
                                        boxShadow: index === 0 ? '0 0 40px rgba(251, 191, 36, 0.15)' : 'none'
                                    }}
                                    data-testid={`winner-${winner.winner_id}`}
                                >
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
                                            style={{ 
                                                background: index === 0 
                                                    ? 'linear-gradient(135deg, #fbbf24, #f97316)' 
                                                    : 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
                                                boxShadow: `0 0 20px ${index === 0 ? 'rgba(251, 191, 36, 0.4)' : 'rgba(139, 92, 246, 0.3)'}`
                                            }}>
                                            <Trophy className="w-7 h-7 text-white" />
                                        </div>
                                        <Badge className={`text-xs font-bold px-3 py-1 ${winner.is_automatic 
                                            ? 'bg-violet-500/20 text-violet-400 border-violet-500/30' 
                                            : 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'}`}>
                                            {winner.is_automatic ? (
                                                <><Zap className="w-3 h-3 mr-1" /> Instant</>
                                            ) : (
                                                <><Clock className="w-3 h-3 mr-1" /> Live Draw</>
                                            )}
                                        </Badge>
                                    </div>
                                    
                                    <h3 className="text-xl font-bold text-white mb-1">{winner.username}</h3>
                                    <p className="text-gray-400 text-sm mb-4">{winner.competition_title}</p>
                                    
                                    <div className="flex items-center justify-between pt-4 border-t border-white/10">
                                        <div className="flex items-center gap-2">
                                            <Ticket className="w-4 h-4 text-violet-400" />
                                            <div>
                                                <p className="text-[10px] text-gray-500 uppercase">{t('winning_ticket')}</p>
                                                <p className="text-lg font-bold text-violet-400">#{winner.ticket_number}</p>
                                            </div>
                                        </div>
                                        <div className="text-right flex items-center gap-2">
                                            <div>
                                                <p className="text-[10px] text-gray-500 uppercase">{t('won_on')}</p>
                                                <p className="text-sm font-medium text-white">
                                                    {new Date(winner.announced_at).toLocaleDateString('ro-RO', {
                                                        day: 'numeric',
                                                        month: 'short'
                                                    })}
                                                </p>
                                            </div>
                                            <Calendar className="w-4 h-4 text-gray-500" />
                                        </div>
                                    </div>

                                    {winner.prize_description && (
                                        <div className="mt-4 p-3 rounded-xl"
                                            style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                                            <p className="text-[10px] text-emerald-400 uppercase mb-1">{t('prize_won')}</p>
                                            <p className="font-semibold text-white">{winner.prize_description}</p>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-16">
                            <div className="w-20 h-20 rounded-2xl mx-auto mb-6 flex items-center justify-center"
                                style={{ background: 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(249, 115, 22, 0.15))', border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                                <Trophy className="w-10 h-10 text-yellow-400" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">{t('no_winners')}</h3>
                            <p className="text-gray-500">{t('no_winners_desc')}</p>
                        </div>
                    )}

                    {/* Trust Section */}
                    <div className="mt-16 rounded-2xl p-8 text-center max-w-2xl mx-auto"
                        style={{
                            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                            border: '1px solid rgba(139, 92, 246, 0.15)'
                        }}>
                        <div className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center"
                            style={{ background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)' }}>
                            <Sparkles className="w-7 h-7 text-white" />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-3">{t('verified_transparent')}</h3>
                        <p className="text-gray-400">
                            {t('verified_desc')}
                        </p>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default WinnersPage;
