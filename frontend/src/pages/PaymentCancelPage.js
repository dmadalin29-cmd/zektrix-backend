import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { ArrowLeft, ShoppingCart, Home } from 'lucide-react';

const PaymentCancelPage = () => {
    const { isRomanian } = useLanguage();

    return (
        <div className="min-h-screen bg-background flex flex-col">
            <Navbar />
            
            <main className="flex-1 flex items-center justify-center p-4 pt-24">
                <Card className="w-full max-w-lg glass border-yellow-500/30" data-testid="payment-cancel-page">
                    <CardContent className="p-8 text-center">
                        <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-yellow-500 to-amber-600 flex items-center justify-center">
                            <ArrowLeft className="w-12 h-12 text-white" />
                        </div>

                        <h1 className="text-3xl font-black mb-2 text-yellow-400">
                            {isRomanian ? 'Plată Anulată' : 'Payment Cancelled'}
                        </h1>
                        <p className="text-muted-foreground mb-8">
                            {isRomanian 
                                ? 'Ai anulat plata. Nu a fost debitată nicio sumă de pe cardul tău.'
                                : 'You cancelled the payment. No amount was charged to your card.'}
                        </p>

                        <div className="space-y-3">
                            <Link to="/competitions" className="block">
                                <Button className="w-full btn-primary" data-testid="back-to-competitions-btn">
                                    <ShoppingCart className="w-4 h-4 mr-2" />
                                    {isRomanian ? 'Înapoi la Competiții' : 'Back to Competitions'}
                                </Button>
                            </Link>
                            <Link to="/" className="block">
                                <Button variant="outline" className="w-full btn-outline" data-testid="back-to-home-btn">
                                    <Home className="w-4 h-4 mr-2" />
                                    {isRomanian ? 'Acasă' : 'Home'}
                                </Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </main>

            <Footer />
        </div>
    );
};

export default PaymentCancelPage;
