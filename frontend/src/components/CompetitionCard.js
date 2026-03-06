import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useCart } from '../context/CartContext';
import CountdownTimer from './CountdownTimer';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Zap, Clock, Ticket, ShoppingCart, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

const CompetitionCard = ({ competition, featured = false }) => {
    const { isRomanian } = useLanguage();
    const { addToCart } = useCart();

    const soldPercentage = (competition.sold_tickets / competition.max_tickets) * 100;
    const available = competition.max_tickets - competition.sold_tickets;
    
    // Determine urgency level
    const getUrgencyClass = () => {
        if (soldPercentage >= 80) return 'progress-urgency-high';
        if (soldPercentage >= 50) return 'progress-urgency-medium';
        return 'progress-urgency-low';
    };

    const getCategoryLabel = () => {
        const labels = {
            'instant_wins': isRomanian ? 'Premiu Instant' : 'Instant Prize',
            'tech': isRomanian ? 'Tehnologie' : 'Tech',
            'cash': isRomanian ? 'Bani' : 'Cash',
            'cars': isRomanian ? 'Mașini' : 'Cars',
            'other': isRomanian ? 'Altele' : 'Other'
        };
        return labels[competition.category] || labels.other;
    };

    const handleQuickAdd = (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        if (competition.qualification_question) {
            toast.info(isRomanian ? 'Te rugăm să răspunzi la întrebarea de calificare' : 'Please answer the qualification question');
            return;
        }
        
        addToCart(competition, 1, null);
        toast.success(isRomanian ? 'Adăugat în coș!' : 'Added to cart!');
    };

    return (
        <Link 
            to={`/competitions/${competition.competition_id}`}
            className={`bento-item card-hover block ${featured ? 'md:col-span-2 md:row-span-2' : ''}`}
            data-testid={`competition-card-${competition.competition_id}`}
        >
            {/* Image */}
            <div className="relative aspect-video overflow-hidden">
                <img 
                    src={competition.image_url || 'https://images.unsplash.com/photo-1579548122080-c35fd6820ecb?w=800'} 
                    alt={competition.title}
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                />
                
                {/* Overlay gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-card via-transparent to-transparent" />
                
                {/* Badges */}
                <div className="absolute top-4 left-4 flex gap-2">
                    {competition.competition_type === 'instant_win' ? (
                        <Badge className="badge-instant">
                            <Zap className="w-3 h-3 mr-1" />
                            {isRomanian ? 'Instant' : 'Instant'}
                        </Badge>
                    ) : (
                        <Badge className="badge-classic">
                            <Clock className="w-3 h-3 mr-1" />
                            {isRomanian ? 'Clasic' : 'Classic'}
                        </Badge>
                    )}
                    <Badge className="badge-muted">{getCategoryLabel()}</Badge>
                </div>

                {/* Sold percentage overlay */}
                {soldPercentage >= 70 && (
                    <div className="absolute top-4 right-4">
                        <Badge className={soldPercentage >= 90 ? 'status-ending' : 'badge-secondary'}>
                            {Math.round(soldPercentage)}% {isRomanian ? 'Vândut' : 'Sold'}
                        </Badge>
                    </div>
                )}

                {/* Flash Sale Badge */}
                {competition.flash_sale?.active && (
                    <div className="absolute top-4 right-4 animate-pulse">
                        <Badge className="bg-orange-500 text-white border-none shadow-lg shadow-orange-500/30">
                            ⚡ -{competition.flash_sale.discount_percent}% FLASH
                        </Badge>
                    </div>
                )}
            </div>

            {/* Progress bar */}
            <div className={`h-1 ${getUrgencyClass()}`}>
                <div className="progress-bar h-full">
                    <div 
                        className="progress-fill" 
                        style={{ width: `${soldPercentage}%` }}
                    />
                </div>
            </div>

            {/* Content */}
            <div className="p-5">
                <h3 className={`font-bold mb-2 line-clamp-2 ${featured ? 'text-2xl' : 'text-lg'}`}>
                    {competition.title}
                </h3>
                
                {featured && (
                    <p className="text-muted-foreground text-sm mb-4 line-clamp-2">
                        {competition.description}
                    </p>
                )}

                {/* Stats */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Ticket className="w-4 h-4" />
                        <span className="font-mono">{available}</span>
                        <span>{isRomanian ? 'rămase' : 'left'}</span>
                    </div>
                    <div className="price-display text-xl">
                        {competition.flash_sale?.active ? (
                            <>
                                <span className="line-through text-muted-foreground text-sm mr-2">
                                    RON {competition.flash_sale.original_price?.toFixed(2)}
                                </span>
                                <span className="text-orange-500">
                                    RON {competition.flash_sale.flash_price?.toFixed(2)}
                                </span>
                            </>
                        ) : (
                            <>RON {competition.ticket_price.toFixed(2)}</>
                        )}
                    </div>
                </div>

                {/* Countdown */}
                {competition.draw_date && (
                    <div className="mb-4">
                        <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider">
                            {isRomanian ? 'Extragere în' : 'Draw in'}
                        </p>
                        <CountdownTimer targetDate={competition.draw_date} compact />
                    </div>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                    <Button 
                        className="flex-1 btn-primary text-sm py-3"
                        data-testid={`view-details-${competition.competition_id}`}
                    >
                        {isRomanian ? 'Vezi Detalii' : 'View Details'}
                        <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                    {!competition.qualification_question && available > 0 && (
                        <Button 
                            variant="outline"
                            className="btn-outline px-3"
                            onClick={handleQuickAdd}
                            data-testid={`quick-add-${competition.competition_id}`}
                        >
                            <ShoppingCart className="w-4 h-4" />
                        </Button>
                    )}
                </div>
            </div>
        </Link>
    );
};

export default CompetitionCard;
