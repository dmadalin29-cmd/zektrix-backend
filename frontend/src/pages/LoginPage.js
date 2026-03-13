import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Loader2, Mail, Lock, User, Trophy, ArrowLeft, Eye, EyeOff, Phone, UserCircle } from 'lucide-react';

const LoginPage = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { login, register, loginWithGoogle } = useAuth();
    const { t, isRomanian } = useLanguage();
    const [loading, setLoading] = useState(false);
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

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await login(loginEmail, loginPassword);
            toast.success(t('welcome') + '!');
            navigate(from, { replace: true });
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        if (!regFirstName || !regLastName || !regPhone) {
            toast.error('Te rugăm să completezi toate câmpurile');
            return;
        }
        if (regPassword !== regConfirmPassword) {
            toast.error('Parolele nu se potrivesc');
            return;
        }
        if (regPassword.length < 6) {
            toast.error('Parola trebuie să aibă minim 6 caractere');
            return;
        }
        setLoading(true);
        try {
            await register(regUsername, regEmail, regPassword, regFirstName, regLastName, regPhone);
            toast.success(t('success') + '!');
            navigate(from, { replace: true });
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Înregistrare eșuată');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#030014] flex items-center justify-center p-4" data-testid="login-page">
            {/* Background effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-[120px]" />
            </div>

            <div className="w-full max-w-md relative z-10">
                {/* Back Button */}
                <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-8">
                    <ArrowLeft className="w-4 h-4" />
                    <span>{isRomanian ? 'Înapoi' : 'Back'}</span>
                </Link>

                {/* Logo */}
                <div className="text-center mb-8">
                    <Link to="/">
                        <h1 className="text-3xl font-black tracking-tighter">
                            <span className="bg-gradient-to-r from-violet-400 to-orange-400 bg-clip-text text-transparent">ZEKTRIX</span>
                            <span className="text-white">.UK</span>
                        </h1>
                    </Link>
                </div>

                {/* Auth Card */}
                <div className="rounded-2xl p-6"
                    style={{
                        background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.95) 0%, rgba(10, 6, 20, 0.98) 100%)',
                        border: '1px solid rgba(139, 92, 246, 0.2)',
                        boxShadow: '0 0 40px rgba(139, 92, 246, 0.1)'
                    }}>
                    
                    {/* Tab Switcher */}
                    <div className="flex gap-2 mb-6 p-1 rounded-xl bg-white/5">
                        <button
                            onClick={() => setActiveTab('login')}
                            className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
                                activeTab === 'login' 
                                    ? 'text-white' 
                                    : 'text-gray-400 hover:text-white'
                            }`}
                            style={activeTab === 'login' ? {
                                background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
                                boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)'
                            } : {}}
                        >
                            {isRomanian ? 'Conectare' : 'Login'}
                        </button>
                        <button
                            onClick={() => setActiveTab('register')}
                            className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
                                activeTab === 'register' 
                                    ? 'text-white' 
                                    : 'text-gray-400 hover:text-white'
                            }`}
                            style={activeTab === 'register' ? {
                                background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
                                boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)'
                            } : {}}
                        >
                            {isRomanian ? 'Înregistrare' : 'Register'}
                        </button>
                    </div>

                    {/* Login Form */}
                    {activeTab === 'login' && (
                        <form onSubmit={handleLogin} className="space-y-4">
                            <div className="text-center mb-6">
                                <h2 className="text-xl font-bold text-white mb-1">{isRomanian ? 'Bine ai revenit!' : 'Welcome back!'}</h2>
                                <p className="text-sm text-gray-500">{isRomanian ? 'Conectează-te la contul tău' : 'Sign in to your account'}</p>
                            </div>

                            <div className="space-y-2">
                                <Label className="text-gray-400 text-sm">Email</Label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <Input
                                        type="email"
                                        value={loginEmail}
                                        onChange={(e) => setLoginEmail(e.target.value)}
                                        placeholder="email@exemplu.com"
                                        className="pl-10 bg-white/5 border-white/10 focus:border-violet-500 h-12"
                                        required
                                        data-testid="login-email"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <Label className="text-gray-400 text-sm">{isRomanian ? 'Parolă' : 'Password'}</Label>
                                    <Link to="/forgot-password" className="text-xs text-violet-400 hover:text-violet-300">
                                        {isRomanian ? 'Ai uitat parola?' : 'Forgot password?'}
                                    </Link>
                                </div>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <Input
                                        type={showPassword ? 'text' : 'password'}
                                        value={loginPassword}
                                        onChange={(e) => setLoginPassword(e.target.value)}
                                        placeholder="••••••••"
                                        className="pl-10 pr-10 bg-white/5 border-white/10 focus:border-violet-500 h-12"
                                        required
                                        data-testid="login-password"
                                    />
                                    <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white">
                                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                </div>
                            </div>

                            <Button
                                type="submit"
                                disabled={loading}
                                className="w-full h-12 text-base font-bold"
                                style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)', boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)' }}
                                data-testid="login-submit"
                            >
                                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (isRomanian ? 'Conectare' : 'Sign In')}
                            </Button>

                            <div className="relative my-6">
                                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/10" /></div>
                                <div className="relative flex justify-center text-xs"><span className="px-3 bg-[#0a0614] text-gray-500">{isRomanian ? 'sau' : 'or'}</span></div>
                            </div>

                            <Button
                                type="button"
                                variant="outline"
                                onClick={loginWithGoogle}
                                className="w-full h-12 border-white/10 hover:border-violet-500 hover:bg-violet-500/10"
                            >
                                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                                {isRomanian ? 'Continuă cu Google' : 'Continue with Google'}
                            </Button>
                        </form>
                    )}

                    {/* Register Form */}
                    {activeTab === 'register' && (
                        <form onSubmit={handleRegister} className="space-y-4">
                            <div className="text-center mb-6">
                                <h2 className="text-xl font-bold text-white mb-1">{isRomanian ? 'Creează cont' : 'Create account'}</h2>
                                <p className="text-sm text-gray-500">{isRomanian ? 'Înregistrează-te pentru a participa' : 'Register to participate'}</p>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-2">
                                    <Label className="text-gray-400 text-sm">{isRomanian ? 'Prenume' : 'First Name'}</Label>
                                    <Input
                                        value={regFirstName}
                                        onChange={(e) => setRegFirstName(e.target.value)}
                                        placeholder="Ion"
                                        className="bg-white/5 border-white/10 focus:border-violet-500 h-11"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label className="text-gray-400 text-sm">{isRomanian ? 'Nume' : 'Last Name'}</Label>
                                    <Input
                                        value={regLastName}
                                        onChange={(e) => setRegLastName(e.target.value)}
                                        placeholder="Popescu"
                                        className="bg-white/5 border-white/10 focus:border-violet-500 h-11"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label className="text-gray-400 text-sm">{isRomanian ? 'Telefon' : 'Phone'}</Label>
                                <div className="relative">
                                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <Input
                                        value={regPhone}
                                        onChange={(e) => setRegPhone(e.target.value)}
                                        placeholder="0712345678"
                                        className="pl-10 bg-white/5 border-white/10 focus:border-violet-500 h-11"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label className="text-gray-400 text-sm">{isRomanian ? 'Utilizator' : 'Username'}</Label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <Input
                                        value={regUsername}
                                        onChange={(e) => setRegUsername(e.target.value)}
                                        placeholder="username"
                                        className="pl-10 bg-white/5 border-white/10 focus:border-violet-500 h-11"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label className="text-gray-400 text-sm">Email</Label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <Input
                                        type="email"
                                        value={regEmail}
                                        onChange={(e) => setRegEmail(e.target.value)}
                                        placeholder="email@exemplu.com"
                                        className="pl-10 bg-white/5 border-white/10 focus:border-violet-500 h-11"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-2">
                                    <Label className="text-gray-400 text-sm">{isRomanian ? 'Parolă' : 'Password'}</Label>
                                    <Input
                                        type="password"
                                        value={regPassword}
                                        onChange={(e) => setRegPassword(e.target.value)}
                                        placeholder="••••••"
                                        className="bg-white/5 border-white/10 focus:border-violet-500 h-11"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label className="text-gray-400 text-sm">{isRomanian ? 'Confirmă' : 'Confirm'}</Label>
                                    <Input
                                        type="password"
                                        value={regConfirmPassword}
                                        onChange={(e) => setRegConfirmPassword(e.target.value)}
                                        placeholder="••••••"
                                        className="bg-white/5 border-white/10 focus:border-violet-500 h-11"
                                        required
                                    />
                                </div>
                            </div>

                            <Button
                                type="submit"
                                disabled={loading}
                                className="w-full h-12 text-base font-bold mt-2"
                                style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)', boxShadow: '0 0 20px rgba(139, 92, 246, 0.4)' }}
                                data-testid="register-submit"
                            >
                                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (isRomanian ? 'Creează Cont' : 'Create Account')}
                            </Button>

                            <p className="text-xs text-gray-500 text-center mt-4">
                                {isRomanian ? 'Prin înregistrare, accepți ' : 'By registering, you agree to our '}
                                <Link to="/terms" className="text-violet-400 hover:underline">{isRomanian ? 'Termenii și Condițiile' : 'Terms'}</Link>
                            </p>
                        </form>
                    )}
                </div>

                {/* Features */}
                <div className="mt-8 grid grid-cols-3 gap-3">
                    {[
                        { icon: Trophy, label: isRomanian ? 'Premii Reale' : 'Real Prizes' },
                        { icon: Lock, label: isRomanian ? 'Plăți Sigure' : 'Secure' },
                        { icon: UserCircle, label: isRomanian ? 'Suport 24/7' : '24/7 Support' }
                    ].map((f, i) => (
                        <div key={i} className="text-center p-3 rounded-xl bg-white/5">
                            <f.icon className="w-5 h-5 text-violet-400 mx-auto mb-1" />
                            <p className="text-[10px] text-gray-500">{f.label}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
