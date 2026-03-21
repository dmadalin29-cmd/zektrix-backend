import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { X, Percent, ArrowRight, Loader2, Clock } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ExitIntentPopup = () => {
    const { token, isAuthenticated } = useAuth();
    const { isRomanian } = useLanguage();
    const [show, setShow] = useState(false);
    const [claimed, setClaimed] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Only trigger for authenticated users who haven't seen it this session
        if (!isAuthenticated) return;
        if (sessionStorage.getItem('zektrix_exit_shown')) return;

        const handleMouseLeave = (e) => {
            if (e.clientY <= 0 && !sessionStorage.getItem('zektrix_exit_shown')) {
                sessionStorage.setItem('zektrix_exit_shown', '1');
                setShow(true);
            }
        };

        // Delay adding the listener so it doesn't trigger immediately
        const timer = setTimeout(() => {
            document.addEventListener('mouseleave', handleMouseLeave);
        }, 10000); // 10 second delay before activating

        return () => {
            clearTimeout(timer);
            document.removeEventListener('mouseleave', handleMouseLeave);
        };
    }, [isAuthenticated]);

    const handleClaim = async () => {
        if (!token || claimed) return;
        setLoading(true);
        try {
            await axios.post(`${API}/exit-intent/claim`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setClaimed(true);
            toast.success(isRomanian ? 'Reducere de 15% activata! Valabila 24h.' : '15% discount activated! Valid for 24h.');
        } catch (err) {
            const msg = err.response?.data?.detail || 'Error';
            if (msg.includes('deja')) {
                setClaimed(true);
                toast.info(isRomanian ? 'Ai folosit deja aceasta oferta' : 'You already used this offer');
            } else {
                toast.error(msg);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={show} onOpenChange={setShow}>
            <DialogContent className="sm:max-w-sm p-0 overflow-hidden border-0 bg-transparent shadow-none" hideCloseBtn>
                <div className="rounded-3xl overflow-hidden relative" style={{
                    background: 'linear-gradient(135deg, rgba(12, 8, 24, 0.98), rgba(8, 4, 16, 0.99))',
                    border: '1px solid rgba(255, 94, 0, 0.25)',
                    boxShadow: '0 0 60px rgba(255, 94, 0, 0.1), 0 25px 50px rgba(0,0,0,0.5)'
                }} data-testid="exit-intent-popup">
                    {/* Close */}
                    <button onClick={() => setShow(false)}
                        className="absolute top-3 right-3 w-8 h-8 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] flex items-center justify-center z-10 transition-colors"
                        data-testid="exit-close-btn">
                        <X className="w-4 h-4 text-gray-400" />
                    </button>

                    {/* Content */}
                    <div className="p-6 text-center">
                        {/* Icon */}
                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center"
                            style={{ background: 'linear-gradient(135deg, #FF5E00, #FF3300)', boxShadow: '0 0 30px rgba(255,94,0,0.3)' }}>
                            <Percent className="w-8 h-8 text-white" />
                        </div>

                        <h2 className="text-2xl font-black text-white tracking-tight mb-2">
                            {isRomanian ? 'Stai! Nu pleca inca!' : 'Wait! Don\'t leave yet!'}
                        </h2>
                        <p className="text-sm text-gray-400 mb-5">
                            {isRomanian
                                ? 'Ai primit o reducere speciala de 15% la urmatoarea ta achizitie!'
                                : 'You\'ve received a special 15% discount on your next purchase!'}
                        </p>

                        {/* Discount Badge */}
                        <div className="inline-flex items-center gap-3 px-5 py-3 rounded-2xl mb-5"
                            style={{
                                background: 'linear-gradient(135deg, rgba(255,94,0,0.1), rgba(255,51,0,0.05))',
                                border: '1px solid rgba(255,94,0,0.2)'
                            }}>
                            <span className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-400">15%</span>
                            <div className="text-left">
                                <p className="text-sm font-bold text-white">{isRomanian ? 'REDUCERE' : 'DISCOUNT'}</p>
                                <div className="flex items-center gap-1 text-[10px] text-gray-500">
                                    <Clock className="w-3 h-3" />
                                    {isRomanian ? 'Valabil 24 ore' : 'Valid 24 hours'}
                                </div>
                            </div>
                        </div>

                        {claimed ? (
                            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                <p className="text-sm font-semibold text-emerald-400">
                                    {isRomanian ? 'Reducerea a fost activata in contul tau!' : 'Discount has been activated in your account!'}
                                </p>
                            </div>
                        ) : (
                            <Button
                                onClick={handleClaim}
                                disabled={loading}
                                className="w-full h-12 rounded-xl font-bold text-base gap-2"
                                style={{
                                    background: 'linear-gradient(135deg, #FF5E00, #FF3300)',
                                    boxShadow: '0 0 20px rgba(255, 94, 0, 0.3)'
                                }}
                                data-testid="claim-exit-discount-btn"
                            >
                                {loading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <>{isRomanian ? 'Activeaza Reducerea' : 'Claim Discount'} <ArrowRight className="w-5 h-5" /></>
                                )}
                            </Button>
                        )}

                        <button onClick={() => setShow(false)} className="mt-3 text-xs text-gray-600 hover:text-gray-400 transition-colors" data-testid="exit-no-thanks">
                            {isRomanian ? 'Nu, multumesc' : 'No, thanks'}
                        </button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default ExitIntentPopup;
