import React, { useState, useEffect, useRef } from 'react';
import { useLanguage } from '../context/LanguageContext';

const CountdownTimer = ({ targetDate, compact = false, onExpire }) => {
    const { isRomanian } = useLanguage();
    
    const calcTimeLeft = () => {
        const diff = new Date(targetDate) - new Date();
        if (diff <= 0) return { expired: true };
        return {
            days: Math.floor(diff / 86400000),
            hours: Math.floor((diff / 3600000) % 24),
            minutes: Math.floor((diff / 60000) % 60),
            seconds: Math.floor((diff / 1000) % 60),
            expired: false
        };
    };

    const [timeLeft, setTimeLeft] = useState(calcTimeLeft);

    useEffect(() => {
        // Use 1s interval only for compact (detail page), 30s for card views
        const interval = compact ? 30000 : 1000;
        const timer = setInterval(() => {
            const t = calcTimeLeft();
            setTimeLeft(t);
            if (t.expired && onExpire) onExpire();
        }, interval);
        return () => clearInterval(timer);
    }, [targetDate]);

    if (timeLeft.expired) {
        return <span className="text-red-400 font-bold text-xs">{isRomanian ? 'Expirat' : 'Expired'}</span>;
    }

    if (compact) {
        const urgent = timeLeft.days === 0;
        return (
            <span className={`font-mono text-xs font-bold ${urgent ? 'text-red-400' : 'text-gray-400'}`}>
                {timeLeft.days > 0 && `${timeLeft.days}z `}
                {String(timeLeft.hours).padStart(2, '0')}:{String(timeLeft.minutes).padStart(2, '0')}
            </span>
        );
    }

    const urgent = timeLeft.days === 0 && timeLeft.hours < 24;
    return (
        <div className="countdown-container">
            {timeLeft.days > 0 && (
                <div className={`countdown-box ${urgent ? 'urgent' : ''}`}>
                    <span className="countdown-number">{timeLeft.days}</span>
                    <span className="countdown-label">{isRomanian ? 'Zile' : 'Days'}</span>
                </div>
            )}
            <div className={`countdown-box ${urgent ? 'urgent' : ''}`}>
                <span className="countdown-number">{String(timeLeft.hours).padStart(2, '0')}</span>
                <span className="countdown-label">{isRomanian ? 'Ore' : 'Hours'}</span>
            </div>
            <div className={`countdown-box ${urgent ? 'urgent' : ''}`}>
                <span className="countdown-number">{String(timeLeft.minutes).padStart(2, '0')}</span>
                <span className="countdown-label">{isRomanian ? 'Min' : 'Min'}</span>
            </div>
            <div className={`countdown-box ${urgent ? 'urgent' : ''}`}>
                <span className="countdown-number">{String(timeLeft.seconds).padStart(2, '0')}</span>
                <span className="countdown-label">{isRomanian ? 'Sec' : 'Sec'}</span>
            </div>
        </div>
    );
};

export default CountdownTimer;
