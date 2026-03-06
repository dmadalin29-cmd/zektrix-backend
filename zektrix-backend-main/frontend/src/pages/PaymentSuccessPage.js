import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { CheckCircle, ArrowRight, Ticket, Home, Loader2 } from 'lucide-react';
import axios from 'axios';
import confetti from 'canvas-confetti';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PaymentSuccessPage = () => {
    const [searchParams] = useSearchParams();
    const { isRomanian } = useLanguage();
    const [loading, setLoading] = useState(true);
    const [tickets, setTickets] = useState([]);
    const [orderDetails, setOrderDetails] = useState(null);
    
    const orderId = searchParams.get('orderId');
    const transactionId = searchParams.get('t');

    useEffect(() => {
        // Confetti celebration
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#8b5cf6', '#f97316', '#00ffff', '#fbbf24']
        });

        // Fetch order details
        if (orderId || transactionId) {
            fetchOrderDetails();
        } else {
            setLoading(false);
        }
    }, [orderId, transactionId]);

    const fetchOrderDetails = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API}/payments/verify`, {
                params: { orderId, transactionId },
                headers: { Authorization: `Bearer ${token}` }
            });
            setOrderDetails(response.data);
            setTickets(response.data.tickets || []);
        } catch (error) {
            console.error('Failed to fetch order:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex flex-col">
            <Navbar />
            
            <main className="flex-1 flex items-center justify-center p-4 pt-24">
                <Card className="w-full max-w-lg glass border-green-500/30">
                    <CardContent className="p-8 text-center">
                        {loading ? (
                            <div className="py-12">
                                <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
                                <p className="mt-4 text-muted-foreground">
                                    {isRomanian ? 'Se procesează plata...' : 'Processing payment...'}
                                </p>
                            </div>
                        ) : (
                            <>
                                {/* Success Icon */}
                                <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center animate-pulse-glow">
                                    <CheckCircle className="w-12 h-12 text-white" />
                                </div>

                                {/* Title */}
                                <h1 className="text-3xl font-black mb-2 gradient-text">
                                    {isRomanian ? 'Plată Reușită!' : 'Payment Successful!'}
                                </h1>
                                <p className="text-muted-foreground mb-8">
                                    {isRomanian 
                                        ? 'Mulțumim pentru achiziție! Locurile tale au fost rezervate.'
                                        : 'Thank you for your purchase! Your spots have been reserved.'
                                    }
                                </p>

                                {/* Order Details */}
                                {orderDetails && (
                                    <div className="bg-black/30 rounded-2xl p-6 mb-6 text-left">
                                        <h3 className="font-bold mb-4 flex items-center gap-2">
                                            <Ticket className="w-5 h-5 text-primary" />
                                            {isRomanian ? 'Detalii Comandă' : 'Order Details'}
                                        </h3>
                                        <div className="space-y-2 text-sm">
                                            <div className="flex justify-between">
                                                <span className="text-muted-foreground">
                                                    {isRomanian ? 'ID Tranzacție' : 'Transaction ID'}
                                                </span>
                                                <span className="font-mono">{transactionId || orderId}</span>
                                            </div>
                                            {orderDetails.amount && (
                                                <div className="flex justify-between">
                                                    <span className="text-muted-foreground">
                                                        {isRomanian ? 'Sumă' : 'Amount'}
                                                    </span>
                                                    <span className="font-bold text-green-400">
                                                        RON {orderDetails.amount?.toFixed(2)}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Tickets */}
                                {tickets.length > 0 && (
                                    <div className="bg-primary/10 border border-primary/30 rounded-2xl p-6 mb-6">
                                        <h3 className="font-bold mb-3">
                                            {isRomanian ? 'Codurile Tale' : 'Your Codes'}
                                        </h3>
                                        <div className="grid grid-cols-3 gap-2">
                                            {tickets.map((ticket, idx) => (
                                                <div key={idx} className="bg-black/30 rounded-lg p-2 font-mono text-sm text-primary">
                                                    {ticket.ticket_code}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Actions */}
                                <div className="space-y-3">
                                    <Link to="/dashboard" className="block">
                                        <Button className="w-full btn-primary">
                                            <Ticket className="w-4 h-4 mr-2" />
                                            {isRomanian ? 'Vezi Locurile Mele' : 'View My Tickets'}
                                            <ArrowRight className="w-4 h-4 ml-2" />
                                        </Button>
                                    </Link>
                                    <Link to="/competitions" className="block">
                                        <Button variant="outline" className="w-full btn-outline">
                                            {isRomanian ? 'Participă la Mai Multe' : 'Join More Competitions'}
                                        </Button>
                                    </Link>
                                </div>
                            </>
                        )}
                    </CardContent>
                </Card>
            </main>

            <Footer />
        </div>
    );
};

export default PaymentSuccessPage;
