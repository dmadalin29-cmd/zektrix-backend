import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Loader2, Phone, CheckCircle, Sparkles } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const CompleteProfilePage = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, token, refreshUser, isAuthenticated } = useAuth();
    const { isRomanian } = useLanguage();
    const [phone, setPhone] = useState('');
    const [loading, setLoading] = useState(false);

    const from = location.state?.from || '/dashboard';

    // Redirect if not authenticated or already has phone
    useEffect(() => {
        if (!isAuthenticated) {
            navigate('/login');
        } else if (user?.phone) {
            navigate(from, { replace: true });
        }
    }, [isAuthenticated, user, navigate, from]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!phone || phone.length < 10) {
            toast.error(isRomanian ? 'Te rugăm să introduci un număr de telefon valid' : 'Please enter a valid phone number');
            return;
        }

        setLoading(true);
        try {
            await axios.put(`${API}/auth/profile`, { phone }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            
            await refreshUser();
            toast.success(isRomanian ? 'Profil completat cu succes!' : 'Profile completed successfully!');
            navigate(from, { replace: true });
        } catch (error) {
            toast.error(error.response?.data?.detail || (isRomanian ? 'Eroare la salvare' : 'Save failed'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#030014] flex items-center justify-center p-4">
            {/* Background effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-500/20 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-orange-500/15 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '1s' }} />
            </div>

            <div className="w-full max-w-md relative z-10">
                {/* Logo */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-black tracking-tighter inline-block">
                        <span className="bg-gradient-to-r from-violet-400 to-orange-400 bg-clip-text text-transparent">ZEKTRIX</span>
                        <span className="text-white">.UK</span>
                    </h1>
                </div>

                {/* Card */}
                <div className="rounded-3xl p-8 relative overflow-hidden"
                    style={{
                        background: 'linear-gradient(135deg, rgba(20, 15, 40, 0.95) 0%, rgba(10, 6, 20, 0.98) 100%)',
                        border: '1px solid rgba(139, 92, 246, 0.15)',
                        boxShadow: '0 0 60px rgba(139, 92, 246, 0.08)'
                    }}>
                    
                    <div className="absolute -top-20 -right-20 w-40 h-40 bg-violet-500/10 rounded-full blur-3xl" />

                    <div className="relative z-10">
                        {/* Icon */}
                        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl flex items-center justify-center"
                            style={{
                                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(139, 92, 246, 0.05))',
                                boxShadow: '0 0 30px rgba(139, 92, 246, 0.2)'
                            }}>
                            <Sparkles className="w-10 h-10 text-violet-400" />
                        </div>

                        {/* Header */}
                        <div className="text-center mb-8">
                            <h2 className="text-2xl font-bold text-white mb-2">
                                {isRomanian ? 'Aproape gata!' : 'Almost done!'}
                            </h2>
                            <p className="text-gray-400">
                                {isRomanian 
                                    ? 'Mai avem nevoie de numărul tău de telefon pentru a-ți putea trimite notificări despre câștiguri.'
                                    : 'We just need your phone number to send you winning notifications.'
                                }
                            </p>
                        </div>

                        {/* User Info */}
                        {user && (
                            <div className="flex items-center gap-4 p-4 rounded-xl bg-white/5 mb-6">
                                {user.picture ? (
                                    <img src={user.picture} alt="" className="w-12 h-12 rounded-full" />
                                ) : (
                                    <div className="w-12 h-12 rounded-full bg-violet-500/20 flex items-center justify-center">
                                        <span className="text-violet-400 font-bold text-lg">
                                            {(user.first_name || user.name || user.email)?.[0]?.toUpperCase()}
                                        </span>
                                    </div>
                                )}
                                <div className="flex-1 min-w-0">
                                    <p className="text-white font-medium truncate">
                                        {user.first_name || user.name || 'Utilizator'}
                                    </p>
                                    <p className="text-gray-500 text-sm truncate flex items-center gap-1">
                                        <CheckCircle className="w-3 h-3 text-green-400" />
                                        {user.email}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Form */}
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="space-y-2">
                                <Label className="text-gray-400 text-sm font-medium">
                                    {isRomanian ? 'Număr de telefon' : 'Phone number'} *
                                </Label>
                                <div className="relative group">
                                    <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500 group-focus-within:text-violet-400 transition-colors" />
                                    <Input
                                        type="tel"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        placeholder="+40 712 345 678"
                                        className="pl-12 h-14 rounded-xl bg-white/5 border-white/10 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 text-white text-lg placeholder:text-gray-600"
                                        required
                                        autoFocus
                                    />
                                </div>
                                <p className="text-xs text-gray-600">
                                    {isRomanian 
                                        ? 'Vom folosi acest număr doar pentru notificări importante despre competiții și câștiguri.'
                                        : 'We will only use this number for important notifications about competitions and wins.'
                                    }
                                </p>
                            </div>

                            <Button
                                type="submit"
                                disabled={loading}
                                className="w-full h-14 rounded-xl text-base font-bold transition-all duration-300 hover:scale-[1.02] disabled:opacity-50"
                                style={{ 
                                    background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6d28d9 100%)', 
                                    boxShadow: '0 4px 20px rgba(139, 92, 246, 0.5)' 
                                }}
                            >
                                {loading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    isRomanian ? 'Finalizează Înregistrarea' : 'Complete Registration'
                                )}
                            </Button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CompleteProfilePage;
