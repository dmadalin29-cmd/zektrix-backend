import React from 'react';
import './AnimatedLogo.css';

const AnimatedLogo = ({ size = 'default' }) => {
    const sizeClasses = {
        small: 'text-lg',
        default: 'text-xl',
        large: 'text-2xl',
        xlarge: 'text-3xl'
    };

    return (
        <span className={`animated-logo font-black tracking-tight ${sizeClasses[size]}`}>
            <span className="logo-gradient">ZEKTRIX</span>
            <span className="text-white">.UK</span>
        </span>
    );
};

export default AnimatedLogo;
