import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Loader2, Lock, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ResetPasswordPage = () => {
    const { isRomanian } = useLanguage();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');
    
    const [loading, setLoading] = useState(false);
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState(false);

    useEffect(() => {
        if (!token) {
            setError(true);
        }
    }, [token]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (password.length < 6) {
            toast.error(isRomanian ? 'Parola trebuie să aibă minim 6 caractere' : 'Password must be at least 6 characters');
            return;
        }
        
        if (password !== confirmPassword) {
            toast.error(isRomanian ? 'Parolele nu se potrivesc' : 'Passwords do not match');
            return;
        }
        
        setLoading(true);
        try {
            await axios.post(`${API}/auth/reset-password`, { 
                token, 
                new_password: password 
            });
            setSuccess(true);
            toast.success(isRomanian ? 'Parola a fost resetată cu succes!' : 'Password reset successfully!');
        } catch (error) {
            const detail = error.response?.data?.detail;
            if (detail?.includes('expirat') || detail?.includes('expired')) {
                setError(true);
            }
            toast.error(detail || 'A apărut o eroare');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen hero-bg flex items-center justify-center p-4">
            {/* Background effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[100px]" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/20 rounded-full blur-[100px]" />
            </div>

            <div className="w-full max-w-md relative z-10">
                {/* Logo */}
                <Link to="/" className="block text-center mb-8">
                    <h1 className="text-3xl font-black tracking-tighter">
                        <span className="gradient-text">ZEKTRIX</span>
                        <span className="text-white">.UK</span>
                    </h1>
                </Link>

                <Card className="glass border-white/10">
                    <CardHeader className="text-center pb-4">
                        <CardTitle className="text-2xl font-bold">
                            {isRomanian ? 'Parolă Nouă' : 'New Password'}
                        </CardTitle>
                        <CardDescription>
                            {isRomanian 
                                ? 'Introdu noua ta parolă' 
                                : 'Enter your new password'}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {error ? (
                            <div className="text-center py-8 space-y-6">
                                <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto">
                                    <XCircle className="w-10 h-10 text-red-500" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold mb-2 text-red-400">
                                        {isRomanian ? 'Link Invalid sau Expirat' : 'Invalid or Expired Link'}
                                    </h3>
                                    <p className="text-muted-foreground">
                                        {isRomanian 
                                            ? 'Acest link de resetare nu mai este valid. Te rugăm să ceri unul nou.' 
                                            : 'This reset link is no longer valid. Please request a new one.'}
                                    </p>
                                </div>
                                <Link to="/forgot-password">
                                    <Button className="btn-primary">
                                        {isRomanian ? 'Cere Link Nou' : 'Request New Link'}
                                    </Button>
                                </Link>
                            </div>
                        ) : success ? (
                            <div className="text-center py-8 space-y-6">
                                <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center mx-auto">
                                    <CheckCircle className="w-10 h-10 text-green-500" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold mb-2">
                                        {isRomanian ? 'Parolă Resetată!' : 'Password Reset!'}
                                    </h3>
                                    <p className="text-muted-foreground">
                                        {isRomanian 
                                            ? 'Parola ta a fost schimbată cu succes.' 
                                            : 'Your password has been changed successfully.'}
                                    </p>
                                </div>
                                <Link to="/login">
                                    <Button className="btn-primary">
                                        {isRomanian ? 'Mergi la Autentificare' : 'Go to Login'}
                                    </Button>
                                </Link>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="space-y-2">
                                    <Label htmlFor="password">{isRomanian ? 'Parolă Nouă' : 'New Password'}</Label>
                                    <div className="relative">
                                        <Lock className="input-icon w-4 h-4 text-muted-foreground" />
                                        <Input
                                            id="password"
                                            type="password"
                                            placeholder="••••••••"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="input-modern input-with-icon"
                                            required
                                            data-testid="reset-password-input"
                                        />
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        {isRomanian ? 'Minim 6 caractere' : 'Minimum 6 characters'}
                                    </p>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="confirm">{isRomanian ? 'Confirmă Parola' : 'Confirm Password'}</Label>
                                    <div className="relative">
                                        <Lock className="input-icon w-4 h-4 text-muted-foreground" />
                                        <Input
                                            id="confirm"
                                            type="password"
                                            placeholder="••••••••"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            className="input-modern input-with-icon"
                                            required
                                            data-testid="reset-confirm-input"
                                        />
                                    </div>
                                </div>
                                <Button
                                    type="submit"
                                    className="w-full btn-primary"
                                    disabled={loading}
                                    data-testid="reset-submit-btn"
                                >
                                    {loading ? (
                                        <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Se procesează...</>
                                    ) : (
                                        isRomanian ? 'Resetează Parola' : 'Reset Password'
                                    )}
                                </Button>
                            </form>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default ResetPasswordPage;
