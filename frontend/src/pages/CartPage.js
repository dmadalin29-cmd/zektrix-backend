import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useCart } from '../context/CartContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';
import { ShoppingCart, Trash2, Minus, Plus, CreditCard, Loader2, ArrowRight, ShoppingBag, PartyPopper } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CartPage = () => {
    const { user, token, isAuthenticated, refreshUser } = useAuth();
    const { isRomanian } = useLanguage();
    const { items, updateQuantity, removeFromCart, clearCart, totalItems, totalPrice } = useCart();
    const navigate = useNavigate();
    
    const [loading, setLoading] = useState(false);
    const [purchaseComplete, setPurchaseComplete] = useState(false);
    const [purchasedTickets, setPurchasedTickets] = useState([]);

    const handleCheckout = async () => {
        if (!isAuthenticated) {
            toast.error(isRomanian ? 'Te rugăm să te autentifici' : 'Please log in first');
            navigate('/login');
            return;
        }

        setLoading(true);
        try {
            // All payments go through Viva
            const response = await axios.post(
                `${API}/cart/purchase`,
                {
                    items: items.map(item => ({
                        competition_id: item.competition_id,
                        quantity: item.quantity,
                        qualification_answer: item.qualification_answer
                    })),
                    payment_method: 'viva'
                },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            if (response.data.checkout_url) {
                window.location.href = response.data.checkout_url;
            }
        } catch (error) {
            toast.error(error.response?.data?.detail || (isRomanian ? 'Eroare la achiziție' : 'Purchase failed'));
            setLoading(false);
        }
    };

    if (purchaseComplete) {
        return (
            <div className="min-h-screen bg-background">
                <Navbar />
                <main className="pt-24 pb-16">
                    <div className="max-w-2xl mx-auto px-4 text-center">
                        <div className="mb-8">
                            <div className="w-24 h-24 rounded-full bg-secondary/20 flex items-center justify-center mx-auto mb-6 neon-secondary">
                                <PartyPopper className="w-12 h-12 text-secondary" />
                            </div>
                            <h1 className="text-4xl font-black mb-4">
                                {isRomanian ? 'Felicitări!' : 'Congratulations!'}
                            </h1>
                            <p className="text-xl text-muted-foreground">
                                {isRomanian 
                                    ? `Ai rezervat ${purchasedTickets.length} ${purchasedTickets.length === 1 ? 'loc' : 'locuri'} cu succes!`
                                    : `You successfully reserved ${purchasedTickets.length} ${purchasedTickets.length === 1 ? 'spot' : 'spots'}!`
                                }
                            </p>
                        </div>

                        <Card className="glass border-white/10 mb-8">
                            <CardContent className="p-6">
                                <h3 className="font-bold mb-4">{isRomanian ? 'Numerele Tale' : 'Your Numbers'}</h3>
                                <div className="flex flex-wrap gap-3 justify-center">
                                    {purchasedTickets.map((ticket) => (
                                        <span key={ticket.ticket_id} className="ticket-badge">
                                            #{ticket.ticket_number}
                                        </span>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>

                        <div className="flex gap-4 justify-center">
                            <Link to="/dashboard/tickets">
                                <Button className="btn-primary">
                                    {isRomanian ? 'Vezi Locurile' : 'View Spots'}
                                </Button>
                            </Link>
                            <Link to="/competitions">
                                <Button variant="outline" className="btn-outline">
                                    {isRomanian ? 'Mai Multe Competiții' : 'More Competitions'}
                                </Button>
                            </Link>
                        </div>
                    </div>
                </main>
                <Footer />
            </div>
        );
    }

    if (items.length === 0) {
        return (
            <div className="min-h-screen bg-background">
                <Navbar />
                <main className="pt-24 pb-16">
                    <div className="max-w-2xl mx-auto px-4 text-center">
                        <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center mx-auto mb-6">
                            <ShoppingBag className="w-12 h-12 text-muted-foreground" />
                        </div>
                        <h1 className="text-3xl font-black mb-4">
                            {isRomanian ? 'Coșul Tău Este Gol' : 'Your Cart is Empty'}
                        </h1>
                        <p className="text-muted-foreground mb-8">
                            {isRomanian 
                                ? 'Adaugă competiții în coș pentru a rezerva locuri'
                                : 'Add competitions to your cart to reserve spots'
                            }
                        </p>
                        <Link to="/competitions">
                            <Button className="btn-primary">
                                {isRomanian ? 'Vezi Competițiile' : 'Browse Competitions'}
                                <ArrowRight className="w-4 h-4 ml-2" />
                            </Button>
                        </Link>
                    </div>
                </main>
                <Footer />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            <Navbar />
            
            <main className="pt-24 pb-16">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="flex items-center gap-4 mb-8">
                        <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                            <ShoppingCart className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-black">
                                {isRomanian ? 'Coșul Tău' : 'Your Cart'}
                            </h1>
                            <p className="text-muted-foreground">
                                {totalItems} {totalItems === 1 
                                    ? (isRomanian ? 'loc' : 'spot') 
                                    : (isRomanian ? 'locuri' : 'spots')
                                }
                            </p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Cart Items */}
                        <div className="lg:col-span-2 space-y-4">
                            {items.map((item) => (
                                <Card key={item.competition_id} className="glass border-white/10">
                                    <CardContent className="p-4">
                                        <div className="flex gap-4">
                                            <img 
                                                src={item.image_url || 'https://images.unsplash.com/photo-1579548122080-c35fd6820ecb?w=200'} 
                                                alt={item.title}
                                                className="w-24 h-24 object-cover rounded-xl"
                                            />
                                            <div className="flex-1">
                                                <h3 className="font-bold mb-1">{item.title}</h3>
                                                <p className="text-sm text-muted-foreground mb-3">
                                                    RON {item.ticket_price.toFixed(2)} {isRomanian ? 'per loc' : 'per spot'}
                                                </p>
                                                
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-2">
                                                        <Button
                                                            variant="outline"
                                                            size="icon"
                                                            className="h-8 w-8"
                                                            onClick={() => updateQuantity(item.competition_id, item.quantity - 1)}
                                                        >
                                                            <Minus className="w-3 h-3" />
                                                        </Button>
                                                        <span className="font-mono font-bold w-8 text-center">{item.quantity}</span>
                                                        <Button
                                                            variant="outline"
                                                            size="icon"
                                                            className="h-8 w-8"
                                                            onClick={() => updateQuantity(item.competition_id, item.quantity + 1)}
                                                            disabled={item.quantity >= item.max_available}
                                                        >
                                                            <Plus className="w-3 h-3" />
                                                        </Button>
                                                    </div>
                                                    
                                                    <div className="flex items-center gap-4">
                                                        <span className="font-bold text-lg">
                                                            RON {(item.quantity * item.ticket_price).toFixed(2)}
                                                        </span>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            className="text-destructive hover:bg-destructive/10"
                                                            onClick={() => removeFromCart(item.competition_id)}
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </Button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>

                        {/* Order Summary */}
                        <div>
                            <Card className="glass border-primary/30 sticky top-24">
                                <CardHeader>
                                    <CardTitle>{isRomanian ? 'Sumar Comandă' : 'Order Summary'}</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">
                                            {isRomanian ? 'Subtotal' : 'Subtotal'}
                                        </span>
                                        <span>RON {totalPrice.toFixed(2)}</span>
                                    </div>
                                    <div className="border-t border-white/10 pt-4">
                                        <div className="flex justify-between text-lg font-bold">
                                            <span>{isRomanian ? 'Total' : 'Total'}</span>
                                            <span className="gradient-text">RON {totalPrice.toFixed(2)}</span>
                                        </div>
                                    </div>

                                    {isAuthenticated && (
                                        <div className="flex items-center gap-3 p-3 rounded-xl border border-primary/20 bg-primary/5">
                                            <CreditCard className="w-5 h-5 text-primary" />
                                            <div className="flex-1 text-left">
                                                <p className="font-medium">{isRomanian ? 'Plată Securizată' : 'Secure Payment'}</p>
                                                <p className="text-xs text-muted-foreground">Visa, Mastercard, Apple Pay, Google Pay</p>
                                            </div>
                                        </div>
                                    )}

                                    <Button
                                        className="w-full btn-secondary text-black"
                                        onClick={handleCheckout}
                                        disabled={loading}
                                        data-testid="checkout-btn"
                                    >
                                        {loading ? (
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                        ) : isAuthenticated ? (
                                            isRomanian ? 'Finalizează Comanda' : 'Complete Purchase'
                                        ) : (
                                            isRomanian ? 'Autentifică-te' : 'Log In'
                                        )}
                                    </Button>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default CartPage;
