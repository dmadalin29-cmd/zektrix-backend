import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';
import { motion } from 'framer-motion';
import {
    Gift, Copy, Share2, Users, CheckCircle2, Clock, Crown,
    Sparkles, User, Save, Edit3, ArrowRight, Ticket, RefreshCw,
    Trophy, Star, ChevronRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ReferralPage() {
    const { user, token, isAuthenticated } = useAuth();
    const { isRomanian } = useLanguage();
    const headers = { Authorization: `Bearer ${token}` };

    const [referralData, setReferralData] = useState(null);
    const [leaderboard, setLeaderboard] = useState([]);
    const [loading, setLoading] = useState(true);
    const [customCode, setCustomCode] = useState('');
    const [editingCode, setEditingCode] = useState(false);
    const [saving, setSaving] = useState(false);

    const fetchAll = useCallback(async () => {
        if (!token) { setLoading(false); return; }
        setLoading(true);
        try {
            const [refRes, lbRes] = await Promise.all([
                axios.get(`${API}/referral/my`, { headers }),
                axios.get(`${API}/referral/leaderboard`)
            ]);
            setReferralData(refRes.data);
            setCustomCode(refRes.data.referral_code || '');
            setLeaderboard(lbRes.data || []);
        } catch (e) { console.error(e); }
        setLoading(false);
    }, [token]);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    const handleCustomize = async () => {
        if (!customCode.trim()) return;
        setSaving(true);
        try {
            const { data } = await axios.post(`${API}/referral/customize`, { code: customCode }, { headers });
            setReferralData(p => ({ ...p, referral_code: data.referral_code, referral_link: data.referral_link }));
            setEditingCode(false);
            toast.success(isRomanian ? 'Cod actualizat!' : 'Code updated!');
        } catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
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

    if (loading) {
        return (
            <div className="min-h-screen"><Navbar />
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="w-8 h-8 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen" data-testid="referral-page">
            <Navbar />
            <div className="max-w-4xl mx-auto px-4 pt-24 pb-20">
                {/* Hero */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#8B3DFF]/10 border border-[#8B3DFF]/20 mb-4">
                        <Gift className="w-4 h-4 text-[#A666FF]" />
                        <span className="text-sm text-[#A666FF] font-medium">{isRomanian ? 'Program Referral' : 'Referral Program'}</span>
                    </div>
                    <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white mb-4 tracking-tight">
                        {isRomanian ? 'Invita ' : 'Invite '}
                        <span className="bg-gradient-to-r from-[#A666FF] via-[#FF5E00] to-[#A666FF] bg-clip-text text-transparent">
                            {isRomanian ? 'Prieteni' : 'Friends'}
                        </span>
                        {isRomanian ? ' & Castiga' : ' & Earn'}
                    </h1>
                    <p className="text-[#A39EBD] max-w-lg mx-auto text-base">
                        {isRomanian
                            ? 'Tu primesti £3 credit, prietenul tau primeste £2 cand face prima achizitie!'
                            : 'You get £3 credit, your friend gets £2 when they make their first purchase!'}
                    </p>
                </motion.div>

                {isAuthenticated ? (
                    <div className="space-y-6">
                        {/* Stats */}
                        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                            className="grid grid-cols-3 gap-4">
                            {[
                                { icon: Users, label: isRomanian ? 'Invitati' : 'Invited', value: referralData?.total_invited || 0, iconClass: 'text-violet-400', valueClass: 'text-white' },
                                { icon: CheckCircle2, label: isRomanian ? 'Finalizati' : 'Completed', value: referralData?.total_completed || 0, iconClass: 'text-emerald-400', valueClass: 'text-emerald-400' },
                                { icon: Sparkles, label: isRomanian ? 'Castigat' : 'Earned', value: `£${(referralData?.total_earnings || 0).toFixed(2)}`, iconClass: 'text-amber-400', valueClass: 'text-amber-400' },
                            ].map((s, i) => {
                                const Icon = s.icon;
                                return (
                                    <div key={i} className="p-5 rounded-2xl text-center bg-white/[0.03] backdrop-blur-xl border border-white/[0.06] hover:border-white/[0.12] transition-all">
                                        <Icon className={`w-6 h-6 ${s.iconClass} mx-auto mb-2`} />
                                        <p className={`text-2xl font-black ${s.valueClass}`}>{s.value}</p>
                                        <p className="text-xs text-[#6E6987] mt-1">{s.label}</p>
                                    </div>
                                );
                            })}
                        </motion.div>

                        {/* Referral Code Card */}
                        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                            className="relative overflow-hidden rounded-3xl p-6" style={{
                                background: 'linear-gradient(135deg, rgba(139,92,246,0.12) 0%, rgba(249,115,22,0.08) 50%, rgba(139,92,246,0.06) 100%)',
                                border: '1px solid rgba(139,92,246,0.2)'
                            }}>
                            <div className="absolute top-0 right-0 w-48 h-48 bg-violet-500/5 rounded-full blur-3xl" />
                            <div className="relative">
                                <p className="text-sm text-[#A39EBD] mb-2 flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-[#A666FF]" />
                                    {isRomanian ? 'Codul Tau de Referral' : 'Your Referral Code'}
                                </p>
                                {editingCode ? (
                                    <div className="flex gap-2 mb-4">
                                        <Input value={customCode} onChange={e => setCustomCode(e.target.value.toUpperCase())}
                                            className="bg-white/[0.06] border-white/[0.1] text-white font-mono text-xl h-12 uppercase tracking-widest"
                                            maxLength={15} placeholder="CODTAU" data-testid="custom-code-input" />
                                        <Button onClick={handleCustomize} disabled={saving}
                                            className="bg-[#8B3DFF] hover:bg-[#A666FF] text-white h-12 px-5" data-testid="save-code-btn">
                                            {saving ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
                                        </Button>
                                        <Button onClick={() => { setEditingCode(false); setCustomCode(referralData?.referral_code || ''); }}
                                            variant="ghost" className="text-gray-400 h-12">
                                            {isRomanian ? 'Anuleaza' : 'Cancel'}
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-between mb-4">
                                        <span className="text-3xl sm:text-4xl font-mono font-black text-[#A666FF] tracking-[0.15em]" data-testid="referral-code-display">
                                            {referralData?.referral_code || 'ZEKTRIX'}
                                        </span>
                                        <Button onClick={() => setEditingCode(true)} variant="ghost" className="text-[#6E6987] hover:text-white gap-1.5" data-testid="edit-code-btn">
                                            <Edit3 className="w-4 h-4" /> {isRomanian ? 'Personalizeaza' : 'Customize'}
                                        </Button>
                                    </div>
                                )}

                                <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06] mb-4">
                                    <p className="text-xs text-[#6E6987] mb-1">Link</p>
                                    <p className="text-sm text-white font-mono truncate">{referralData?.referral_link}</p>
                                </div>

                                <div className="grid grid-cols-2 gap-3">
                                    <Button onClick={copyLink} className="bg-[#8B3DFF] hover:bg-[#A666FF] text-white rounded-xl gap-2 h-12 text-base" data-testid="copy-ref-link">
                                        <Copy className="w-5 h-5" /> {isRomanian ? 'Copiaza Link' : 'Copy Link'}
                                    </Button>
                                    <Button onClick={shareWhatsApp} className="bg-[#25D366] hover:bg-[#22c55e] text-white rounded-xl gap-2 h-12 text-base" data-testid="share-whatsapp">
                                        <Share2 className="w-5 h-5" /> WhatsApp
                                    </Button>
                                </div>
                            </div>
                        </motion.div>

                        {/* How it Works */}
                        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
                            className="rounded-2xl p-6" style={{
                                background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                                border: '1px solid rgba(139,92,246,0.1)'
                            }}>
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-[#A666FF]" /> {isRomanian ? 'Cum Functioneaza?' : 'How It Works?'}
                            </h3>
                            <div className="grid sm:grid-cols-3 gap-4">
                                {[
                                    { icon: Share2, step: '1', title: isRomanian ? 'Trimite Link-ul' : 'Share Your Link', desc: isRomanian ? 'Trimite link-ul tau prietenilor pe WhatsApp, TikTok sau orice retea sociala' : 'Share with friends via WhatsApp, TikTok or any social network' },
                                    { icon: User, step: '2', title: isRomanian ? 'Prietenul se Inscrie' : 'Friend Signs Up', desc: isRomanian ? 'Prietenul se inregistreaza pe Zektrix cu link-ul tau de referral' : 'Your friend registers on Zektrix with your referral link' },
                                    { icon: Gift, step: '3', title: isRomanian ? 'Ambii Castigati!' : 'Both Win!', desc: isRomanian ? 'Cand prietenul cumpara primul bilet: tu primesti £3, el £2 in wallet!' : 'When friend buys first ticket: you get £3, they get £2 in wallet!' },
                                ].map((s, i) => {
                                    const Icon = s.icon;
                                    return (
                                        <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                                            <div className="flex items-center gap-2 mb-2">
                                                <div className="w-8 h-8 rounded-lg bg-[#8B3DFF]/15 flex items-center justify-center">
                                                    <Icon className="w-4 h-4 text-[#A666FF]" />
                                                </div>
                                                <span className="text-xs font-bold text-[#8B3DFF]">{isRomanian ? 'PASUL' : 'STEP'} {s.step}</span>
                                            </div>
                                            <h4 className="text-sm font-bold text-white mb-1">{s.title}</h4>
                                            <p className="text-xs text-[#6E6987] leading-relaxed">{s.desc}</p>
                                        </div>
                                    );
                                })}
                            </div>
                        </motion.div>

                        {/* Invited Friends */}
                        {referralData?.invited_list?.length > 0 && (
                            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
                                className="rounded-2xl overflow-hidden" style={{
                                    background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                                    border: '1px solid rgba(139,92,246,0.1)'
                                }}>
                                <div className="p-5 border-b border-white/[0.06] flex items-center justify-between">
                                    <h3 className="text-white font-bold flex items-center gap-2"><Users className="w-5 h-5 text-[#A666FF]" /> {isRomanian ? 'Prieteni Invitati' : 'Invited Friends'}</h3>
                                    <span className="text-xs text-[#6E6987]">{referralData.invited_list.length} total</span>
                                </div>
                                <div className="divide-y divide-white/[0.04]">
                                    {referralData.invited_list.map((f, i) => (
                                        <div key={i} className="flex items-center gap-3 p-4 hover:bg-white/[0.02] transition-colors">
                                            <div className="w-10 h-10 rounded-xl bg-white/[0.04] flex items-center justify-center">
                                                <User className="w-5 h-5 text-gray-400" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-white font-medium">{f.username}</p>
                                                <p className="text-xs text-[#6E6987]">{new Date(f.created_at).toLocaleDateString('ro-RO', {day:'2-digit', month:'short', year:'numeric'})}</p>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                {f.status === 'completed' ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Clock className="w-4 h-4 text-amber-400" />}
                                                <span className={`text-xs font-medium ${f.status === 'completed' ? 'text-emerald-400' : 'text-amber-400'}`}>
                                                    {f.status === 'completed' ? (isRomanian ? 'Finalizat (+£3)' : 'Completed (+£3)') : (isRomanian ? 'In asteptare' : 'Pending')}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {/* Leaderboard */}
                        {leaderboard.length > 0 && (
                            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
                                className="rounded-2xl overflow-hidden" style={{
                                    background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                                    border: '1px solid rgba(139,92,246,0.1)'
                                }}>
                                <div className="p-5 border-b border-white/[0.06]">
                                    <h3 className="text-white font-bold flex items-center gap-2"><Crown className="w-5 h-5 text-amber-400" /> {isRomanian ? 'Top Invitatii' : 'Referral Leaderboard'}</h3>
                                </div>
                                <div className="divide-y divide-white/[0.04]">
                                    {leaderboard.map((entry, i) => (
                                        <div key={i} className="flex items-center gap-3 p-4 hover:bg-white/[0.02] transition-colors">
                                            <span className={`w-9 h-9 rounded-xl flex items-center justify-center text-sm font-black ${
                                                i === 0 ? 'bg-gradient-to-br from-amber-500 to-amber-600 text-black' :
                                                i === 1 ? 'bg-gradient-to-br from-gray-300 to-gray-400 text-black' :
                                                i === 2 ? 'bg-gradient-to-br from-orange-500 to-orange-600 text-black' :
                                                'bg-white/[0.06] text-[#6E6987]'
                                            }`}>{entry.rank}</span>
                                            <div className="flex-1">
                                                <p className="text-sm text-white font-semibold">{entry.username}</p>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <Trophy className="w-4 h-4 text-[#A666FF]" />
                                                <span className="text-sm font-bold text-[#A666FF]">{entry.referrals}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        )}
                    </div>
                ) : (
                    /* Not logged in */
                    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
                        className="text-center p-10 rounded-3xl" style={{
                            background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                            border: '1px solid rgba(139,92,246,0.15)'
                        }}>
                        <div className="w-20 h-20 rounded-3xl mx-auto mb-6 flex items-center justify-center bg-gradient-to-br from-[#8B3DFF] to-[#FF5E00] shadow-[0_0_30px_rgba(139,61,255,0.3)]">
                            <Gift className="w-10 h-10 text-white" />
                        </div>
                        <h2 className="text-2xl font-black text-white mb-3">{isRomanian ? 'Inregistreaza-te pentru a primi codul tau' : 'Sign up to get your code'}</h2>
                        <p className="text-[#A39EBD] mb-6 max-w-md mx-auto">
                            {isRomanian ? 'Creaza un cont gratuit si incepe sa castigi bani invitand prieteni!' : 'Create a free account and start earning by inviting friends!'}
                        </p>
                        <a href="/login">
                            <Button className="bg-[#8B3DFF] hover:bg-[#A666FF] text-white rounded-xl gap-2 h-12 px-8 text-base">
                                <ArrowRight className="w-5 h-5" /> {isRomanian ? 'Inregistreaza-te' : 'Sign Up'}
                            </Button>
                        </a>
                    </motion.div>
                )}
            </div>
            <Footer />
        </div>
    );
}
