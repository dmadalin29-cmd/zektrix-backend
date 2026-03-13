import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import { Loader2, Mail, ArrowLeft, CheckCircle } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ForgotPasswordPage = () => {
    const { isRomanian } = useLanguage();
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState('');
    const [sent, setSent] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!email) {
            toast.error(isRomanian ? 'Te rugăm să introduci emailul' : 'Please enter your email');
            return;
        }
        
        setLoading(true);
        try {
            await axios.post(`${API}/auth/request-password-reset`, { email });
            setSent(true);
            toast.success(isRomanian ? 'Verifică emailul pentru linkul de resetare!' : 'Check your email for reset link!');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'A apărut o eroare');
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
                            {isRomanian ? 'Resetare Parolă' : 'Reset Password'}
                        </CardTitle>
                        <CardDescription>
                            {isRomanian 
                                ? 'Introdu emailul pentru a primi linkul de resetare' 
                                : 'Enter your email to receive a reset link'}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {sent ? (
                            <div className="text-center py-8 space-y-6">
                                <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center mx-auto">
                                    <CheckCircle className="w-10 h-10 text-green-500" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold mb-2">
                                        {isRomanian ? 'Email Trimis!' : 'Email Sent!'}
                                    </h3>
                                    <p className="text-muted-foreground">
                                        {isRomanian 
                                            ? 'Dacă există un cont cu acest email, vei primi un link de resetare.' 
                                            : 'If an account exists with this email, you will receive a reset link.'}
                                    </p>
                                </div>
                                <div className="space-y-3">
                                    <p className="text-sm text-muted-foreground">
                                        {isRomanian ? 'Nu ai primit emailul?' : "Didn't receive the email?"}
                                    </p>
                                    <Button 
                                        variant="outline" 
                                        onClick={() => setSent(false)}
                                        className="border-white/20"
                                    >
                                        {isRomanian ? 'Trimite din nou' : 'Send again'}
                                    </Button>
                                </div>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="space-y-2">
                                    <Label htmlFor="email">{isRomanian ? 'Adresa de Email' : 'Email Address'}</Label>
                                    <div className="relative">
                                        <Mail className="input-icon w-4 h-4 text-muted-foreground" />
                                        <Input
                                            id="email"
                                            type="email"
                                            placeholder="you@example.com"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="input-modern input-with-icon"
                                            required
                                            data-testid="forgot-email-input"
                                        />
                                    </div>
                                </div>
                                <Button
                                    type="submit"
                                    className="w-full btn-primary"
                                    disabled={loading}
                                    data-testid="forgot-submit-btn"
                                >
                                    {loading ? (
                                        <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Se trimite...</>
                                    ) : (
                                        isRomanian ? 'Trimite Link de Resetare' : 'Send Reset Link'
                                    )}
                                </Button>
                            </form>
                        )}

                        <div className="mt-6 text-center">
                            <Link 
                                to="/login" 
                                className="inline-flex items-center text-sm text-muted-foreground hover:text-primary transition-colors"
                            >
                                <ArrowLeft className="w-4 h-4 mr-2" />
                                {isRomanian ? 'Înapoi la Autentificare' : 'Back to Login'}
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default ForgotPasswordPage;
