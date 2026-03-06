import React, { createContext, useContext, useState, useEffect } from 'react';

const CartContext = createContext();

export const useCart = () => {
    const context = useContext(CartContext);
    if (!context) {
        throw new Error('useCart must be used within a CartProvider');
    }
    return context;
};

export const CartProvider = ({ children }) => {
    const [items, setItems] = useState(() => {
        const saved = localStorage.getItem('zektrix_cart');
        return saved ? JSON.parse(saved) : [];
    });

    useEffect(() => {
        localStorage.setItem('zektrix_cart', JSON.stringify(items));
    }, [items]);

    const addToCart = (competition, quantity, qualificationAnswer) => {
        setItems(prev => {
            const existing = prev.find(item => item.competition_id === competition.competition_id);
            if (existing) {
                return prev.map(item =>
                    item.competition_id === competition.competition_id
                        ? { ...item, quantity: item.quantity + quantity }
                        : item
                );
            }
            return [...prev, {
                competition_id: competition.competition_id,
                title: competition.title,
                ticket_price: competition.ticket_price,
                image_url: competition.image_url,
                quantity,
                qualification_answer: qualificationAnswer,
                max_available: competition.max_tickets - competition.sold_tickets
            }];
        });
    };

    const removeFromCart = (competitionId) => {
        setItems(prev => prev.filter(item => item.competition_id !== competitionId));
    };

    const updateQuantity = (competitionId, quantity) => {
        if (quantity <= 0) {
            removeFromCart(competitionId);
            return;
        }
        setItems(prev =>
            prev.map(item =>
                item.competition_id === competitionId
                    ? { ...item, quantity: Math.min(quantity, item.max_available) }
                    : item
            )
        );
    };

    const clearCart = () => {
        setItems([]);
    };

    const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
    const totalPrice = items.reduce((sum, item) => sum + item.quantity * item.ticket_price, 0);

    return (
        <CartContext.Provider value={{
            items,
            addToCart,
            removeFromCart,
            updateQuantity,
            clearCart,
            totalItems,
            totalPrice
        }}>
            {children}
        </CartContext.Provider>
    );
};

export default CartContext;
