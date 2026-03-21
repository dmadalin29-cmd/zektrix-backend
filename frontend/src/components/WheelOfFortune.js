import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Dialog, DialogContent, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { X, Sparkles, Gift, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SEGMENT_COLORS = [
    '#8b5cf6', '#f59e0b', '#ef4444', '#10b981',
    '#06b6d4', '#f97316', '#6b7280', '#ec4899'
];

const WheelOfFortune = ({ open, onClose }) => {
    const { token, isAuthenticated } = useAuth();
    const { isRomanian } = useLanguage();
    const [prizes, setPrizes] = useState([]);
    const [canSpin, setCanSpin] = useState(true);
    const [spinning, setSpinning] = useState(false);
    const [result, setResult] = useState(null);
    const [rotation, setRotation] = useState(0);
    const [loading, setLoading] = useState(true);
    const canvasRef = useRef(null);

    useEffect(() => {
        if (!open || !token) return;
        setLoading(true);
        Promise.all([
            axios.get(`${API}/wheel/prizes`),
            axios.get(`${API}/wheel/status`, { headers: { Authorization: `Bearer ${token}` } })
        ]).then(([prizesRes, statusRes]) => {
            setPrizes(prizesRes.data || []);
            setCanSpin(statusRes.data.can_spin);
            if (!statusRes.data.can_spin && statusRes.data.previous_spin) {
                setResult({
                    prize_label: statusRes.data.previous_spin.prize_label,
                    prize_type: statusRes.data.previous_spin.prize_type
                });
            }
        }).catch(() => {}).finally(() => setLoading(false));
    }, [open, token]);

    useEffect(() => {
        if (prizes.length > 0 && canvasRef.current) {
            drawWheel(rotation);
        }
    }, [prizes, rotation]);

    const drawWheel = (rot) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const size = canvas.width;
        const center = size / 2;
        const radius = center - 8;
        const segAngle = (2 * Math.PI) / prizes.length;

        ctx.clearRect(0, 0, size, size);
        ctx.save();
        ctx.translate(center, center);
        ctx.rotate((rot * Math.PI) / 180);

        prizes.forEach((prize, i) => {
            const startAngle = i * segAngle - Math.PI / 2;
            const endAngle = startAngle + segAngle;

            // Segment fill
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.arc(0, 0, radius, startAngle, endAngle);
            ctx.closePath();
            ctx.fillStyle = prize.color || SEGMENT_COLORS[i % SEGMENT_COLORS.length];
            ctx.fill();

            // Border
            ctx.strokeStyle = 'rgba(255,255,255,0.15)';
            ctx.lineWidth = 1;
            ctx.stroke();

            // Text
            ctx.save();
            ctx.rotate(startAngle + segAngle / 2);
            ctx.textAlign = 'center';
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 11px Outfit, sans-serif';
            ctx.shadowColor = 'rgba(0,0,0,0.5)';
            ctx.shadowBlur = 3;
            const label = prize.label.length > 14 ? prize.label.substring(0, 13) + '..' : prize.label;
            ctx.fillText(label, radius * 0.6, 4);
            ctx.restore();
        });

        ctx.restore();

        // Outer ring glow
        ctx.beginPath();
        ctx.arc(center, center, radius + 4, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(139,92,246,0.4)';
        ctx.lineWidth = 3;
        ctx.stroke();

        // Center circle
        ctx.beginPath();
        ctx.arc(center, center, 22, 0, Math.PI * 2);
        const grd = ctx.createRadialGradient(center, center, 5, center, center, 22);
        grd.addColorStop(0, '#A666FF');
        grd.addColorStop(1, '#8B3DFF');
        ctx.fillStyle = grd;
        ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.3)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Arrow pointer (top)
        ctx.beginPath();
        ctx.moveTo(center, 2);
        ctx.lineTo(center - 12, 28);
        ctx.lineTo(center + 12, 28);
        ctx.closePath();
        ctx.fillStyle = '#FF5E00';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.5;
        ctx.stroke();
    };

    const handleSpin = async () => {
        if (!canSpin || spinning || !isAuthenticated) return;
        setSpinning(true);
        setResult(null);

        try {
            const { data } = await axios.post(`${API}/wheel/spin`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });

            // Find prize index
            const prizeIndex = prizes.findIndex(p => p.id === data.prize_id);
            const segAngle = 360 / prizes.length;
            // Target: prize segment centered at top (under arrow)
            const targetAngle = 360 - (prizeIndex * segAngle + segAngle / 2);
            const totalRotation = 360 * 6 + targetAngle; // 6 full spins + landing

            // Animate
            let startTime = null;
            const duration = 4500;
            const startRot = rotation;

            const animate = (timestamp) => {
                if (!startTime) startTime = timestamp;
                const elapsed = timestamp - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // Ease out cubic
                const eased = 1 - Math.pow(1 - progress, 3);
                const currentRot = startRot + totalRotation * eased;
                setRotation(currentRot % 360 === 0 ? currentRot : currentRot);
                drawWheel(currentRot);

                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    setRotation(currentRot % 360);
                    setResult(data);
                    setCanSpin(false);
                    setSpinning(false);

                    if (data.prize_type !== 'nothing') {
                        toast.success(isRomanian ? `Felicitari! Ai castigat ${data.prize_label}!` : `Congratulations! You won ${data.prize_label}!`);
                    }
                }
            };

            requestAnimationFrame(animate);
        } catch (err) {
            setSpinning(false);
            const msg = err.response?.data?.detail || 'Error';
            toast.error(msg);
            if (msg.includes('deja')) setCanSpin(false);
        }
    };

    if (!isAuthenticated) return null;

    return (
        <Dialog open={open} onOpenChange={(v) => { if (!spinning) onClose(); }}>
            <DialogContent className="sm:max-w-md p-0 overflow-hidden border-0 bg-transparent shadow-none" hideCloseBtn>
                <div className="rounded-3xl overflow-hidden" style={{
                    background: 'linear-gradient(135deg, rgba(12, 8, 24, 0.98), rgba(8, 4, 16, 0.99))',
                    border: '1px solid rgba(139, 92, 246, 0.25)',
                    boxShadow: '0 0 60px rgba(139, 92, 246, 0.15), 0 25px 50px rgba(0,0,0,0.5)'
                }} data-testid="wheel-of-fortune-modal">
                    <DialogTitle className="sr-only">Roata Norocului</DialogTitle>
                    {/* Header */}
                    <div className="flex items-center justify-between p-4 border-b border-white/[0.06]">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                                <Gift className="w-4 h-4 text-white" />
                            </div>
                            <div>
                                <h2 className="text-base font-bold text-white tracking-tight">
                                    {isRomanian ? 'Roata Norocului' : 'Wheel of Fortune'}
                                </h2>
                                <p className="text-[10px] text-gray-500">
                                    {isRomanian ? 'Invarte roata si castiga premii!' : 'Spin the wheel and win prizes!'}
                                </p>
                            </div>
                        </div>
                        <button onClick={() => { if (!spinning) onClose(); }}
                            className="w-8 h-8 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] flex items-center justify-center transition-colors"
                            data-testid="wheel-close-btn">
                            <X className="w-4 h-4 text-gray-400" />
                        </button>
                    </div>

                    {/* Wheel */}
                    <div className="p-4 flex flex-col items-center">
                        {loading ? (
                            <div className="w-64 h-64 flex items-center justify-center">
                                <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
                            </div>
                        ) : (
                            <div className="relative">
                                <canvas
                                    ref={canvasRef}
                                    width={280}
                                    height={280}
                                    className="rounded-full"
                                    data-testid="wheel-canvas"
                                />
                                {/* Glow effect */}
                                {spinning && (
                                    <div className="absolute inset-0 rounded-full animate-pulse"
                                        style={{ boxShadow: '0 0 40px rgba(139, 92, 246, 0.3)' }} />
                                )}
                            </div>
                        )}

                        {/* Result */}
                        {result && !spinning && (
                            <div className="mt-4 p-4 rounded-2xl text-center w-full"
                                style={{
                                    background: result.prize_type === 'nothing'
                                        ? 'rgba(107, 114, 128, 0.1)'
                                        : 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(245,158,11,0.1))',
                                    border: `1px solid ${result.prize_type === 'nothing' ? 'rgba(107,114,128,0.2)' : 'rgba(139,92,246,0.3)'}`
                                }}
                                data-testid="wheel-result"
                            >
                                <Sparkles className={`w-6 h-6 mx-auto mb-2 ${result.prize_type === 'nothing' ? 'text-gray-500' : 'text-amber-400'}`} />
                                <p className="text-lg font-bold text-white">{result.prize_label}</p>
                                <p className="text-xs text-gray-400 mt-1">
                                    {result.prize_type === 'nothing'
                                        ? (isRomanian ? 'Mai mult noroc data viitoare!' : 'Better luck next time!')
                                        : (isRomanian ? 'Premiul a fost adaugat in contul tau!' : 'Prize has been added to your account!')}
                                </p>
                            </div>
                        )}

                        {/* Spin Button */}
                        <Button
                            onClick={handleSpin}
                            disabled={!canSpin || spinning || loading}
                            className="mt-4 w-full h-12 rounded-xl font-bold text-base gap-2 shadow-lg"
                            style={{
                                background: canSpin
                                    ? 'linear-gradient(135deg, #8B3DFF, #FF5E00)'
                                    : 'rgba(107, 114, 128, 0.2)',
                                boxShadow: canSpin ? '0 0 20px rgba(139, 61, 255, 0.3)' : 'none'
                            }}
                            data-testid="spin-wheel-btn"
                        >
                            {spinning ? (
                                <><Loader2 className="w-5 h-5 animate-spin" /> {isRomanian ? 'Se invarte...' : 'Spinning...'}</>
                            ) : !canSpin ? (
                                <>{isRomanian ? 'Ai folosit deja roata' : 'Already spun'}</>
                            ) : (
                                <><Sparkles className="w-5 h-5" /> {isRomanian ? 'Invarte Roata!' : 'Spin the Wheel!'}</>
                            )}
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default WheelOfFortune;
