import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { XCircle, ArrowLeft, RefreshCw, MessageCircle, Home } from 'lucide-react';

const PaymentFailedPage = () => {
    const [searchParams] = useSearchParams();
    const { isRomanian } = useLanguage();
    
    const errorCode = searchParams.get('error');
    const orderId = searchParams.get('orderId');

    const getErrorMessage = () => {
        switch (errorCode) {
            case 'cancelled':
                return isRomanian ? 'Ai anulat plata.' : 'You cancelled the payment.';
            case 'declined':
                return isRomanian ? 'Cardul a fost refuzat.' : 'Your card was declined.';
            case 'insufficient_funds':
                return isRomanian ? 'Fonduri insuficiente.' : 'Insufficient funds.';
            case 'expired':
                return isRomanian ? 'Sesiunea de plată a expirat.' : 'Payment session expired.';
            default:
                return isRomanian 
                    ? 'A apărut o eroare la procesarea plății.' 
                    : 'An error occurred while processing your payment.';
        }
    };

    return (
        <div className="min-h-screen bg-background flex flex-col">
            <Navbar />
            
            <main className="flex-1 flex items-center justify-center p-4 pt-24">
                <Card className="w-full max-w-lg glass border-destructive/30">
                    <CardContent className="p-8 text-center">
                        {/* Error Icon */}
                        <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center">
                            <XCircle className="w-12 h-12 text-white" />
                        </div>

                        {/* Title */}
                        <h1 className="text-3xl font-black mb-2 text-destructive">
                            {isRomanian ? 'Plată Nereușită' : 'Payment Failed'}
                        </h1>
                        <p className="text-muted-foreground mb-6">
                            {getErrorMessage()}
                        </p>

                        {/* Error Details */}
                        {(errorCode || orderId) && (
                            <div className="bg-destructive/10 border border-destructive/30 rounded-2xl p-4 mb-6 text-left">
                                <p className="text-sm text-muted-foreground">
                                    {isRomanian ? 'Detalii eroare:' : 'Error details:'}
                                </p>
                                {errorCode && (
                                    <p className="font-mono text-sm mt-1">
                                        {isRomanian ? 'Cod' : 'Code'}: {errorCode}
                                    </p>
                                )}
                                {orderId && (
                                    <p className="font-mono text-sm mt-1">
                                        {isRomanian ? 'Referință' : 'Reference'}: {orderId}
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Suggestions */}
                        <div className="bg-black/30 rounded-2xl p-6 mb-6 text-left">
                            <h3 className="font-bold mb-3">
                                {isRomanian ? 'Ce poți face:' : 'What you can do:'}
                            </h3>
                            <ul className="space-y-2 text-sm text-muted-foreground">
                                <li className="flex items-start gap-2">
                                    <span className="text-primary">•</span>
                                    {isRomanian 
                                        ? 'Verifică datele cardului și încearcă din nou'
                                        : 'Check your card details and try again'
                                    }
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-primary">•</span>
                                    {isRomanian 
                                        ? 'Folosește un alt card sau metodă de plată'
                                        : 'Use a different card or payment method'
                                    }
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-primary">•</span>
                                    {isRomanian 
                                        ? 'Contactează banca pentru mai multe detalii'
                                        : 'Contact your bank for more details'
                                    }
                                </li>
                            </ul>
                        </div>

                        {/* Actions */}
                        <div className="space-y-3">
                            <Link to="/competitions" className="block">
                                <Button className="w-full btn-primary">
                                    <RefreshCw className="w-4 h-4 mr-2" />
                                    {isRomanian ? 'Încearcă Din Nou' : 'Try Again'}
                                </Button>
                            </Link>
                            <Link to="/" className="block">
                                <Button variant="outline" className="w-full btn-outline">
                                    <Home className="w-4 h-4 mr-2" />
                                    {isRomanian ? 'Acasă' : 'Home'}
                                </Button>
                            </Link>
                            <a 
                                href="mailto:support@zektrix.uk" 
                                className="block text-sm text-muted-foreground hover:text-primary transition-colors"
                            >
                                <MessageCircle className="w-4 h-4 inline mr-1" />
                                {isRomanian ? 'Contactează Suportul' : 'Contact Support'}
                            </a>
                        </div>
                    </CardContent>
                </Card>
            </main>

            <Footer />
        </div>
    );
};

export default PaymentFailedPage;
