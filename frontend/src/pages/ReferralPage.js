import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';
import { Copy, Users, Gift, Share2, CheckCircle, Clock, Twitter, Facebook, MessageCircle, Loader2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ReferralPage = () => {
    const { user, token } = useAuth();
    const { t, isRomanian } = useLanguage();
    const [referralData, setReferralData] = useState(null);
    const [referrals, setReferrals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [applyCode, setApplyCode] = useState('');
    const [applying, setApplying] = useState(false);

    useEffect(() => {
        if (token) {
            fetchReferralData();
        }
    }, [token]);

    const fetchReferralData = async () => {
        try {
            const [codeRes, referralsRes] = await Promise.all([
                axios.get(`${API}/referral/my-code`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API}/referral/my-referrals`, { headers: { Authorization: `Bearer ${token}` } })
            ]);
            setReferralData(codeRes.data);
            setReferrals(referralsRes.data);
        } catch (error) {
            console.error('Failed to fetch referral data:', error);
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        toast.success(isRomanian ? 'Copiat în clipboard!' : 'Copied to clipboard!');
    };

    const handleApplyCode = async () => {
        if (!applyCode.trim()) {
            toast.error(isRomanian ? 'Introdu un cod de referral' : 'Enter a referral code');
            return;
        }
        setApplying(true);
        try {
            await axios.post(`${API}/referral/apply`, 
                { referrer_code: applyCode },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            toast.success(isRomanian ? 'Cod aplicat cu succes!' : 'Code applied successfully!');
            setApplyCode('');
            fetchReferralData();
        } catch (error) {
            toast.error(error.response?.data?.detail || (isRomanian ? 'Cod invalid' : 'Invalid code'));
        } finally {
            setApplying(false);
        }
    };

    const shareOnTwitter = () => {
        const text = isRomanian 
            ? `🎉 Înscrie-te la Zektrix UK și primești RON 5 bonus! Folosește codul meu: ${referralData?.referral_code}`
            : `🎉 Join Zektrix UK and get RON 5 bonus! Use my code: ${referralData?.referral_code}`;
        window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(referralData?.referral_link)}`, '_blank');
    };

    const shareOnFacebook = () => {
        window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(referralData?.referral_link)}`, '_blank');
    };

    const shareOnWhatsApp = () => {
        const text = isRomanian 
            ? `🎉 Înscrie-te la Zektrix UK și primești RON 5 bonus! ${referralData?.referral_link} - Codul meu: ${referralData?.referral_code}`
            : `🎉 Join Zektrix UK and get RON 5 bonus! ${referralData?.referral_link} - My code: ${referralData?.referral_code}`;
        window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-background">
                <Navbar />
                <main className="pt-24 pb-16 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            <Navbar />
            
            <main className="pt-24 pb-16">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="text-center mb-12">
                        <Badge className="mb-4 bg-secondary/20 text-secondary border-secondary/30">
                            <Gift className="w-3 h-3 mr-1" /> {isRomanian ? 'Program Referral' : 'Referral Program'}
                        </Badge>
                        <h1 className="text-4xl md:text-5xl font-black tracking-tighter mb-4">
                            {isRomanian ? 'Invită ' : 'Invite '} 
                            <span className="gradient-text">{isRomanian ? 'Prieteni' : 'Friends'}</span>
                            {isRomanian ? ' & Primește Bonus' : ' & Get Bonus'}
                        </h1>
                        <p className="text-muted-foreground max-w-xl mx-auto">
                            {isRomanian 
                                ? 'Primește RON 5 pentru fiecare prieten care se înregistrează și face prima achiziție. Prietenul tău primește și el RON 5!'
                                : 'Get RON 5 for every friend who signs up and makes their first purchase. Your friend gets RON 5 too!'
                            }
                        </p>
                    </div>

                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <Card className="glass border-white/10">
                            <CardContent className="p-6 text-center">
                                <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-3">
                                    <Users className="w-6 h-6 text-primary" />
                                </div>
                                <p className="text-3xl font-bold">{referralData?.total_referrals || 0}</p>
                                <p className="text-sm text-muted-foreground">
                                    {isRomanian ? 'Total Referrals' : 'Total Referrals'}
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="glass border-white/10">
                            <CardContent className="p-6 text-center">
                                <div className="w-12 h-12 rounded-full bg-secondary/20 flex items-center justify-center mx-auto mb-3">
                                    <CheckCircle className="w-6 h-6 text-secondary" />
                                </div>
                                <p className="text-3xl font-bold">{referralData?.completed_referrals || 0}</p>
                                <p className="text-sm text-muted-foreground">
                                    {isRomanian ? 'Completate' : 'Completed'}
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="glass border-secondary/30">
                            <CardContent className="p-6 text-center">
                                <div className="w-12 h-12 rounded-full bg-secondary/20 flex items-center justify-center mx-auto mb-3">
                                    <Gift className="w-6 h-6 text-secondary" />
                                </div>
                                <p className="text-3xl font-bold text-secondary">RON {referralData?.total_earned || 0}</p>
                                <p className="text-sm text-muted-foreground">
                                    {isRomanian ? 'Total Primit' : 'Total Earned'}
                                </p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Referral Code Card */}
                    <Card className="glass border-primary/30 mb-8">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Share2 className="w-5 h-5 text-primary" />
                                {isRomanian ? 'Codul Tău de Referral' : 'Your Referral Code'}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex gap-4 items-center">
                                <div className="flex-1 bg-muted/50 rounded-xl p-4 text-center">
                                    <p className="text-3xl font-mono font-bold tracking-widest text-primary">
                                        {referralData?.referral_code}
                                    </p>
                                </div>
                                <Button 
                                    variant="outline" 
                                    className="border-primary/30 hover:bg-primary/20"
                                    onClick={() => copyToClipboard(referralData?.referral_code)}
                                >
                                    <Copy className="w-4 h-4 mr-2" />
                                    {isRomanian ? 'Copiază' : 'Copy'}
                                </Button>
                            </div>
                            
                            <div className="flex gap-4 items-center">
                                <Input 
                                    value={referralData?.referral_link || ''} 
                                    readOnly 
                                    className="input-modern text-sm"
                                />
                                <Button 
                                    variant="outline" 
                                    className="border-primary/30 hover:bg-primary/20"
                                    onClick={() => copyToClipboard(referralData?.referral_link)}
                                >
                                    <Copy className="w-4 h-4" />
                                </Button>
                            </div>

                            {/* Social Share Buttons */}
                            <div className="flex gap-3 justify-center pt-4">
                                <Button onClick={shareOnTwitter} className="bg-[#1DA1F2] hover:bg-[#1DA1F2]/80">
                                    <Twitter className="w-4 h-4 mr-2" />
                                    Twitter
                                </Button>
                                <Button onClick={shareOnFacebook} className="bg-[#4267B2] hover:bg-[#4267B2]/80">
                                    <Facebook className="w-4 h-4 mr-2" />
                                    Facebook
                                </Button>
                                <Button onClick={shareOnWhatsApp} className="bg-[#25D366] hover:bg-[#25D366]/80">
                                    <MessageCircle className="w-4 h-4 mr-2" />
                                    WhatsApp
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Apply Code Card */}
                    <Card className="glass border-white/10 mb-8">
                        <CardHeader>
                            <CardTitle>{isRomanian ? 'Ai un Cod de Referral?' : 'Have a Referral Code?'}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex gap-4">
                                <Input 
                                    placeholder={isRomanian ? 'Introdu codul...' : 'Enter code...'}
                                    value={applyCode}
                                    onChange={(e) => setApplyCode(e.target.value.toUpperCase())}
                                    className="input-modern"
                                />
                                <Button 
                                    onClick={handleApplyCode}
                                    disabled={applying}
                                    className="btn-secondary"
                                >
                                    {applying ? <Loader2 className="w-4 h-4 animate-spin" /> : (isRomanian ? 'Aplică' : 'Apply')}
                                </Button>
                            </div>
                            <p className="text-sm text-muted-foreground mt-2">
                                {isRomanian 
                                    ? 'Aplică un cod înainte de prima ta achiziție pentru a primi RON 5 bonus!'
                                    : 'Apply a code before your first purchase to get RON 5 bonus!'
                                }
                            </p>
                        </CardContent>
                    </Card>

                    {/* Referrals List */}
                    {referrals.length > 0 && (
                        <Card className="glass border-white/10">
                            <CardHeader>
                                <CardTitle>{isRomanian ? 'Referralurile Tale' : 'Your Referrals'}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {referrals.map((ref) => (
                                        <div 
                                            key={ref.referral_id} 
                                            className="flex items-center justify-between p-4 bg-muted/30 rounded-xl"
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                                                    ref.status === 'completed' ? 'bg-secondary/20' : 'bg-muted'
                                                }`}>
                                                    {ref.status === 'completed' 
                                                        ? <CheckCircle className="w-5 h-5 text-secondary" />
                                                        : <Clock className="w-5 h-5 text-muted-foreground" />
                                                    }
                                                </div>
                                                <div>
                                                    <p className="font-medium">{ref.referred_username}</p>
                                                    <p className="text-sm text-muted-foreground">
                                                        {new Date(ref.created_at).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            </div>
                                            <Badge className={ref.status === 'completed' ? 'badge-secondary' : 'badge-muted'}>
                                                {ref.status === 'completed' 
                                                    ? (isRomanian ? 'Completat' : 'Completed')
                                                    : (isRomanian ? 'În așteptare' : 'Pending')
                                                }
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* How it Works */}
                    <Card className="glass border-white/10 mt-8">
                        <CardHeader>
                            <CardTitle>{isRomanian ? 'Cum Funcționează' : 'How It Works'}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="text-center">
                                    <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-3">
                                        <span className="text-xl font-bold text-primary">1</span>
                                    </div>
                                    <h4 className="font-bold mb-2">{isRomanian ? 'Distribuie Codul' : 'Share Your Code'}</h4>
                                    <p className="text-sm text-muted-foreground">
                                        {isRomanian 
                                            ? 'Trimite codul tău de referral prietenilor'
                                            : 'Send your referral code to friends'
                                        }
                                    </p>
                                </div>
                                <div className="text-center">
                                    <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-3">
                                        <span className="text-xl font-bold text-primary">2</span>
                                    </div>
                                    <h4 className="font-bold mb-2">{isRomanian ? 'Se Înscriu' : 'They Sign Up'}</h4>
                                    <p className="text-sm text-muted-foreground">
                                        {isRomanian 
                                            ? 'Prietenii se înregistrează și fac prima achiziție'
                                            : 'Friends register and make first purchase'
                                        }
                                    </p>
                                </div>
                                <div className="text-center">
                                    <div className="w-12 h-12 rounded-full bg-secondary/20 flex items-center justify-center mx-auto mb-3">
                                        <span className="text-xl font-bold text-secondary">3</span>
                                    </div>
                                    <h4 className="font-bold mb-2">{isRomanian ? 'Primiți Amândoi' : 'Both Earn'}</h4>
                                    <p className="text-sm text-muted-foreground">
                                        {isRomanian 
                                            ? 'Tu și prietenul primești RON 5 bonus!'
                                            : 'You and friend each get RON 5 bonus!'
                                        }
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default ReferralPage;
