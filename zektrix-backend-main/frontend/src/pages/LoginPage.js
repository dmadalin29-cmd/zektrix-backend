import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Loader2, Mail, Lock, Eye, EyeOff, Phone, User, ArrowLeft, Sparkles, Shield, Trophy, Gift } from 'lucide-react';

const LoginPage = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { login, register, loginWithGoogle, isAuthenticated } = useAuth();
    const { isRomanian } = useLanguage();
    const [loading, setLoading] = useState(false);
    const [googleLoading, setGoogleLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('login');
    const [showPassword, setShowPassword] = useState(false);

    // Login form
    const [loginEmail, setLoginEmail] = useState('');
    const [loginPassword, setLoginPassword] = useState('');

    // Register form
    const [regFirstName, setRegFirstName] = useState('');
    const [regLastName, setRegLastName] = useState('');
    const [regPhone, setRegPhone] = useState('');
    const [regUsername, setRegUsername] = useState('');
    const [regEmail, setRegEmail] = useState('');
    const [regPassword, setRegPassword] = useState('');
    const [regConfirmPassword, setRegConfirmPassword] = useState('');

    const from = location.state?.from?.pathname || '/dashboard';

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) {
            navigate(from, { replace: true });
        }
    }, [isAuthenticated, navigate, from]);

    // Handle Google OAuth callback
    useEffect(() => {
        const processGoogleCallback = async () => {
            // Check BOTH query params and hash for session_id
            const searchParams = new URLSearchParams(window.location.search);
            const hashParams = new URLSearchParams(window.location.hash.replace('#', ''));
            const sessionId = searchParams.get('session_id') || hashParams.get('session_id');
            
            if (sessionId) {
                setGoogleLoading(true);
                try {
                    const userData = await loginWithGoogle(sessionId);
                    // Clear the URL params
                    window.history.replaceState(null, '', window.location.pathname);
                    
                    // Check if user needs to add phone number
                    if (!userData.phone) {
                        navigate('/complete-profile', { state: { from: from } });
                    } else {
                        toast.success(isRomanian ? 'Bine ai venit!' : 'Welcome!');
                        navigate(from, { replace: true });
                    }
                } catch (error) {
                    console.error('Google login error:', error);
                    toast.error(isRomanian ? 'Autentificare eșuată' : 'Authentication failed');
                    window.history.replaceState(null, '', window.location.pathname);
                } finally {
                    setGoogleLoading(false);
                }
            }
        };
        
        processGoogleCallback();
    }, [loginWithGoogle, navigate, from, isRomanian]);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await login(loginEmail, loginPassword);
            toast.success(isRomanian ? 'Bine ai revenit!' : 'Welcome back!');
            navigate(from, { replace: true });
        } catch (error) {
            toast.error(error.response?.data?.detail || (isRomanian ? 'Autentificare eșuată' : 'Login failed'));
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        if (!regFirstName || !regLastName || !regPhone) {
            toast.error(isRomanian ? 'Te rugăm să completezi toate câmpurile' : 'Please fill in all fields');
            return;
        }
        if (regPassword !== regConfirmPassword) {
            toast.error(isRomanian ? 'Parolele nu se potrivesc' : 'Passwords do not match');
            return;
        }
        if (regPassword.length < 6) {
            toast.error(isRomanian ? 'Parola trebuie să aibă minim 6 caractere' : 'Password must be at least 6 characters');
            return;
        }
        setLoading(true);
        try {
            await register(regUsername, regEmail, regPassword, regFirstName, regLastName, regPhone);
            toast.success(isRomanian ? 'Cont creat cu succes!' : 'Account created successfully!');
            navigate(from, { replace: true });
        } catch (error) {
            toast.error(error.response?.data?.detail || (isRomanian ? 'Înregistrare eșuată' : 'Registration failed'));
        } finally {
            setLoading(false);
        }
    };

    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const handleGoogleLogin = () => {
        const redirectUrl = window.location.origin + '/login';
        window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    };

    // Show loading while processing Google callback
    if (googleLoading) {
        return (
            <div className="min-h-screen bg-[#030014] flex items-center justify-center">
                <div className="text-center">
                    <div className="relative w-20 h-20 mx-auto mb-6">
                        <div className="absolute inset-0 rounded-full border-4 border-violet-500/20"></div>
                        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-violet-500 animate-spin"></div>
                        <Sparkles className="absolute inset-0 m-auto w-8 h-8 text-violet-400 animate-pulse" />
                    </div>
                    <p className="text-white font-medium">{isRomanian ? 'Se procesează autentificarea...' : 'Processing authentication...'}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#030014] flex" data-testid="login-page">
            {/* Left Side - Branding & Features */}
            <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
                {/* Animated Background */}
                <div className="absolute inset-0">
                    <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-violet-600/20 via-transparent to-orange-500/20" />
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-500/30 rounded-full blur-[120px] animate-pulse" />
                    <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-orange-500/20 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '1s' }} />
                    <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-cyan-500/20 rounded-full blur-[80px] animate-pulse" style={{ animationDelay: '2s' }} />
                </div>

                {/* Content */}
                <div className="relative z-10 flex flex-col justify-center px-12 xl:px-20">
                    {/* Logo */}
                    <Link to="/" className="mb-12">
                        <h1 className="text-5xl font-black tracking-tighter">
                            <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-orange-400 bg-clip-text text-transparent animate-gradient">ZEKTRIX</span>
                            <span className="text-white">.UK</span>
                        </h1>
                    </Link>

                    {/* Tagline */}
                    <h2 className="text-4xl xl:text-5xl font-bold text-white mb-6 leading-tight">
                        {isRomanian ? (
                            <>Câștigă premii<br /><span className="bg-gradient-to-r from-violet-400 to-orange-400 bg-clip-text text-transparent">extraordinare</span></>
                        ) : (
                            <>Win amazing<br /><span className="bg-gradient-to-r from-violet-400 to-orange-400 bg-clip-text text-transparent">prizes</span></>
                        )}
                    </h2>

                    <p className="text-gray-400 text-lg mb-12 max-w-md">
                        {isRomanian 
                            ? 'Participă la competiții exclusive și ai șansa de a câștiga mașini, bani cash și multe alte premii incredibile.'
                            : 'Enter exclusive competitions and have the chance to win cars, cash, and many other incredible prizes.'
                        }
                    </p>

                    {/* Features */}
                    <div className="space-y-6">
                        <div className="flex items-center gap-4 group">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500/20 to-violet-500/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                                <Trophy className="w-6 h-6 text-violet-400" />
                            </div>
                            <div>
                                <h3 className="text-white font-semibold">{isRomanian ? 'Premii Reale' : 'Real Prizes'}</h3>
                                <p className="text-gray-500 text-sm">{isRomanian ? 'Tesla, iPhone, Cash și multe altele' : 'Tesla, iPhone, Cash and more'}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-4 group">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500/20 to-orange-500/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                                <Shield className="w-6 h-6 text-orange-400" />
                            </div>
                            <div>
                                <h3 className="text-white font-semibold">{isRomanian ? '100% Sigur' : '100% Secure'}</h3>
                                <p className="text-gray-500 text-sm">{isRomanian ? 'Plăți securizate cu Viva Payments' : 'Secure payments via Viva Payments'}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-4 group">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-cyan-500/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                                <Gift className="w-6 h-6 text-cyan-400" />
                            </div>
                            <div>
                                <h3 className="text-white font-semibold">{isRomanian ? 'Extrageri Live' : 'Live Draws'}</h3>
                                <p className="text-gray-500 text-sm">{isRomanian ? 'Transparență totală în alegerea câștigătorilor' : 'Total transparency in selecting winners'}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Decorative elements */}
                <div className="absolute bottom-10 left-12 text-gray-600 text-sm">
                    © 2026 Zektrix UK. {isRomanian ? 'Toate drepturile rezervate.' : 'All rights reserved.'}
                </div>
            </div>

            {/* Right Side - Auth Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12">
                <div className="w-full max-w-md">
                    {/* Mobile Logo */}
                    <div className="lg:hidden text-center mb-8">
                        <Link to="/">
                            <h1 className="text-3xl font-black tracking-tighter inline-block">
                                <span className="bg-gradient-to-r from-violet-400 to-orange-400 bg-clip-text text-transparent">ZEKTRIX</span>
                                <span className="text-white">.UK</span>
                            </h1>
                        </Link>
                    </div>

                    {/* Back Button - Mobile */}
                    <Link to="/" className="lg:hidden inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-6">
                        <ArrowLeft className="w-4 h-4" />
                        <span>{isRomanian ? 'Înapoi' : 'Back'}</span>
                    </Link>

                    {/* Auth Card */}
                    <div className="rounded-3xl p-8 relative overflow-hidden"
                        style={{
                            background: 'linear-gradient(135deg, rgba(20, 15, 40, 0.95) 0%, rgba(10, 6, 20, 0.98) 100%)',
                            border: '1px solid rgba(139, 92, 246, 0.15)',
                            boxShadow: '0 0 60px rgba(139, 92, 246, 0.08), inset 0 1px 0 rgba(255,255,255,0.05)'
                        }}>
                        
                        {/* Glow effect */}
                        <div className="absolute -top-20 -right-20 w-40 h-40 bg-violet-500/10 rounded-full blur-3xl" />
                        
                        {/* Tab Switcher */}
                        <div className="flex gap-1 mb-8 p-1.5 rounded-2xl bg-white/5 relative z-10">
                            <button
                                onClick={() => setActiveTab('login')}
                                className={`flex-1 py-3.5 px-6 rounded-xl text-sm font-bold transition-all duration-500 ${
                                    activeTab === 'login' ? 'text-white shadow-lg' : 'text-gray-400 hover:text-white'
                                }`}
                                style={activeTab === 'login' ? {
                                    background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6d28d9 100%)',
                                    boxShadow: '0 4px 20px rgba(139, 92, 246, 0.5), 0 0 40px rgba(139, 92, 246, 0.2)'
                                } : {}}
                            >
                                {isRomanian ? 'Conectare' : 'Login'}
                            </button>
                            <button
                                onClick={() => setActiveTab('register')}
                                className={`flex-1 py-3.5 px-6 rounded-xl text-sm font-bold transition-all duration-500 ${
                                    activeTab === 'register' ? 'text-white shadow-lg' : 'text-gray-400 hover:text-white'
                                }`}
                                style={activeTab === 'register' ? {
                                    background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6d28d9 100%)',
                                    boxShadow: '0 4px 20px rgba(139, 92, 246, 0.5), 0 0 40px rgba(139, 92, 246, 0.2)'
                                } : {}}
                            >
                                {isRomanian ? 'Înregistrare' : 'Register'}
                            </button>
                        </div>

                        {/* Login Form */}
                        {activeTab === 'login' && (
                            <form onSubmit={handleLogin} className="space-y-5 relative z-10">
                                <div className="text-center mb-8">
                                    <h2 className="text-2xl font-bold text-white mb-2">{isRomanian ? 'Bine ai revenit!' : 'Welcome back!'}</h2>
                                    <p className="text-gray-500">{isRomanian ? 'Conectează-te pentru a continua' : 'Sign in to continue'}</p>
                                </div>

                                {/* Google Login Button */}
                                <Button
                                    type="button"
                                    onClick={handleGoogleLogin}
                                    className="w-full h-14 rounded-xl font-bold text-base transition-all duration-300 hover:scale-[1.02]"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
                                    }}
                                >
                                    <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                                    </svg>
                                    {isRomanian ? 'Continuă cu Google' : 'Continue with Google'}
                                </Button>

                                <div className="relative my-6">
                                    <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/10" /></div>
                                    <div className="relative flex justify-center text-xs">
                                        <span className="px-4 text-gray-500" style={{ background: 'linear-gradient(135deg, rgba(20, 15, 40, 0.95), rgba(10, 6, 20, 0.98))' }}>
                                            {isRomanian ? 'sau cu email' : 'or with email'}
                                        </span>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-gray-400 text-sm font-medium">Email</Label>
                                    <div className="relative group">
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500 group-focus-within:text-violet-400 transition-colors" />
                                        <Input
                                            type="email"
                                            value={loginEmail}
                                            onChange={(e) => setLoginEmail(e.target.value)}
                                            placeholder="email@exemplu.com"
                                            className="pl-12 h-14 rounded-xl bg-white/5 border-white/10 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 text-white placeholder:text-gray-600"
                                            required
                                            data-testid="login-email"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-gray-400 text-sm font-medium">{isRomanian ? 'Parolă' : 'Password'}</Label>
                                    <div className="relative group">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500 group-focus-within:text-violet-400 transition-colors" />
                                        <Input
                                            type={showPassword ? 'text' : 'password'}
                                            value={loginPassword}
                                            onChange={(e) => setLoginPassword(e.target.value)}
                                            placeholder="••••••••"
                                            className="pl-12 pr-12 h-14 rounded-xl bg-white/5 border-white/10 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 text-white placeholder:text-gray-600"
                                            required
                                            data-testid="login-password"
                                        />
                                        <button 
                                            type="button" 
                                            onClick={() => setShowPassword(!showPassword)} 
                                            className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
                                        >
                                            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                        </button>
                                    </div>
                                </div>

                                <Button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full h-14 rounded-xl text-base font-bold transition-all duration-300 hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
                                    style={{ 
                                        background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6d28d9 100%)', 
                                        boxShadow: '0 4px 20px rgba(139, 92, 246, 0.5), 0 0 40px rgba(139, 92, 246, 0.2)' 
                                    }}
                                    data-testid="login-submit"
                                >
                                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (isRomanian ? 'Conectare' : 'Sign In')}
                                </Button>
                            </form>
                        )}

                        {/* Register Form */}
                        {activeTab === 'register' && (
                            <form onSubmit={handleRegister} className="space-y-4 relative z-10">
                                <div className="text-center mb-6">
                                    <h2 className="text-2xl font-bold text-white mb-2">{isRomanian ? 'Creează cont' : 'Create account'}</h2>
                                    <p className="text-gray-500">{isRomanian ? 'Înregistrează-te pentru a participa' : 'Register to participate'}</p>
                                </div>

                                {/* Google Register Button */}
                                <Button
                                    type="button"
                                    onClick={handleGoogleLogin}
                                    className="w-full h-12 rounded-xl font-bold transition-all duration-300 hover:scale-[1.02]"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
                                        border: '1px solid rgba(255,255,255,0.1)'
                                    }}
                                >
                                    <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                                    </svg>
                                    {isRomanian ? 'Înregistrare cu Google' : 'Register with Google'}
                                </Button>

                                <div className="relative my-4">
                                    <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/10" /></div>
                                    <div className="relative flex justify-center text-xs">
                                        <span className="px-4 text-gray-500" style={{ background: 'linear-gradient(135deg, rgba(20, 15, 40, 0.95), rgba(10, 6, 20, 0.98))' }}>
                                            {isRomanian ? 'sau completează' : 'or fill in'}
                                        </span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-3">
                                    <div className="space-y-1.5">
                                        <Label className="text-gray-400 text-xs font-medium">{isRomanian ? 'Prenume' : 'First Name'} *</Label>
                                        <div className="relative">
                                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                            <Input
                                                value={regFirstName}
                                                onChange={(e) => setRegFirstName(e.target.value)}
                                                placeholder="Ion"
                                                className="pl-10 h-11 rounded-lg bg-white/5 border-white/10 focus:border-violet-500 text-white text-sm"
                                                required
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-gray-400 text-xs font-medium">{isRomanian ? 'Nume' : 'Last Name'} *</Label>
                                        <Input
                                            value={regLastName}
                                            onChange={(e) => setRegLastName(e.target.value)}
                                            placeholder="Popescu"
                                            className="h-11 rounded-lg bg-white/5 border-white/10 focus:border-violet-500 text-white text-sm"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1.5">
                                    <Label className="text-gray-400 text-xs font-medium">{isRomanian ? 'Telefon' : 'Phone'} *</Label>
                                    <div className="relative">
                                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <Input
                                            value={regPhone}
                                            onChange={(e) => setRegPhone(e.target.value)}
                                            placeholder="+40 712 345 678"
                                            className="pl-10 h-11 rounded-lg bg-white/5 border-white/10 focus:border-violet-500 text-white text-sm"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-1.5">
                                    <Label className="text-gray-400 text-xs font-medium">{isRomanian ? 'Nume utilizator' : 'Username'}</Label>
                                    <Input
                                        value={regUsername}
                                        onChange={(e) => setRegUsername(e.target.value)}
                                        placeholder="ion_popescu"
                                        className="h-11 rounded-lg bg-white/5 border-white/10 focus:border-violet-500 text-white text-sm"
                                    />
                                </div>

                                <div className="space-y-1.5">
                                    <Label className="text-gray-400 text-xs font-medium">Email *</Label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <Input
                                            type="email"
                                            value={regEmail}
                                            onChange={(e) => setRegEmail(e.target.value)}
                                            placeholder="email@exemplu.com"
                                            className="pl-10 h-11 rounded-lg bg-white/5 border-white/10 focus:border-violet-500 text-white text-sm"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-3">
                                    <div className="space-y-1.5">
                                        <Label className="text-gray-400 text-xs font-medium">{isRomanian ? 'Parolă' : 'Password'} *</Label>
                                        <div className="relative">
                                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                            <Input
                                                type={showPassword ? 'text' : 'password'}
                                                value={regPassword}
                                                onChange={(e) => setRegPassword(e.target.value)}
                                                placeholder="••••••"
                                                className="pl-10 h-11 rounded-lg bg-white/5 border-white/10 focus:border-violet-500 text-white text-sm"
                                                required
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-gray-400 text-xs font-medium">{isRomanian ? 'Confirmă' : 'Confirm'} *</Label>
                                        <Input
                                            type={showPassword ? 'text' : 'password'}
                                            value={regConfirmPassword}
                                            onChange={(e) => setRegConfirmPassword(e.target.value)}
                                            placeholder="••••••"
                                            className="h-11 rounded-lg bg-white/5 border-white/10 focus:border-violet-500 text-white text-sm"
                                            required
                                        />
                                    </div>
                                </div>

                                <Button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full h-12 rounded-xl text-base font-bold mt-4 transition-all duration-300 hover:scale-[1.02]"
                                    style={{ 
                                        background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)', 
                                        boxShadow: '0 4px 20px rgba(139, 92, 246, 0.4)' 
                                    }}
                                >
                                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (isRomanian ? 'Creează Cont' : 'Create Account')}
                                </Button>
                            </form>
                        )}

                        {/* Terms */}
                        <p className="text-center text-xs text-gray-600 mt-6 relative z-10">
                            {isRomanian ? 'Prin continuare, ești de acord cu ' : 'By continuing, you agree to our '}
                            <Link to="/terms" className="text-violet-400 hover:underline">{isRomanian ? 'Termenii' : 'Terms'}</Link>
                            {isRomanian ? ' și ' : ' and '}
                            <Link to="/privacy" className="text-violet-400 hover:underline">{isRomanian ? 'Politica de Confidențialitate' : 'Privacy Policy'}</Link>
                        </p>
                    </div>

                    {/* Back to home - Desktop */}
                    <div className="hidden lg:block text-center mt-8">
                        <Link to="/" className="inline-flex items-center gap-2 text-gray-500 hover:text-white transition-colors">
                            <ArrowLeft className="w-4 h-4" />
                            <span>{isRomanian ? 'Înapoi la pagina principală' : 'Back to home'}</span>
                        </Link>
                    </div>
                </div>
            </div>

            {/* CSS for gradient animation */}
            <style>{`
                @keyframes gradient {
                    0%, 100% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                }
                .animate-gradient {
                    background-size: 200% 200%;
                    animation: gradient 3s ease infinite;
                }
            `}</style>
        </div>
    );
};

export default LoginPage;
