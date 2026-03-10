import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';

const CountdownTimer = ({ targetDate, compact = false, onExpire }) => {
    const { isRomanian } = useLanguage();
    const [timeLeft, setTimeLeft] = useState(calculateTimeLeft());

    function calculateTimeLeft() {
        const difference = new Date(targetDate) - new Date();
        
        if (difference <= 0) {
            return { expired: true };
        }

        return {
            days: Math.floor(difference / (1000 * 60 * 60 * 24)),
            hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
            minutes: Math.floor((difference / 1000 / 60) % 60),
            seconds: Math.floor((difference / 1000) % 60),
            expired: false
        };
    }

    useEffect(() => {
        const timer = setInterval(() => {
            const newTimeLeft = calculateTimeLeft();
            setTimeLeft(newTimeLeft);
            if (newTimeLeft.expired && onExpire) {
                onExpire();
            }
        }, 1000);

        return () => clearInterval(timer);
    }, [targetDate]);

    if (timeLeft.expired) {
        return (
            <div className="text-destructive font-bold">
                {isRomanian ? 'Expirat' : 'Expired'}
            </div>
        );
    }

    const isUrgent = timeLeft.days === 0 && timeLeft.hours < 24;

    if (compact) {
        return (
            <div className={`font-mono text-sm font-bold ${isUrgent ? 'text-destructive animate-countdown' : 'text-muted-foreground'}`}>
                {timeLeft.days > 0 && `${timeLeft.days}z `}
                {String(timeLeft.hours).padStart(2, '0')}:
                {String(timeLeft.minutes).padStart(2, '0')}:
                {String(timeLeft.seconds).padStart(2, '0')}
            </div>
        );
    }

    return (
        <div className="countdown-container">
            {timeLeft.days > 0 && (
                <div className={`countdown-box ${isUrgent ? 'urgent' : ''}`}>
                    <span className="countdown-number">{timeLeft.days}</span>
                    <span className="countdown-label">{isRomanian ? 'Zile' : 'Days'}</span>
                </div>
            )}
            <div className={`countdown-box ${isUrgent ? 'urgent' : ''}`}>
                <span className="countdown-number">{String(timeLeft.hours).padStart(2, '0')}</span>
                <span className="countdown-label">{isRomanian ? 'Ore' : 'Hours'}</span>
            </div>
            <div className={`countdown-box ${isUrgent ? 'urgent' : ''}`}>
                <span className="countdown-number">{String(timeLeft.minutes).padStart(2, '0')}</span>
                <span className="countdown-label">{isRomanian ? 'Min' : 'Min'}</span>
            </div>
            <div className={`countdown-box ${isUrgent ? 'urgent' : ''}`}>
                <span className="countdown-number">{String(timeLeft.seconds).padStart(2, '0')}</span>
                <span className="countdown-label">{isRomanian ? 'Sec' : 'Sec'}</span>
            </div>
        </div>
    );
};

export default CountdownTimer;
