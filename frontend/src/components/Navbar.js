import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useCart } from '../context/CartContext';
import { Button } from '../components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '../components/ui/dropdown-menu';
import { Sheet, SheetContent, SheetTrigger, SheetClose } from '../components/ui/sheet';
import { Menu, User, LogOut, LayoutDashboard, Ticket, Shield, ShoppingCart, ChevronDown, X } from 'lucide-react';
import AnimatedLogo from './AnimatedLogo';

// TikTok Icon Component
const TikTokIcon = ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
    </svg>
);

const Navbar = () => {
    const { user, isAuthenticated, isAdmin, logout } = useAuth();
    const { t, language, toggleLanguage, isRomanian } = useLanguage();
    const { totalItems } = useCart();
    const location = useLocation();

    const navLinks = [
        { href: '/competitions', label: isRomanian ? 'Competiții' : 'Competitions', icon: '🎯' },
        { href: '/winners', label: isRomanian ? 'Premianți' : 'Winners', icon: '🏆' },
        { href: '/search', label: isRomanian ? 'Caută Locuri' : 'Find Spots', icon: '🔍' },
        { href: '/faq', label: isRomanian ? 'Întrebări' : 'FAQ', icon: '❓' },
    ];

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0614]/95 backdrop-blur-md border-b border-white/5">
            <div className="max-w-7xl mx-auto px-4 sm:px-6">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link to="/" className="flex items-center" data-testid="navbar-logo">
                        <AnimatedLogo size="default" />
                    </Link>

                    {/* Desktop Navigation - Center */}
                    <div className="hidden lg:flex items-center gap-1">
                        {navLinks.map((link) => (
                            <Link
                                key={link.href}
                                to={link.href}
                                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                                    isActive(link.href) 
                                        ? 'bg-primary/10 text-primary' 
                                        : 'text-gray-300 hover:text-white hover:bg-white/5'
                                }`}
                                data-testid={`nav-link-${link.href.replace('/', '')}`}
                            >
                                <span>{link.icon}</span>
                                <span>{link.label}</span>
                            </Link>
                        ))}
                        
                        {/* TikTok Link */}
                        <a
                            href="https://www.tiktok.com/@x67digital.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 transition-all"
                            data-testid="tiktok-link"
                        >
                            <TikTokIcon className="w-4 h-4" />
                        </a>
                    </div>

                    {/* Right Side */}
                    <div className="flex items-center gap-2">
                        {/* Language Toggle */}
                        <button
                            onClick={toggleLanguage}
                            className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-bold text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                            data-testid="language-toggle"
                        >
                            <span className="w-5 h-5 rounded-full overflow-hidden flex items-center justify-center bg-white/10">
                                {language === 'ro' ? '🇷🇴' : '🇬🇧'}
                            </span>
                            <span>{language.toUpperCase()}</span>
                        </button>

                        {/* Cart Button */}
                        <Link to="/cart" className="relative" data-testid="cart-btn">
                            <button className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all relative">
                                <ShoppingCart className="w-5 h-5" />
                                {totalItems > 0 && (
                                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-primary text-white text-xs font-bold rounded-full flex items-center justify-center">
                                        {totalItems}
                                    </span>
                                )}
                            </button>
                        </Link>

                        {isAuthenticated ? (
                            <>
                                {/* User Menu */}
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <button className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/5 transition-all" data-testid="user-menu-btn">
                                            <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center overflow-hidden">
                                                {user?.picture ? (
                                                    <img src={user.picture} alt={user.username} className="w-full h-full object-cover" />
                                                ) : (
                                                    <User className="w-4 h-4 text-primary" />
                                                )}
                                            </div>
                                            <ChevronDown className="w-4 h-4 text-gray-400 hidden sm:block" />
                                        </button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent className="w-56 bg-[#1a1625] border-white/10" align="end">
                                        <div className="px-3 py-2 border-b border-white/10">
                                            <p className="text-sm font-medium text-white">{user?.username}</p>
                                            <p className="text-xs text-gray-400">{user?.email}</p>
                                        </div>
                                        <div className="p-1">
                                            <DropdownMenuItem asChild>
                                                <Link to="/dashboard" className="flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer hover:bg-white/5" data-testid="menu-dashboard">
                                                    <LayoutDashboard className="w-4 h-4 text-gray-400" />
                                                    <span>{t('nav_dashboard')}</span>
                                                </Link>
                                            </DropdownMenuItem>
                                            <DropdownMenuItem asChild>
                                                <Link to="/dashboard/tickets" className="flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer hover:bg-white/5" data-testid="menu-tickets">
                                                    <Ticket className="w-4 h-4 text-gray-400" />
                                                    <span>{t('nav_my_locs')}</span>
                                                </Link>
                                            </DropdownMenuItem>
                                            {isAdmin && (
                                                <DropdownMenuItem asChild>
                                                    <Link to="/admin" className="flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer hover:bg-white/5 text-primary" data-testid="menu-admin">
                                                        <Shield className="w-4 h-4" />
                                                        <span>Admin</span>
                                                    </Link>
                                                </DropdownMenuItem>
                                            )}
                                        </div>
                                        <div className="border-t border-white/10 p-1">
                                            <DropdownMenuItem onClick={logout} className="flex items-center gap-2 px-2 py-2 rounded-md cursor-pointer hover:bg-red-500/10 text-red-400" data-testid="menu-logout">
                                                <LogOut className="w-4 h-4" />
                                                <span>{t('nav_logout')}</span>
                                            </DropdownMenuItem>
                                        </div>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </>
                        ) : (
                            <div className="flex items-center gap-2">
                                <Link to="/login">
                                    <button className="hidden sm:block px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors" data-testid="nav-login-btn">
                                        {isRomanian ? 'Conectare' : 'Login'}
                                    </button>
                                </Link>
                                <Link to="/login">
                                    <button className="px-4 py-2 bg-primary hover:bg-primary/90 text-white text-sm font-semibold rounded-lg transition-all" data-testid="nav-signup-btn">
                                        {isRomanian ? 'Creează cont' : 'Sign Up'}
                                    </button>
                                </Link>
                            </div>
                        )}

                        {/* Mobile Menu */}
                        <Sheet>
                            <SheetTrigger asChild className="lg:hidden">
                                <button className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all" data-testid="mobile-menu-btn">
                                    <Menu className="w-6 h-6" />
                                </button>
                            </SheetTrigger>
                            <SheetContent side="right" className="w-full sm:w-[320px] p-0 border-l border-white/10 bg-[#0a0614]">
                                {/* Mobile Header */}
                                <div className="flex items-center justify-between p-4 border-b border-white/10">
                                    <AnimatedLogo size="default" />
                                    <SheetClose asChild>
                                        <button className="p-2 rounded-lg hover:bg-white/5">
                                            <X className="w-5 h-5" />
                                        </button>
                                    </SheetClose>
                                </div>

                                {/* Mobile User Info */}
                                {isAuthenticated && (
                                    <div className="p-4 border-b border-white/10 bg-white/5">
                                        <div className="flex items-center gap-3">
                                            <div className="w-12 h-12 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center">
                                                {user?.picture ? (
                                                    <img src={user.picture} alt="" className="w-full h-full rounded-full object-cover" />
                                                ) : (
                                                    <User className="w-6 h-6 text-primary" />
                                                )}
                                            </div>
                                            <div>
                                                <p className="font-semibold text-white">{user?.username}</p>
                                                <p className="text-sm text-gray-400">{user?.email}</p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Mobile Navigation */}
                                <div className="p-4 space-y-1">
                                    {navLinks.map((link) => (
                                        <SheetClose asChild key={link.href}>
                                            <Link
                                                to={link.href}
                                                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                                                    isActive(link.href)
                                                        ? 'bg-primary/10 text-primary'
                                                        : 'text-gray-300 hover:bg-white/5'
                                                }`}
                                            >
                                                <span className="text-lg">{link.icon}</span>
                                                <span>{link.label}</span>
                                            </Link>
                                        </SheetClose>
                                    ))}
                                    
                                    {isAuthenticated && (
                                        <>
                                            <div className="border-t border-white/10 my-3"></div>
                                            <SheetClose asChild>
                                                <Link to="/dashboard" className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-300 hover:bg-white/5">
                                                    <LayoutDashboard className="w-5 h-5" />
                                                    <span>{t('nav_dashboard')}</span>
                                                </Link>
                                            </SheetClose>
                                            {isAdmin && (
                                                <SheetClose asChild>
                                                    <Link to="/admin" className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-primary hover:bg-primary/10">
                                                        <Shield className="w-5 h-5" />
                                                        <span>Admin Panel</span>
                                                    </Link>
                                                </SheetClose>
                                            )}
                                        </>
                                    )}
                                </div>

                                {/* Mobile Footer */}
                                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10">
                                    {isAuthenticated ? (
                                        <button
                                            onClick={logout}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 text-red-400 font-medium hover:bg-red-500/20 transition-all"
                                        >
                                            <LogOut className="w-5 h-5" />
                                            <span>{t('nav_logout')}</span>
                                        </button>
                                    ) : (
                                        <div className="space-y-2">
                                            <SheetClose asChild>
                                                <Link to="/login" className="block">
                                                    <button className="w-full px-4 py-3 rounded-xl bg-primary text-white font-semibold hover:bg-primary/90 transition-all">
                                                        {isRomanian ? 'Creează cont' : 'Sign Up'}
                                                    </button>
                                                </Link>
                                            </SheetClose>
                                            <SheetClose asChild>
                                                <Link to="/login" className="block">
                                                    <button className="w-full px-4 py-3 rounded-xl border border-white/10 text-gray-300 font-medium hover:bg-white/5 transition-all">
                                                        {isRomanian ? 'Conectare' : 'Login'}
                                                    </button>
                                                </Link>
                                            </SheetClose>
                                        </div>
                                    )}
                                </div>
                            </SheetContent>
                        </Sheet>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
