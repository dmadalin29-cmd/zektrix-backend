import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useCart } from '../context/CartContext';
import { Button } from '../components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../components/ui/dropdown-menu';
import { Sheet, SheetContent, SheetTrigger, SheetClose } from '../components/ui/sheet';
import { Menu, User, LogOut, LayoutDashboard, Ticket, Shield, ShoppingCart, ChevronDown, X, Trophy, Search, HelpCircle, Crosshair, Wallet, Crown } from 'lucide-react';
import AnimatedLogo from './AnimatedLogo';
import UserNotificationBell from './UserNotificationBell';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TikTokIcon = ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
    </svg>
);

const Navbar = () => {
    const { user, isAuthenticated, isAdmin, logout, token } = useAuth();
    const { t, language, toggleLanguage, isRomanian } = useLanguage();
    const { totalItems } = useCart();
    const location = useLocation();
    const [walletBalance, setWalletBalance] = React.useState(null);

    React.useEffect(() => {
        if (token) {
            axios.get(`${API}/wallet/balance`, { headers: { Authorization: `Bearer ${token}` }})
                .then(r => setWalletBalance(r.data.balance || 0))
                .catch(() => {});
        }
    }, [token]);

    const navLinks = [
        { href: '/competitions', label: isRomanian ? 'Competitii' : 'Competitions', icon: Crosshair },
        { href: '/subscriptions', label: isRomanian ? 'Abonamente' : 'Subscriptions', icon: Crown },
        { href: '/winners', label: isRomanian ? 'Premianti' : 'Winners', icon: Trophy },
        { href: '/faq', label: 'FAQ', icon: HelpCircle },
    ];

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="fixed top-3 left-3 right-3 sm:left-4 sm:right-4 lg:left-6 lg:right-6 z-50" data-testid="navbar">
            <div className="max-w-7xl mx-auto rounded-2xl bg-[#060311]/70 backdrop-blur-2xl border border-white/[0.06] shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
                <div className="flex items-center justify-between h-14 sm:h-16 px-3 sm:px-5">
                    {/* Logo */}
                    <Link to="/" className="flex items-center shrink-0" data-testid="navbar-logo">
                        <AnimatedLogo size="default" />
                    </Link>

                    {/* Desktop Nav Links */}
                    <div className="hidden lg:flex items-center gap-0.5 mx-4">
                        {navLinks.map((link) => {
                            const Icon = link.icon;
                            return (
                                <Link
                                    key={link.href}
                                    to={link.href}
                                    className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-[13px] font-medium transition-all duration-200 ${
                                        isActive(link.href)
                                            ? 'bg-violet-500/15 text-violet-300 shadow-[inset_0_0_12px_rgba(139,92,246,0.1)]'
                                            : 'text-gray-400 hover:text-white hover:bg-white/[0.06]'
                                    }`}
                                    data-testid={`nav-link-${link.href.replace('/', '')}`}
                                >
                                    <Icon className="w-4 h-4" />
                                    <span>{link.label}</span>
                                </Link>
                            );
                        })}
                        <a
                            href="https://www.tiktok.com/@x67digital.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center px-3 py-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/[0.06] transition-all duration-200"
                            data-testid="tiktok-link"
                        >
                            <TikTokIcon className="w-4 h-4" />
                        </a>
                    </div>

                    {/* Right Side Actions */}
                    <div className="flex items-center gap-1 sm:gap-1.5">
                        {/* Language */}
                        <button
                            onClick={toggleLanguage}
                            className="flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-xl text-xs font-bold text-gray-400 hover:text-white hover:bg-white/[0.06] transition-all duration-200"
                            data-testid="language-toggle"
                            title={language === 'ro' ? 'Switch to English' : 'Schimba in Romana'}
                        >
                            {language.toUpperCase()}
                        </button>

                        {/* Wallet Balance */}
                        {isAuthenticated && walletBalance !== null && (
                            <Link to="/wallet" data-testid="wallet-nav-btn">
                                <button className="relative flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-emerald-400 hover:bg-emerald-500/10 transition-all duration-200">
                                    <Wallet className="w-[18px] h-[18px]" />
                                    <span className="text-xs font-bold">£{walletBalance.toFixed(2)}</span>
                                </button>
                            </Link>
                        )}

                        {/* User Notifications */}
                        {isAuthenticated && <UserNotificationBell />}

                        {/* Cart */}
                        <Link to="/cart" data-testid="cart-btn" aria-label="Shopping cart">
                            <button className="relative flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-xl text-gray-400 hover:text-white hover:bg-white/[0.06] transition-all duration-200" aria-label="Shopping cart">
                                <ShoppingCart className="w-[18px] h-[18px]" />
                                {totalItems > 0 && (
                                    <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-orange-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-[#0a0614]">
                                        {totalItems}
                                    </span>
                                )}
                            </button>
                        </Link>

                        {isAuthenticated ? (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <button className="flex items-center gap-1.5 pl-1.5 pr-2 py-1 rounded-xl hover:bg-white/[0.06] transition-all duration-200" data-testid="user-menu-btn">
                                        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-violet-500/30 to-orange-500/30 border border-white/10 flex items-center justify-center overflow-hidden">
                                            {user?.picture ? (
                                                <img src={user.picture} alt="" className="w-full h-full object-cover" />
                                            ) : (
                                                <span className="text-xs font-bold text-white">{user?.username?.charAt(0)?.toUpperCase() || 'U'}</span>
                                            )}
                                        </div>
                                        <ChevronDown className="w-3.5 h-3.5 text-gray-500 hidden sm:block" />
                                    </button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent className="w-56 bg-[#12101c] border-white/10 rounded-xl shadow-2xl mt-2" align="end">
                                    <div className="px-3 py-2.5 border-b border-white/[0.06]">
                                        <p className="text-sm font-semibold text-white truncate">{user?.username}</p>
                                        <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                                    </div>
                                    <div className="p-1">
                                        <DropdownMenuItem asChild>
                                            <Link to="/wallet" className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg cursor-pointer hover:bg-emerald-500/10" data-testid="menu-wallet">
                                                <Wallet className="w-4 h-4 text-emerald-400" />
                                                <span className="text-sm text-emerald-300">{isRomanian ? 'Portofel' : 'Wallet'}</span>
                                                {walletBalance !== null && <span className="ml-auto text-xs font-bold text-emerald-400">£{walletBalance.toFixed(2)}</span>}
                                            </Link>
                                        </DropdownMenuItem>
                                        <DropdownMenuItem asChild>
                                            <Link to="/dashboard" className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg cursor-pointer hover:bg-white/[0.06]" data-testid="menu-dashboard">
                                                <LayoutDashboard className="w-4 h-4 text-gray-500" />
                                                <span className="text-sm">{t('nav_dashboard')}</span>
                                            </Link>
                                        </DropdownMenuItem>
                                        <DropdownMenuItem asChild>
                                            <Link to="/dashboard/tickets" className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg cursor-pointer hover:bg-white/[0.06]" data-testid="menu-tickets">
                                                <Ticket className="w-4 h-4 text-gray-500" />
                                                <span className="text-sm">{t('nav_my_tickets')}</span>
                                            </Link>
                                        </DropdownMenuItem>
                                        {isAdmin && (
                                            <DropdownMenuItem asChild>
                                                <Link to="/admin" className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg cursor-pointer hover:bg-violet-500/10 text-violet-400" data-testid="menu-admin">
                                                    <Shield className="w-4 h-4" />
                                                    <span className="text-sm">Admin</span>
                                                </Link>
                                            </DropdownMenuItem>
                                        )}
                                    </div>
                                    <div className="border-t border-white/[0.06] p-1">
                                        <DropdownMenuItem onClick={logout} className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg cursor-pointer hover:bg-red-500/10 text-red-400" data-testid="menu-logout">
                                            <LogOut className="w-4 h-4" />
                                            <span className="text-sm">{t('nav_logout')}</span>
                                        </DropdownMenuItem>
                                    </div>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        ) : (
                            <div className="flex items-center gap-1.5">
                                <Link to="/login" aria-label="Login">
                                    <button className="hidden sm:block px-3.5 py-1.5 text-[13px] font-medium text-gray-400 hover:text-white transition-colors rounded-lg" data-testid="nav-login-btn">
                                        {isRomanian ? 'Conectare' : 'Login'}
                                    </button>
                                </Link>
                                <Link to="/login">
                                    <Button size="sm" className="bg-gradient-to-r from-violet-600 to-violet-500 hover:from-violet-500 hover:to-violet-400 text-white text-[13px] font-semibold rounded-xl h-8 sm:h-9 px-3.5 shadow-lg shadow-violet-500/20" data-testid="nav-signup-btn">
                                        {isRomanian ? 'Inscrie-te' : 'Sign Up'}
                                    </Button>
                                </Link>
                            </div>
                        )}

                        {/* Mobile Menu */}
                        <Sheet>
                            <SheetTrigger asChild className="lg:hidden">
                                <button className="flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-xl text-gray-400 hover:text-white hover:bg-white/[0.06] transition-all duration-200 ml-0.5" data-testid="mobile-menu-btn" aria-label="Open menu">
                                    <Menu className="w-5 h-5" />
                                </button>
                            </SheetTrigger>
                            <SheetContent side="right" className="w-[280px] sm:w-[320px] p-0 border-l border-white/[0.06] bg-[#060311]/95 backdrop-blur-2xl">
                                {/* Mobile Header */}
                                <div className="flex items-center justify-between p-4 border-b border-white/[0.06]">
                                    <AnimatedLogo size="default" />
                                    <SheetClose asChild>
                                        <button className="p-2 rounded-xl hover:bg-white/[0.06] transition-colors">
                                            <X className="w-5 h-5 text-gray-400" />
                                        </button>
                                    </SheetClose>
                                </div>

                                {/* User Info */}
                                {isAuthenticated && (
                                    <div className="p-4 border-b border-white/[0.06]">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/30 to-orange-500/30 border border-white/10 flex items-center justify-center overflow-hidden">
                                                {user?.picture ? (
                                                    <img src={user.picture} alt="" className="w-full h-full object-cover" />
                                                ) : (
                                                    <span className="text-sm font-bold text-white">{user?.username?.charAt(0)?.toUpperCase() || 'U'}</span>
                                                )}
                                            </div>
                                            <div className="min-w-0">
                                                <p className="font-semibold text-white text-sm truncate">{user?.username}</p>
                                                <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Nav Links */}
                                <div className="p-3 space-y-0.5">
                                    {navLinks.map((link) => {
                                        const Icon = link.icon;
                                        return (
                                            <SheetClose asChild key={link.href}>
                                                <Link
                                                    to={link.href}
                                                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                                                        isActive(link.href)
                                                            ? 'bg-violet-500/15 text-violet-300'
                                                            : 'text-gray-400 hover:bg-white/[0.06] hover:text-white'
                                                    }`}
                                                >
                                                    <Icon className="w-[18px] h-[18px]" />
                                                    <span>{link.label}</span>
                                                </Link>
                                            </SheetClose>
                                        );
                                    })}

                                    <a
                                        href="https://www.tiktok.com/@x67digital.com"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-gray-400 hover:bg-white/[0.06] hover:text-white transition-all duration-200"
                                    >
                                        <TikTokIcon className="w-[18px] h-[18px]" />
                                        <span>TikTok</span>
                                    </a>

                                    {isAuthenticated && (
                                        <>
                                            <div className="border-t border-white/[0.06] my-2"></div>
                                            <SheetClose asChild>
                                                <Link to="/wallet" className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-emerald-400 hover:bg-emerald-500/10 transition-all duration-200">
                                                    <Wallet className="w-[18px] h-[18px]" />
                                                    <span>{isRomanian ? 'Portofel' : 'Wallet'}</span>
                                                    {walletBalance !== null && <span className="ml-auto text-xs font-bold">£{walletBalance.toFixed(2)}</span>}
                                                </Link>
                                            </SheetClose>
                                            <SheetClose asChild>
                                                <Link to="/dashboard" className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-gray-400 hover:bg-white/[0.06] hover:text-white transition-all duration-200">
                                                    <LayoutDashboard className="w-[18px] h-[18px]" />
                                                    <span>{t('nav_dashboard')}</span>
                                                </Link>
                                            </SheetClose>
                                            {isAdmin && (
                                                <SheetClose asChild>
                                                    <Link to="/admin" className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-violet-400 hover:bg-violet-500/10 transition-all duration-200">
                                                        <Shield className="w-[18px] h-[18px]" />
                                                        <span>Admin Panel</span>
                                                    </Link>
                                                </SheetClose>
                                            )}
                                        </>
                                    )}
                                </div>

                                {/* Bottom */}
                                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/[0.06]">
                                    {isAuthenticated ? (
                                        <button
                                            onClick={logout}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-red-500/10 text-red-400 text-sm font-medium hover:bg-red-500/15 transition-all"
                                        >
                                            <LogOut className="w-4 h-4" />
                                            <span>{t('nav_logout')}</span>
                                        </button>
                                    ) : (
                                        <div className="space-y-2">
                                            <SheetClose asChild>
                                                <Link to="/login" className="block">
                                                    <Button className="w-full bg-gradient-to-r from-violet-600 to-violet-500 text-white font-semibold rounded-xl h-10">
                                                        {isRomanian ? 'Inscrie-te' : 'Sign Up'}
                                                    </Button>
                                                </Link>
                                            </SheetClose>
                                            <SheetClose asChild>
                                                <Link to="/login" className="block">
                                                    <button className="w-full px-4 py-2.5 rounded-xl border border-white/10 text-gray-400 text-sm font-medium hover:bg-white/[0.06] transition-all">
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
