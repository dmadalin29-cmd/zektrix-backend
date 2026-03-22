import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useCart } from '../context/CartContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import ShareButton from '../components/ShareButton';
import CountdownTimer from '../components/CountdownTimer';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';
import { 
    Zap, Clock, Ticket, Minus, Plus, Loader2, Trophy, ArrowLeft, 
    PartyPopper, CreditCard, Mail, HelpCircle, CheckCircle, XCircle, 
    ShoppingCart, Users, Calendar, Gift, ChevronLeft, ChevronRight, Wallet,
    Package, Percent, Radio, ExternalLink
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CompetitionDetailPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user, token, isAuthenticated, refreshUser } = useAuth();
    const { t, isRomanian } = useLanguage();
    const { addToCart } = useCart();
    const [competition, setCompetition] = useState(null);
    const [loading, setLoading] = useState(true);
    const [quantity, setQuantity] = useState(1);
    const [purchasing, setPurchasing] = useState(false);
    const [purchaseSuccess, setPurchaseSuccess] = useState(false);
    const [purchasedLocuri, setPurchasedLocuri] = useState([]);
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [answerError, setAnswerError] = useState(false);
    const [answerVerified, setAnswerVerified] = useState(false);
    const [enteringFree, setEnteringFree] = useState(false);
    const [activeImageIndex, setActiveImageIndex] = useState(0);
    const [paymentMethod, setPaymentMethod] = useState('viva');
    const [bundles, setBundles] = useState([]);
    const [liveDraw, setLiveDraw] = useState(null);
    const [tiktokVideos, setTiktokVideos] = useState([]);

    useEffect(() => { fetchCompetition(); fetchBundles(); fetchLiveDraw(); fetchTiktokVideos(); }, [id]);

    const fetchCompetition = async () => {
        try {
            const response = await axios.get(`${API}/competitions/${id}`);
            setCompetition(response.data);
        } catch (error) {
            toast.error('Competition not found');
            navigate('/competitions');
        } finally {
            setLoading(false);
        }
    };

    const fetchBundles = async () => {
        try {
            const res = await axios.get(`${API}/bundles`);
            setBundles(res.data || []);
        } catch { }
    };

    const fetchLiveDraw = async () => {
        try {
            const res = await axios.get(`${API}/live-draw`);
            if (res.data?.is_live) setLiveDraw(res.data);
        } catch { }
    };

    const fetchTiktokVideos = async () => {
        try {
            const res = await axios.get(`${API}/tiktok-videos`);
            setTiktokVideos(res.data || []);
        } catch { }
    };

    const verifyAnswer = () => {
        if (selectedAnswer === null) { toast.error(isRomanian ? 'Selectează un răspuns' : 'Select an answer'); return; }
        const isCorrect = selectedAnswer === competition.qualification_question?.correct_answer;
        if (isCorrect) { setAnswerVerified(true); setAnswerError(false); toast.success(isRomanian ? 'Răspuns corect!' : 'Correct answer!'); }
        else { setAnswerError(true); toast.error(isRomanian ? 'Răspuns incorect. Încearcă din nou!' : 'Incorrect answer. Try again!'); }
    };

    const handlePurchase = async () => {
        if (!isAuthenticated) { navigate('/login', { state: { from: { pathname: `/competitions/${id}` } } }); return; }
        if (competition.qualification_question && !answerVerified) { toast.error(isRomanian ? 'Răspunde corect la întrebare' : 'Answer the question correctly first'); return; }

        setPurchasing(true);
        try {
            if (paymentMethod === 'wallet') {
                const response = await axios.post(`${API}/tickets/purchase`,
                    { competition_id: id, quantity, qualification_answer: selectedAnswer },
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                setPurchasedLocuri(response.data);
                setPurchaseSuccess(true);
                toast.success(isRomanian ? 'Locuri cumpărate cu succes!' : 'Tickets purchased successfully!');
                fetchCompetition();
                refreshUser();
            } else {
                const response = await axios.post(`${API}/tickets/purchase-viva`,
                    { competition_id: id, quantity, qualification_answer: selectedAnswer },
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                if (response.data.checkout_url) { window.location.href = response.data.checkout_url; }
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Payment failed');
        } finally {
            setPurchasing(false);
        }
    };

    const handleAddToCart = () => {
        if (competition.qualification_question && !answerVerified) { toast.error(isRomanian ? 'Răspunde corect la întrebare' : 'Answer the question correctly first'); return; }
        addToCart(competition, quantity, selectedAnswer);
        toast.success(isRomanian ? 'Adăugat în coș!' : 'Added to cart!');
    };

    const handleFreeEntry = async () => {
        if (!isAuthenticated) { navigate('/login', { state: { from: { pathname: `/competitions/${id}` } } }); return; }
        if (competition.qualification_question && !answerVerified) { toast.error(isRomanian ? 'Răspunde corect la întrebare' : 'Answer the question correctly first'); return; }
        setEnteringFree(true);
        try {
            const response = await axios.post(`${API}/tickets/enter-free`, { competition_id: id, qualification_answer: selectedAnswer }, { headers: { Authorization: `Bearer ${token}` } });
            setPurchasedLocuri([response.data.ticket]);
            setPurchaseSuccess(true);
            toast.success(response.data.message);
            fetchCompetition();
        } catch (error) {
            toast.error(error.response?.data?.detail || (isRomanian ? 'Eroare la înscriere' : 'Entry failed'));
        } finally {
            setEnteringFree(false);
        }
    };

    if (loading) {
        return (<div className="min-h-screen bg-background"><Navbar /><main className="pt-28 flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary" /></main></div>);
    }
    if (!competition) return null;

    const soldPercentage = (competition.sold_tickets / competition.max_tickets) * 100;
    const available = competition.max_tickets - competition.sold_tickets;
    const activeBundle = bundles.find(b => b.quantity === quantity);
    const totalCost = activeBundle 
        ? competition.ticket_price * quantity * (1 - activeBundle.discount_percent / 100) 
        : competition.ticket_price * quantity;
    const isFree = competition.is_free || competition.ticket_price === 0;
    const qualQuestion = competition.qualification_question;
    const postalEntry = competition.postal_entry;
    const getUrgencyClass = () => { if (soldPercentage >= 80) return 'progress-urgency-high'; if (soldPercentage >= 50) return 'progress-urgency-medium'; return 'progress-urgency-low'; };

    return (
        <div className="min-h-screen bg-background">
            <Navbar />
            <div className="fixed inset-0 pointer-events-none overflow-hidden"><div className="orb orb-1" /><div className="orb orb-2" /></div>

            <main className="relative pt-28 pb-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <Link to="/competitions" className="inline-flex items-center gap-2 text-muted-foreground hover:text-white transition-colors mb-8">
                        <ArrowLeft className="w-4 h-4" /> {isRomanian ? 'Înapoi la Competiții' : 'Back to Competitions'}
                    </Link>

                    {/* Success Dialog */}
                    <Dialog open={purchaseSuccess} onOpenChange={setPurchaseSuccess}>
                        <DialogContent className="glass border-secondary/30" aria-describedby="success-description">
                            <DialogHeader className="space-y-3 pt-2">
                                <div className="w-14 h-14 rounded-full bg-secondary/20 flex items-center justify-center mx-auto neon-secondary">
                                    <PartyPopper className="w-7 h-7 text-secondary" />
                                </div>
                                <DialogTitle className="text-center text-xl font-bold">{t('congratulations')}</DialogTitle>
                            </DialogHeader>
                            <div id="success-description" className="text-center space-y-3 py-2">
                                <p className="text-sm text-muted-foreground">{t('you_purchased')} {purchasedLocuri.length} {purchasedLocuri.length === 1 ? 'loc' : t('locuri')}!</p>
                                <div className="flex flex-wrap gap-2 justify-center">
                                    {purchasedLocuri.map((ticket) => (<span key={ticket.ticket_id} className="ticket-badge text-sm">#{ticket.ticket_number}</span>))}
                                </div>
                            </div>
                            <div className="flex flex-col gap-3 pt-2">
                                <Button className="w-full btn-secondary text-black font-semibold h-11" onClick={() => navigate('/dashboard/locuri')}>{t('view_my_locs')}</Button>
                                <Button variant="outline" className="w-full font-semibold h-11" onClick={() => { setPurchaseSuccess(false); fetchCompetition(); }}>{t('buy_more')}</Button>
                            </div>
                        </DialogContent>
                    </Dialog>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* ===== PURCHASE CARD (first on mobile, sticky right on desktop) ===== */}
                        <div className="lg:col-start-3 lg:row-start-1 lg:row-span-10">
                            <div className="lg:sticky lg:top-24">
                            <Card className="glass border-primary/30" data-testid="purchase-card">
                                <CardHeader className="pb-3">
                                    <CardTitle className="flex items-center justify-between">
                                        <span>{isFree ? (isRomanian ? 'Intrare Gratuită' : 'Free Entry') : (isRomanian ? 'Cumpără Locuri' : 'Buy Spots')}</span>
                                        {isFree ? (
                                            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-lg px-3 py-1" data-testid="free-badge"><Gift className="w-4 h-4 mr-1" /> GRATUIT</Badge>
                                        ) : (
                                            <span className="price-display">£{competition.ticket_price.toFixed(2)}</span>
                                        )}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {competition.status === 'completed' ? (
                                        <div className="text-center py-6"><Trophy className="w-10 h-10 mx-auto text-secondary mb-3" /><p className="font-bold text-lg">{isRomanian ? 'Competiție Încheiată' : 'Competition Ended'}</p></div>
                                    ) : available === 0 ? (
                                        <div className="text-center py-6"><Ticket className="w-10 h-10 mx-auto text-muted-foreground mb-3" /><p className="font-bold text-lg">Sold Out</p></div>
                                    ) : (
                                        <>
                                            {/* Qualification Question (always first) */}
                                            {qualQuestion && (
                                                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-3">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <HelpCircle className="w-4 h-4 text-yellow-500" />
                                                        <span className="text-xs font-medium">{isRomanian ? 'Întrebare de Calificare' : 'Qualification Question'}</span>
                                                        {answerVerified && <Badge className="badge-secondary ml-auto text-[10px]"><CheckCircle className="w-3 h-3 mr-0.5" /> OK</Badge>}
                                                    </div>
                                                    <p className="text-sm font-medium mb-2">{qualQuestion.question}</p>
                                                    <RadioGroup value={selectedAnswer?.toString()} onValueChange={(v) => { setSelectedAnswer(parseInt(v)); setAnswerError(false); setAnswerVerified(false); }} disabled={answerVerified} className="space-y-1.5">
                                                        {qualQuestion.options.map((option, idx) => (
                                                            <div key={idx} className={`flex items-center space-x-2 p-2.5 rounded-lg border cursor-pointer transition-all text-sm ${selectedAnswer === idx ? answerError ? 'border-destructive bg-destructive/10' : answerVerified ? 'border-secondary bg-secondary/10' : 'border-yellow-500 bg-yellow-500/10' : 'border-white/10 hover:border-white/20'} ${answerVerified ? 'opacity-70 cursor-not-allowed' : ''}`}>
                                                                <RadioGroupItem value={idx.toString()} id={`answer-${idx}`} data-testid={`answer-${idx}`} />
                                                                <Label htmlFor={`answer-${idx}`} className="cursor-pointer flex-1 flex items-center justify-between text-sm">
                                                                    <span>{option}</span>
                                                                    {selectedAnswer === idx && answerError && <XCircle className="w-4 h-4 text-destructive" />}
                                                                    {selectedAnswer === idx && answerVerified && <CheckCircle className="w-4 h-4 text-secondary" />}
                                                                </Label>
                                                            </div>
                                                        ))}
                                                    </RadioGroup>
                                                    {!answerVerified && (
                                                        <Button className="w-full mt-2 btn-outline text-sm py-2" onClick={verifyAnswer} disabled={selectedAnswer === null} size="sm">
                                                            {isRomanian ? 'Verifică' : 'Verify'}
                                                        </Button>
                                                    )}
                                                </div>
                                            )}

                                            {isFree ? (
                                                <>
                                                    <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-3 text-center">
                                                        <Gift className="w-8 h-8 mx-auto mb-2 text-emerald-400" />
                                                        <p className="font-bold text-emerald-400">{isRomanian ? 'Competiție Gratuită!' : 'Free Competition!'}</p>
                                                        <p className="text-xs text-muted-foreground mt-1">{isRomanian ? 'Primești 1 loc automat.' : 'You get 1 spot automatically.'}</p>
                                                    </div>
                                                    <Button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white py-5 text-base font-bold" onClick={handleFreeEntry} disabled={enteringFree || (qualQuestion && !answerVerified)} data-testid="enter-free-btn">
                                                        {enteringFree ? <Loader2 className="w-5 h-5 animate-spin" /> : !isAuthenticated ? (isRomanian ? 'Autentifică-te' : 'Log In') : <><Gift className="w-5 h-5 mr-2" /> {isRomanian ? 'Participă Gratuit' : 'Enter for Free'}</>}
                                                    </Button>
                                                </>
                                            ) : (
                                                <>
                                                    {/* Quantity */}
                                                    <div>
                                                        <p className="text-xs text-muted-foreground mb-2">{isRomanian ? 'Cantitate' : 'Quantity'}</p>
                                                        <div className="flex items-center gap-3">
                                                            <Button variant="outline" size="icon" onClick={() => setQuantity(Math.max(1, quantity - 1))} disabled={quantity <= 1} className="h-10 w-10" data-testid="qty-minus-btn"><Minus className="w-4 h-4" /></Button>
                                                            <Input type="number" value={quantity} onChange={(e) => setQuantity(Math.min(available, Math.max(1, parseInt(e.target.value) || 1)))} className="w-16 text-center input-modern h-10 text-lg font-mono font-bold" min={1} max={available} data-testid="qty-input" />
                                                            <Button variant="outline" size="icon" onClick={() => setQuantity(Math.min(available, quantity + 1))} disabled={quantity >= available} className="h-10 w-10" data-testid="qty-plus-btn"><Plus className="w-4 h-4" /></Button>
                                                        </div>
                                                    </div>

                                                    {/* Bundle Deals */}
                                                    {bundles.length > 0 && (
                                                        <div data-testid="bundle-deals-section">
                                                            <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1.5">
                                                                <Package className="w-3.5 h-3.5 text-amber-400" />
                                                                {isRomanian ? 'Pachete cu Reducere' : 'Bundle Deals'}
                                                            </p>
                                                            <div className="grid grid-cols-1 gap-2">
                                                                {bundles.map(b => {
                                                                    const bundlePrice = (competition.ticket_price * b.quantity * (1 - b.discount_percent / 100)).toFixed(2);
                                                                    const isSelected = quantity === b.quantity;
                                                                    return (
                                                                        <button
                                                                            key={b.bundle_id}
                                                                            onClick={() => setQuantity(Math.min(available, b.quantity))}
                                                                            data-testid={`bundle-${b.bundle_id}`}
                                                                            className={`w-full flex items-center justify-between p-3 rounded-xl border transition-all text-left ${isSelected ? 'border-amber-500 bg-amber-500/10 ring-1 ring-amber-500/30' : 'border-white/10 hover:border-white/20 bg-white/[0.02]'}`}
                                                                        >
                                                                            <div className="flex items-center gap-2.5">
                                                                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${isSelected ? 'bg-amber-500/20 text-amber-400' : 'bg-white/5 text-gray-400'}`}>
                                                                                    {b.quantity}x
                                                                                </div>
                                                                                <div>
                                                                                    <p className="text-sm font-medium">{b.name}</p>
                                                                                    <p className="text-[10px] text-muted-foreground">{b.quantity} {isRomanian ? 'locuri' : 'spots'}</p>
                                                                                </div>
                                                                            </div>
                                                                            <div className="text-right">
                                                                                <div className="flex items-center gap-1.5">
                                                                                    <span className="text-[10px] line-through text-gray-500">£{(competition.ticket_price * b.quantity).toFixed(2)}</span>
                                                                                    <span className={`text-sm font-bold ${isSelected ? 'text-amber-400' : 'text-white'}`}>£{bundlePrice}</span>
                                                                                </div>
                                                                                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px] mt-0.5">
                                                                                    <Percent className="w-2.5 h-2.5 mr-0.5" /> {b.discount_percent}% OFF
                                                                                </Badge>
                                                                            </div>
                                                                        </button>
                                                                    );
                                                                })}
                                                            </div>
                                                        </div>
                                                    )}

                                                    {/* Total */}
                                                    <div className="flex justify-between items-center py-3 border-y border-white/10">
                                                        <span className="text-muted-foreground text-sm">Total</span>
                                                        <span className="text-2xl font-black gradient-text font-mono">£{totalCost.toFixed(2)}</span>
                                                    </div>

                                                    {/* Payment Method */}
                                                    {isAuthenticated && (
                                                        <div className="space-y-2">
                                                            <p className="text-xs text-muted-foreground">{isRomanian ? 'Metoda de Plată' : 'Payment Method'}</p>
                                                            <button onClick={() => setPaymentMethod('wallet')} className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-all text-left ${paymentMethod === 'wallet' ? 'border-violet-500 bg-violet-500/10' : 'border-white/10 hover:border-white/20'}`} data-testid="payment-wallet-btn">
                                                                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${paymentMethod === 'wallet' ? 'border-violet-500' : 'border-gray-500'}`}>
                                                                    {paymentMethod === 'wallet' && <div className="w-2 h-2 rounded-full bg-violet-500" />}
                                                                </div>
                                                                <Wallet className="w-4 h-4 text-violet-400 shrink-0" />
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="text-sm font-medium">{isRomanian ? 'Portofel' : 'Wallet'}</p>
                                                                    <p className="text-[10px] text-muted-foreground">{isRomanian ? 'Sold' : 'Balance'}: £{(user?.balance || 0).toFixed(2)}</p>
                                                                </div>
                                                                {(user?.balance || 0) < totalCost && (
                                                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 shrink-0">{isRomanian ? 'Fonduri insuficiente' : 'Insufficient'}</span>
                                                                )}
                                                            </button>
                                                            <button onClick={() => setPaymentMethod('viva')} className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-all text-left ${paymentMethod === 'viva' ? 'border-violet-500 bg-violet-500/10' : 'border-white/10 hover:border-white/20'}`} data-testid="payment-viva-btn">
                                                                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${paymentMethod === 'viva' ? 'border-violet-500' : 'border-gray-500'}`}>
                                                                    {paymentMethod === 'viva' && <div className="w-2 h-2 rounded-full bg-violet-500" />}
                                                                </div>
                                                                <CreditCard className="w-4 h-4 text-amber-400 shrink-0" />
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="text-sm font-medium">Card / Apple Pay / Google Pay</p>
                                                                    <p className="text-[10px] text-muted-foreground">Visa, Mastercard, Apple Pay, Google Pay</p>
                                                                </div>
                                                            </button>
                                                        </div>
                                                    )}

                                                    {/* Buy Buttons */}
                                                    <div className="space-y-2">
                                                        <Button className="w-full btn-secondary text-black py-5 text-base font-bold" onClick={handlePurchase} disabled={purchasing || (qualQuestion && !answerVerified) || (paymentMethod === 'wallet' && isAuthenticated && (user?.balance || 0) < totalCost)} data-testid="buy-now-btn">
                                                            {purchasing ? <Loader2 className="w-5 h-5 animate-spin" /> : !isAuthenticated ? (isRomanian ? 'Autentifică-te pentru a Cumpăra' : 'Log In to Purchase') : paymentMethod === 'wallet' ? <><Wallet className="w-4 h-4 mr-2" /> {isRomanian ? 'Plătește din Portofel' : 'Pay with Wallet'} — £{totalCost.toFixed(2)}</> : <><CreditCard className="w-4 h-4 mr-2" /> {isRomanian ? 'Plătește cu Cardul' : 'Pay with Card'} — £{totalCost.toFixed(2)}</>}
                                                        </Button>
                                                        <Button variant="outline" className="w-full btn-outline py-4 text-sm" onClick={handleAddToCart} disabled={qualQuestion && !answerVerified} data-testid="add-to-cart-btn">
                                                            <ShoppingCart className="w-4 h-4 mr-2" /> {isRomanian ? 'Adaugă în Coș' : 'Add to Cart'}
                                                        </Button>
                                                    </div>

                                                    {qualQuestion && !answerVerified && (
                                                        <p className="text-xs text-center text-muted-foreground">{isRomanian ? 'Răspunde la întrebarea de calificare' : 'Answer the qualification question'}</p>
                                                    )}
                                                </>
                                            )}
                                        </>
                                    )}
                                </CardContent>
                            </Card>
                            </div>
                        </div>

                        {/* ===== LEFT COLUMN - Main Content ===== */}
                        <div className="lg:col-span-2 space-y-6">
                            {/* Image Gallery */}
                            <Card className="glass border-white/10 overflow-hidden">
                                <div className="relative">
                                    <div className="relative aspect-video">
                                        <img 
                                            src={(competition.images && competition.images.length > 0 ? competition.images[activeImageIndex || 0] : competition.image_url) || 'https://images.unsplash.com/photo-1579548122080-c35fd6820ecb?w=1200'} 
                                            alt={competition.title}
                                            className="w-full h-full object-cover"
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-t from-card via-transparent to-transparent" />
                                        
                                        {competition.images && competition.images.length > 1 && (
                                            <>
                                                <button onClick={() => setActiveImageIndex(i => (i || 0) > 0 ? (i || 0) - 1 : competition.images.length - 1)} className="absolute left-3 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/70 transition-colors z-10">
                                                    <ChevronLeft className="w-5 h-5" />
                                                </button>
                                                <button onClick={() => setActiveImageIndex(i => ((i || 0) + 1) % competition.images.length)} className="absolute right-3 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/70 transition-colors z-10">
                                                    <ChevronRight className="w-5 h-5" />
                                                </button>
                                            </>
                                        )}

                                        <div className="absolute top-4 left-4 flex gap-2">
                                            {competition.competition_type === 'instant_win' ? (
                                                <Badge className="badge-instant"><Zap className="w-3 h-3 mr-1" /> Autodraw</Badge>
                                            ) : (
                                                <Badge className="badge-classic"><Clock className="w-3 h-3 mr-1" /> Draw</Badge>
                                            )}
                                        </div>
                                        <div className="absolute top-4 right-4">
                                            <ShareButton competitionId={competition.competition_id} competitionTitle={competition.title} />
                                        </div>

                                        {soldPercentage >= 50 && (
                                            <div className="absolute bottom-4 right-4">
                                                <Badge className={soldPercentage >= 80 ? 'status-ending' : 'badge-secondary'}>
                                                    {Math.round(soldPercentage)}% {isRomanian ? 'Vândut' : 'Sold'}
                                                </Badge>
                                            </div>
                                        )}
                                    </div>

                                    {competition.images && competition.images.length > 1 && (
                                        <div className="flex gap-2 p-3 bg-black/20 overflow-x-auto">
                                            {competition.images.map((img, idx) => (
                                                <button key={idx} onClick={() => setActiveImageIndex(idx)} className={`flex-shrink-0 w-16 h-12 rounded-lg overflow-hidden border-2 transition-all ${(activeImageIndex || 0) === idx ? 'border-violet-500 scale-105' : 'border-transparent opacity-60 hover:opacity-100'}`}>
                                                    <img src={img} alt={`${idx+1}`} className="w-full h-full object-cover" />
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                <div className={`h-2 ${getUrgencyClass()}`}>
                                    <div className="progress-bar h-full">
                                        <div className="progress-fill" style={{ width: `${soldPercentage}%` }} />
                                    </div>
                                </div>

                                <CardContent className="p-6">
                                    <h1 className="text-3xl md:text-4xl font-black mb-4" data-testid="comp-title">{competition.title}</h1>
                                    <p className="text-muted-foreground text-lg mb-6">{competition.description}</p>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div className="bg-white/5 rounded-xl p-4 text-center">
                                            <Ticket className="w-5 h-5 mx-auto mb-2 text-primary" />
                                            <p className="text-2xl font-black font-mono">{available}</p>
                                            <p className="text-xs text-muted-foreground">{isRomanian ? 'Rămase' : 'Remaining'}</p>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-4 text-center">
                                            <Users className="w-5 h-5 mx-auto mb-2 text-secondary" />
                                            <p className="text-2xl font-black font-mono">{competition.sold_tickets}</p>
                                            <p className="text-xs text-muted-foreground">{isRomanian ? 'Vândute' : 'Sold'}</p>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-4 text-center">
                                            <Trophy className="w-5 h-5 mx-auto mb-2 text-accent" />
                                            <p className="text-2xl font-black font-mono">{competition.max_tickets}</p>
                                            <p className="text-xs text-muted-foreground">Total</p>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-4 text-center">
                                            <Calendar className="w-5 h-5 mx-auto mb-2 text-primary" />
                                            <p className="text-xl font-black">{Math.round(soldPercentage)}%</p>
                                            <p className="text-xs text-muted-foreground">{isRomanian ? 'Completat' : 'Complete'}</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* TikTok Live Draw Embed */}
                            {liveDraw && liveDraw.is_live && (liveDraw.competition_id === id || !liveDraw.competition_id) && (
                                <Card className="glass border-red-500/30 overflow-hidden" data-testid="live-draw-section">
                                    <CardContent className="p-6">
                                        <div className="flex items-center gap-3 mb-4">
                                            <div className="relative">
                                                <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                                                    <Radio className="w-5 h-5 text-red-400" />
                                                </div>
                                                <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-red-500 rounded-full animate-pulse border-2 border-background" />
                                            </div>
                                            <div className="flex-1">
                                                <h3 className="font-bold text-lg text-red-400">
                                                    {isRomanian ? 'EXTRAGERE LIVE!' : 'LIVE DRAW!'}
                                                </h3>
                                                <p className="text-sm text-muted-foreground">
                                                    {isRomanian ? 'Urmărește extragerea în direct pe TikTok' : 'Watch the draw live on TikTok'}
                                                </p>
                                            </div>
                                        </div>
                                        {liveDraw.tiktok_live_url && (
                                            <a 
                                                href={liveDraw.tiktok_live_url} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                data-testid="live-draw-link"
                                                className="flex items-center justify-center gap-2 w-full py-4 rounded-xl bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white font-bold text-base transition-all hover:scale-[1.02]"
                                            >
                                                <Radio className="w-5 h-5 animate-pulse" />
                                                {isRomanian ? 'Urmărește LIVE pe TikTok' : 'Watch LIVE on TikTok'}
                                                <ExternalLink className="w-4 h-4 ml-1" />
                                            </a>
                                        )}
                                    </CardContent>
                                </Card>
                            )}

                            {/* TikTok Video Gallery */}
                            {tiktokVideos.length > 0 && (
                                <Card className="glass border-white/10 overflow-hidden" data-testid="tiktok-gallery-section">
                                    <CardContent className="p-6">
                                        <div className="flex items-center gap-3 mb-5">
                                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#ff0050] to-[#00f2ea] flex items-center justify-center">
                                                <svg viewBox="0 0 24 24" className="w-5 h-5 text-white fill-current"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 00-.79-.05A6.34 6.34 0 003.15 15.2a6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.34-6.34V8.98a8.18 8.18 0 004.76 1.52V7.05a4.84 4.84 0 01-1-.36z"/></svg>
                                            </div>
                                            <div>
                                                <h3 className="font-bold text-lg">{isRomanian ? 'Videoclipuri TikTok' : 'TikTok Videos'}</h3>
                                                <p className="text-sm text-muted-foreground">{isRomanian ? 'Urmărește-ne pe TikTok' : 'Follow us on TikTok'}</p>
                                            </div>
                                        </div>
                                        <div className="grid gap-4" style={{ gridTemplateColumns: tiktokVideos.length === 1 ? '1fr' : 'repeat(auto-fit, minmax(280px, 1fr))' }}>
                                            {tiktokVideos.map(v => (
                                                <div key={v.video_uid} className="rounded-xl overflow-hidden bg-black/30 border border-white/5" data-testid={`tiktok-video-${v.video_uid}`}>
                                                    <iframe
                                                        src={v.embed_url}
                                                        className="w-full"
                                                        style={{ height: '500px', border: 'none' }}
                                                        allow="encrypted-media"
                                                        allowFullScreen
                                                        title={v.title || 'TikTok Video'}
                                                    />
                                                    {v.title && <p className="text-sm text-gray-400 p-3 border-t border-white/5">{v.title}</p>}
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}

                            {/* Countdown Timer */}
                            {competition.draw_date && (
                                <Card className="glass border-primary/30">
                                    <CardContent className="p-6">
                                        <div className="flex items-center justify-between mb-4">
                                            <div>
                                                <h3 className="font-bold text-lg">{isRomanian ? 'Extragerea În' : 'Draw In'}</h3>
                                                <p className="text-sm text-muted-foreground">
                                                    {new Date(competition.draw_date).toLocaleDateString('ro-RO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                                </p>
                                            </div>
                                            <Clock className="w-8 h-8 text-primary" />
                                        </div>
                                        <CountdownTimer targetDate={competition.draw_date} />
                                    </CardContent>
                                </Card>
                            )}

                            {/* Instant Prizes */}
                            {competition.instant_prizes && competition.instant_prizes.length > 0 && (
                                <Card className="glass border-amber-500/30 overflow-hidden" data-testid="instant-prizes-section">
                                    <CardContent className="p-6">
                                        <div className="flex items-center gap-3 mb-5">
                                            <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center"><Gift className="w-5 h-5 text-amber-400" /></div>
                                            <div>
                                                <h3 className="font-bold text-lg">{isRomanian ? 'Premii Instant' : 'Instant Prizes'}</h3>
                                                <p className="text-sm text-muted-foreground">{isRomanian ? 'Câștigă automat când pragul este atins!' : 'Win automatically when threshold is reached!'}</p>
                                            </div>
                                        </div>
                                        <div className="space-y-3">
                                            {competition.instant_prizes.sort((a, b) => a.percentage - b.percentage).map((prize, idx) => {
                                                const isAwarded = prize.awarded;
                                                const isReached = soldPercentage >= prize.percentage;
                                                return (
                                                    <div key={idx} className={`relative rounded-xl p-4 border transition-all ${isAwarded ? 'bg-green-500/10 border-green-500/30' : isReached ? 'bg-amber-500/10 border-amber-500/30 animate-pulse' : 'bg-white/5 border-white/10'}`} data-testid={`instant-prize-${idx}`}>
                                                        <div className="flex items-center justify-between gap-3">
                                                            <div className="flex items-center gap-3 min-w-0">
                                                                <div className={`w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-sm ${isAwarded ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'}`}>{prize.percentage}%</div>
                                                                <div className="min-w-0">
                                                                    <p className="font-bold truncate">{prize.prize_name}</p>
                                                                    {prize.prize_description && <p className="text-xs text-muted-foreground truncate">{prize.prize_description}</p>}
                                                                    {isAwarded && prize.winner_username && <p className="text-xs text-green-400 mt-1"><CheckCircle className="w-3 h-3 inline mr-1" />{isRomanian ? 'Câștigat de' : 'Won by'} {prize.winner_username}</p>}
                                                                </div>
                                                            </div>
                                                            <Badge className={`flex-shrink-0 ${isAwarded ? 'bg-green-500/20 text-green-400 border-green-500/30' : isReached ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-white/10 text-muted-foreground border-white/10'}`}>
                                                                {isAwarded ? (isRomanian ? 'Acordat' : 'Awarded') : isReached ? (isRomanian ? 'Se extrage!' : 'Drawing!') : (isRomanian ? 'La ' + prize.percentage + '%' : 'At ' + prize.percentage + '%')}
                                                            </Badge>
                                                        </div>
                                                        <div className="mt-3 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                                            <div className={`h-full rounded-full transition-all duration-500 ${isAwarded ? 'bg-green-500' : isReached ? 'bg-amber-500' : 'bg-primary/50'}`} style={{ width: `${Math.min(100, (soldPercentage / prize.percentage) * 100)}%` }} />
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}

                            {/* Postal Entry */}
                            {postalEntry && (
                                <Card className="postal-entry-section">
                                    <CardContent className="p-6">
                                        <div className="flex items-center gap-3 mb-4">
                                            <div className="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center"><Mail className="w-5 h-5 text-cyan-500" /></div>
                                            <div>
                                                <h3 className="font-bold">{isRomanian ? 'Intrare Poștală Gratuită' : 'Free Postal Entry'}</h3>
                                                <p className="text-sm text-muted-foreground">{isRomanian ? 'Alternativă fără cost' : 'No purchase necessary'}</p>
                                            </div>
                                        </div>
                                        <div className="space-y-4">
                                            <p className="text-sm text-muted-foreground">
                                                {isRomanian ? 'Pentru a participa gratuit, trimiteți o carte poștală sau scrisoare la adresa de mai jos. Fiecare scrisoare = 1 loc. Limită: 5 intrări per persoană.' : 'To enter for free, send a postcard or letter to the address below. Each letter = 1 ticket. Limit: 5 entries per person.'}
                                            </p>
                                            <div className="bg-black/20 rounded-xl p-4">
                                                <p className="text-sm font-bold mb-2">{isRomanian ? 'Includeți:' : 'Include:'}</p>
                                                <ul className="text-sm text-muted-foreground space-y-1">
                                                    {Array.isArray(postalEntry.instructions) ? (
                                                        postalEntry.instructions.map((inst, idx) => (<li key={idx} className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-cyan-500" />{inst}</li>))
                                                    ) : (
                                                        <>
                                                            <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-cyan-500" /> {isRomanian ? 'Nume complet' : 'Full name'}</li>
                                                            <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-cyan-500" /> {isRomanian ? 'Adresă poștală' : 'Postal address'}</li>
                                                            <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-cyan-500" /> {isRomanian ? 'Email și telefon' : 'Email & phone'}</li>
                                                            <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-cyan-500" /> {isRomanian ? 'Numele competiției' : 'Competition name'}</li>
                                                        </>
                                                    )}
                                                </ul>
                                            </div>
                                            <div className="bg-black/30 rounded-xl p-4 border border-cyan-500/20">
                                                <p className="text-xs text-muted-foreground mb-2">{isRomanian ? 'Trimiteți la:' : 'Send to:'}</p>
                                                <p className="font-mono text-sm">
                                                    {postalEntry.company_name || 'Zektrix UK Ltd'}<br/>
                                                    {postalEntry.address_line1 || 'c/o Bartle House'}<br/>
                                                    {postalEntry.address_line2 || 'Oxford Court, Manchester'}<br/>
                                                    {postalEntry.postcode || 'M23 WQ'}<br/>
                                                    {postalEntry.country || 'United Kingdom'}
                                                </p>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default CompetitionDetailPage;
