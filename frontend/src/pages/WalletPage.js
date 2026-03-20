import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useSearchParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';
import {
    Wallet, ArrowUpCircle, ArrowDownCircle, Clock, CheckCircle2,
    XCircle, Gift, TrendingUp, CreditCard, Banknote, History,
    ChevronRight, Sparkles, AlertCircle, RefreshCw
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function WalletPage() {
    const { user, token } = useAuth();
    const { isRomanian } = useLanguage();
    const [searchParams] = useSearchParams();
    const headers = { Authorization: `Bearer ${token}` };

    const [balance, setBalance] = useState(0);
    const [transactions, setTransactions] = useState([]);
    const [withdrawals, setWithdrawals] = useState([]);
    const [bonusInfo, setBonusInfo] = useState({ active: false, bonus_percent: 0, bonus_max: 0 });
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    // Deposit form
    const [depositAmount, setDepositAmount] = useState('');
    const [depositing, setDepositing] = useState(false);

    // Withdrawal form
    const [withdrawAmount, setWithdrawAmount] = useState('');
    const [bankDetails, setBankDetails] = useState('');
    const [withdrawing, setWithdrawing] = useState(false);

    const fetchAll = useCallback(async () => {
        if (!token) return;
        setLoading(true);
        try {
            const [balRes, txnRes, wdRes, bonusRes] = await Promise.all([
                axios.get(`${API}/wallet/balance`, { headers }),
                axios.get(`${API}/wallet/transactions`, { headers }),
                axios.get(`${API}/wallet/withdrawals`, { headers }),
                axios.get(`${API}/wallet/bonus-info`)
            ]);
            setBalance(balRes.data.balance || 0);
            setTransactions(txnRes.data || []);
            setWithdrawals(wdRes.data || []);
            setBonusInfo(bonusRes.data || {});
        } catch (e) { console.error(e); }
        setLoading(false);
    }, [token]);

    useEffect(() => {
        fetchAll();
        const depositStatus = searchParams.get('deposit');
        if (depositStatus === 'success') toast.success(isRomanian ? 'Depunerea a fost realizata cu succes!' : 'Deposit successful!');
        if (depositStatus === 'failed') toast.error(isRomanian ? 'Depunerea a esuat.' : 'Deposit failed.');
        if (depositStatus === 'cancel') toast.info(isRomanian ? 'Depunerea a fost anulata.' : 'Deposit cancelled.');
    }, [fetchAll, searchParams, isRomanian]);

    const handleDeposit = async () => {
        const amount = parseFloat(depositAmount);
        if (!amount || amount < 5) return toast.error(isRomanian ? 'Minim £5' : 'Minimum £5');
        if (amount > 5000) return toast.error(isRomanian ? 'Maxim £5,000' : 'Maximum £5,000');
        setDepositing(true);
        try {
            const { data } = await axios.post(`${API}/wallet/deposit`, { amount }, { headers });
            if (data.checkout_url) {
                window.location.href = data.checkout_url;
            }
        } catch (e) {
            toast.error(e.response?.data?.detail || 'Error');
        }
        setDepositing(false);
    };

    const handleWithdraw = async () => {
        const amount = parseFloat(withdrawAmount);
        if (!amount || amount < 10) return toast.error(isRomanian ? 'Minim £10' : 'Minimum £10');
        if (amount > balance) return toast.error(isRomanian ? 'Fonduri insuficiente' : 'Insufficient balance');
        if (!bankDetails.trim()) return toast.error(isRomanian ? 'Introdu detaliile bancare' : 'Enter bank details');
        setWithdrawing(true);
        try {
            await axios.post(`${API}/wallet/withdraw`, {
                amount,
                method: 'bank_transfer',
                bank_details: bankDetails.trim()
            }, { headers });
            toast.success(isRomanian ? 'Cererea de retragere a fost trimisa!' : 'Withdrawal request submitted!');
            setWithdrawAmount('');
            setBankDetails('');
            fetchAll();
        } catch (e) {
            toast.error(e.response?.data?.detail || 'Error');
        }
        setWithdrawing(false);
    };

    const quickDeposits = [10, 25, 50, 100, 200, 500];

    const getStatusIcon = (status) => {
        if (status === 'completed' || status === 'approved') return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
        if (status === 'pending') return <Clock className="w-4 h-4 text-amber-400" />;
        if (status === 'failed' || status === 'rejected' || status === 'refunded') return <XCircle className="w-4 h-4 text-red-400" />;
        return <Clock className="w-4 h-4 text-gray-400" />;
    };

    const getTypeIcon = (type) => {
        if (type === 'deposit') return <ArrowDownCircle className="w-5 h-5 text-emerald-400" />;
        if (type === 'withdrawal_request') return <ArrowUpCircle className="w-5 h-5 text-orange-400" />;
        if (type === 'ticket_purchase' || type === 'ticket_purchase_viva') return <CreditCard className="w-5 h-5 text-violet-400" />;
        if (type === 'admin_adjustment') return <Sparkles className="w-5 h-5 text-amber-400" />;
        if (type === 'referral_bonus') return <Gift className="w-5 h-5 text-pink-400" />;
        return <History className="w-5 h-5 text-gray-400" />;
    };

    const getTypeLabel = (type) => {
        const labels = {
            deposit: isRomanian ? 'Depunere' : 'Deposit',
            withdrawal_request: isRomanian ? 'Retragere' : 'Withdrawal',
            ticket_purchase: isRomanian ? 'Cumparare bilete' : 'Ticket Purchase',
            ticket_purchase_viva: isRomanian ? 'Cumparare bilete' : 'Ticket Purchase',
            admin_adjustment: isRomanian ? 'Ajustare admin' : 'Admin Adjustment',
            referral_bonus: isRomanian ? 'Bonus referral' : 'Referral Bonus',
        };
        return labels[type] || type;
    };

    const formatDate = (d) => {
        try { return new Date(d).toLocaleDateString('ro-RO', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
        catch { return d; }
    };

    const tabs = [
        { id: 'overview', label: isRomanian ? 'Prezentare' : 'Overview', icon: Wallet },
        { id: 'deposit', label: isRomanian ? 'Depune' : 'Deposit', icon: ArrowDownCircle },
        { id: 'withdraw', label: isRomanian ? 'Retrage' : 'Withdraw', icon: ArrowUpCircle },
        { id: 'history', label: isRomanian ? 'Istoric' : 'History', icon: History },
    ];

    if (loading) {
        return (
            <div className="min-h-screen bg-[#060311]">
                <Navbar />
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="w-8 h-8 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#060311]" data-testid="wallet-page">
            <Navbar />
            <div className="max-w-5xl mx-auto px-4 pt-24 pb-20">
                {/* Header with Balance */}
                <div className="relative overflow-hidden rounded-3xl p-6 sm:p-8 mb-8" style={{
                    background: 'linear-gradient(135deg, rgba(139,92,246,0.15) 0%, rgba(249,115,22,0.1) 50%, rgba(139,92,246,0.08) 100%)',
                    border: '1px solid rgba(139,92,246,0.2)'
                }} data-testid="wallet-balance-card">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-violet-500/5 rounded-full blur-3xl" />
                    <div className="relative">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500/30 to-orange-500/30 flex items-center justify-center">
                                <Wallet className="w-6 h-6 text-violet-300" />
                            </div>
                            <div>
                                <p className="text-sm text-gray-400">{isRomanian ? 'Soldul tau' : 'Your Balance'}</p>
                                <h1 className="text-3xl sm:text-4xl font-bold text-white" data-testid="wallet-balance-amount">
                                    £{balance.toFixed(2)}
                                </h1>
                            </div>
                        </div>
                        {bonusInfo.active && (
                            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20" data-testid="bonus-badge">
                                <Gift className="w-4 h-4 text-emerald-400" />
                                <span className="text-sm text-emerald-300 font-medium">
                                    {bonusInfo.bonus_percent}% bonus {isRomanian ? 'la depunere' : 'on deposits'}
                                    {bonusInfo.bonus_max > 0 && ` (max £${bonusInfo.bonus_max})`}
                                </span>
                            </div>
                        )}
                        <div className="flex gap-3 mt-5">
                            <Button onClick={() => setActiveTab('deposit')} className="bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl gap-2" data-testid="quick-deposit-btn">
                                <ArrowDownCircle className="w-4 h-4" /> {isRomanian ? 'Depune' : 'Deposit'}
                            </Button>
                            <Button onClick={() => setActiveTab('withdraw')} variant="outline" className="border-white/10 text-white hover:bg-white/5 rounded-xl gap-2" data-testid="quick-withdraw-btn">
                                <ArrowUpCircle className="w-4 h-4" /> {isRomanian ? 'Retrage' : 'Withdraw'}
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-1 p-1 rounded-2xl bg-white/[0.03] border border-white/[0.06] mb-6 overflow-x-auto">
                    {tabs.map(t => {
                        const Icon = t.icon;
                        return (
                            <button key={t.id} onClick={() => setActiveTab(t.id)}
                                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                                    activeTab === t.id
                                        ? 'bg-violet-500/15 text-violet-300 shadow-[inset_0_0_12px_rgba(139,92,246,0.1)]'
                                        : 'text-gray-500 hover:text-white hover:bg-white/[0.04]'
                                }`}
                                data-testid={`wallet-tab-${t.id}`}
                            >
                                <Icon className="w-4 h-4" /> {t.label}
                            </button>
                        );
                    })}
                </div>

                {/* Overview Tab */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {/* Quick Stats */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {[
                                { label: isRomanian ? 'Sold' : 'Balance', value: `£${balance.toFixed(2)}`, icon: Wallet, color: 'violet' },
                                { label: isRomanian ? 'Depuneri' : 'Deposits', value: transactions.filter(t => t.transaction_type === 'deposit' && t.status === 'completed').length, icon: ArrowDownCircle, color: 'emerald' },
                                { label: isRomanian ? 'Cumparari' : 'Purchases', value: transactions.filter(t => t.transaction_type.includes('ticket')).length, icon: CreditCard, color: 'orange' },
                                { label: isRomanian ? 'Retrageri' : 'Withdrawals', value: withdrawals.length, icon: ArrowUpCircle, color: 'pink' },
                            ].map((stat, i) => {
                                const Icon = stat.icon;
                                return (
                                    <div key={i} className="rounded-2xl p-4" style={{
                                        background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                                        border: '1px solid rgba(139,92,246,0.1)'
                                    }}>
                                        <Icon className={`w-5 h-5 text-${stat.color}-400 mb-2`} />
                                        <p className="text-xs text-gray-500">{stat.label}</p>
                                        <p className="text-lg font-bold text-white">{stat.value}</p>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Recent Transactions */}
                        <div className="rounded-2xl overflow-hidden" style={{
                            background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                            border: '1px solid rgba(139,92,246,0.1)'
                        }}>
                            <div className="flex items-center justify-between p-5 border-b border-white/[0.06]">
                                <h3 className="text-white font-semibold">{isRomanian ? 'Tranzactii Recente' : 'Recent Transactions'}</h3>
                                <button onClick={() => setActiveTab('history')} className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1">
                                    {isRomanian ? 'Vezi tot' : 'View all'} <ChevronRight className="w-3 h-3" />
                                </button>
                            </div>
                            <div className="divide-y divide-white/[0.04]">
                                {transactions.slice(0, 5).map((txn, i) => (
                                    <div key={i} className="flex items-center gap-3 p-4 hover:bg-white/[0.02] transition-colors">
                                        <div className="w-10 h-10 rounded-xl bg-white/[0.04] flex items-center justify-center shrink-0">
                                            {getTypeIcon(txn.transaction_type)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-white font-medium truncate">{getTypeLabel(txn.transaction_type)}</p>
                                            <p className="text-xs text-gray-500">{formatDate(txn.created_at)}</p>
                                        </div>
                                        <div className="text-right shrink-0">
                                            <p className={`text-sm font-semibold ${txn.amount >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {txn.amount >= 0 ? '+' : ''}£{Math.abs(txn.amount).toFixed(2)}
                                            </p>
                                            <div className="flex items-center gap-1 justify-end">
                                                {getStatusIcon(txn.status)}
                                                <span className="text-[10px] text-gray-500 capitalize">{txn.status}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                {transactions.length === 0 && (
                                    <div className="p-8 text-center text-gray-500 text-sm">
                                        {isRomanian ? 'Nicio tranzactie inca' : 'No transactions yet'}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Deposit Tab */}
                {activeTab === 'deposit' && (
                    <div className="space-y-6">
                        <div className="rounded-2xl p-6" style={{
                            background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                            border: '1px solid rgba(139,92,246,0.1)'
                        }}>
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-12 h-12 rounded-2xl bg-emerald-500/15 flex items-center justify-center">
                                    <Banknote className="w-6 h-6 text-emerald-400" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-white">{isRomanian ? 'Depune Fonduri' : 'Deposit Funds'}</h2>
                                    <p className="text-sm text-gray-500">{isRomanian ? 'Adauga bani in portofel' : 'Add money to your wallet'}</p>
                                </div>
                            </div>

                            {bonusInfo.active && (
                                <div className="mb-6 p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/15">
                                    <div className="flex items-center gap-2 mb-1">
                                        <Sparkles className="w-4 h-4 text-emerald-400" />
                                        <span className="text-sm font-semibold text-emerald-300">
                                            {bonusInfo.bonus_percent}% Bonus {isRomanian ? 'Activ!' : 'Active!'}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-400">
                                        {isRomanian
                                            ? `Primesti ${bonusInfo.bonus_percent}% bonus la fiecare depunere${bonusInfo.bonus_max > 0 ? `, maxim £${bonusInfo.bonus_max}` : ''}`
                                            : `Get ${bonusInfo.bonus_percent}% bonus on every deposit${bonusInfo.bonus_max > 0 ? `, max £${bonusInfo.bonus_max}` : ''}`
                                        }
                                    </p>
                                </div>
                            )}

                            {/* Quick amounts */}
                            <p className="text-xs text-gray-500 mb-3">{isRomanian ? 'Suma rapida' : 'Quick amount'}</p>
                            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-4">
                                {quickDeposits.map(amt => (
                                    <button key={amt} onClick={() => setDepositAmount(String(amt))}
                                        className={`py-2.5 rounded-xl text-sm font-semibold transition-all ${
                                            depositAmount === String(amt)
                                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                                : 'bg-white/[0.04] text-gray-400 border border-white/[0.06] hover:bg-white/[0.08] hover:text-white'
                                        }`}
                                        data-testid={`deposit-quick-${amt}`}
                                    >
                                        £{amt}
                                    </button>
                                ))}
                            </div>

                            {/* Custom amount */}
                            <div className="flex gap-3">
                                <div className="flex-1 relative">
                                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-semibold">£</span>
                                    <Input
                                        type="number"
                                        value={depositAmount}
                                        onChange={e => setDepositAmount(e.target.value)}
                                        placeholder={isRomanian ? 'Suma personalizata' : 'Custom amount'}
                                        className="pl-8 bg-white/[0.04] border-white/[0.08] text-white h-12 rounded-xl text-lg"
                                        min="5" max="5000" step="1"
                                        data-testid="deposit-amount-input"
                                    />
                                </div>
                                <Button onClick={handleDeposit} disabled={depositing}
                                    className="bg-emerald-600 hover:bg-emerald-500 text-white h-12 px-8 rounded-xl text-base font-semibold gap-2"
                                    data-testid="deposit-submit-btn"
                                >
                                    {depositing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
                                    {isRomanian ? 'Depune' : 'Deposit'}
                                </Button>
                            </div>

                            {depositAmount && parseFloat(depositAmount) >= 5 && bonusInfo.active && (
                                <div className="mt-4 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-gray-400">{isRomanian ? 'Depunere' : 'Deposit'}</span>
                                        <span className="text-white">£{parseFloat(depositAmount).toFixed(2)}</span>
                                    </div>
                                    <div className="flex justify-between text-sm mt-1">
                                        <span className="text-emerald-400">+ Bonus {bonusInfo.bonus_percent}%</span>
                                        <span className="text-emerald-400">
                                            +£{Math.min(parseFloat(depositAmount) * bonusInfo.bonus_percent / 100, bonusInfo.bonus_max || Infinity).toFixed(2)}
                                        </span>
                                    </div>
                                    <div className="border-t border-white/[0.06] mt-2 pt-2 flex justify-between text-sm">
                                        <span className="text-white font-semibold">{isRomanian ? 'Total in portofel' : 'Total in wallet'}</span>
                                        <span className="text-white font-semibold">
                                            £{(parseFloat(depositAmount) + Math.min(parseFloat(depositAmount) * bonusInfo.bonus_percent / 100, bonusInfo.bonus_max || Infinity)).toFixed(2)}
                                        </span>
                                    </div>
                                </div>
                            )}

                            <p className="text-xs text-gray-600 mt-3 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" /> {isRomanian ? 'Plata securizata prin Viva Payments. Minim £5, maxim £5,000.' : 'Secure payment via Viva Payments. Min £5, max £5,000.'}
                            </p>
                        </div>
                    </div>
                )}

                {/* Withdraw Tab */}
                {activeTab === 'withdraw' && (
                    <div className="space-y-6">
                        <div className="rounded-2xl p-6" style={{
                            background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                            border: '1px solid rgba(139,92,246,0.1)'
                        }}>
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-12 h-12 rounded-2xl bg-orange-500/15 flex items-center justify-center">
                                    <Banknote className="w-6 h-6 text-orange-400" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-white">{isRomanian ? 'Retrage Fonduri' : 'Withdraw Funds'}</h2>
                                    <p className="text-sm text-gray-500">
                                        {isRomanian ? `Sold disponibil: £${balance.toFixed(2)}` : `Available: £${balance.toFixed(2)}`}
                                    </p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-sm text-gray-400 mb-1.5 block">{isRomanian ? 'Suma' : 'Amount'}</label>
                                    <div className="relative">
                                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-semibold">£</span>
                                        <Input
                                            type="number" value={withdrawAmount}
                                            onChange={e => setWithdrawAmount(e.target.value)}
                                            className="pl-8 bg-white/[0.04] border-white/[0.08] text-white h-12 rounded-xl"
                                            placeholder={isRomanian ? 'Minim £10' : 'Minimum £10'}
                                            min="10" max={balance} step="1"
                                            data-testid="withdraw-amount-input"
                                        />
                                    </div>
                                    {balance > 0 && (
                                        <button onClick={() => setWithdrawAmount(String(balance))}
                                            className="text-xs text-violet-400 hover:text-violet-300 mt-1"
                                        >
                                            {isRomanian ? 'Retrage tot' : 'Withdraw all'} (£{balance.toFixed(2)})
                                        </button>
                                    )}
                                </div>

                                <div>
                                    <label className="text-sm text-gray-400 mb-1.5 block">{isRomanian ? 'Detalii bancare (IBAN/Sort Code)' : 'Bank Details (IBAN/Sort Code)'}</label>
                                    <textarea
                                        value={bankDetails} onChange={e => setBankDetails(e.target.value)}
                                        className="w-full h-24 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white p-3 text-sm resize-none focus:border-violet-500 focus:outline-none"
                                        placeholder={isRomanian ? 'IBAN, Sort Code + Account Number, sau alte detalii...' : 'IBAN, Sort Code + Account Number, or other details...'}
                                        data-testid="withdraw-bank-input"
                                    />
                                </div>

                                <Button onClick={handleWithdraw} disabled={withdrawing || balance < 10}
                                    className="w-full bg-orange-600 hover:bg-orange-500 text-white h-12 rounded-xl text-base font-semibold gap-2"
                                    data-testid="withdraw-submit-btn"
                                >
                                    {withdrawing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ArrowUpCircle className="w-4 h-4" />}
                                    {isRomanian ? 'Trimite Cererea' : 'Submit Request'}
                                </Button>

                                <p className="text-xs text-gray-600 flex items-center gap-1">
                                    <AlertCircle className="w-3 h-3" /> {isRomanian ? 'Retragerile sunt procesate manual dupa aprobare. Timp estimat: 1-3 zile lucratoare.' : 'Withdrawals are processed after admin approval. Estimated time: 1-3 business days.'}
                                </p>
                            </div>
                        </div>

                        {/* Withdrawal History */}
                        {withdrawals.length > 0 && (
                            <div className="rounded-2xl overflow-hidden" style={{
                                background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                                border: '1px solid rgba(139,92,246,0.1)'
                            }}>
                                <div className="p-5 border-b border-white/[0.06]">
                                    <h3 className="text-white font-semibold">{isRomanian ? 'Cererile Tale de Retragere' : 'Your Withdrawal Requests'}</h3>
                                </div>
                                <div className="divide-y divide-white/[0.04]">
                                    {withdrawals.map((wd, i) => (
                                        <div key={i} className="flex items-center gap-3 p-4">
                                            <div className="w-10 h-10 rounded-xl bg-white/[0.04] flex items-center justify-center shrink-0">
                                                {getStatusIcon(wd.status)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-white font-medium">£{wd.amount?.toFixed(2)}</p>
                                                <p className="text-xs text-gray-500">{formatDate(wd.created_at)}</p>
                                            </div>
                                            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                                                wd.status === 'pending' ? 'bg-amber-500/10 text-amber-400' :
                                                wd.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400' :
                                                'bg-red-500/10 text-red-400'
                                            }`}>
                                                {wd.status === 'pending' ? (isRomanian ? 'In asteptare' : 'Pending') :
                                                 wd.status === 'approved' ? (isRomanian ? 'Aprobat' : 'Approved') :
                                                 (isRomanian ? 'Respins' : 'Rejected')}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* History Tab */}
                {activeTab === 'history' && (
                    <div className="rounded-2xl overflow-hidden" style={{
                        background: 'linear-gradient(135deg, rgba(15,10,30,0.9), rgba(10,6,20,0.95))',
                        border: '1px solid rgba(139,92,246,0.1)'
                    }}>
                        <div className="p-5 border-b border-white/[0.06] flex items-center justify-between">
                            <h3 className="text-white font-semibold">{isRomanian ? 'Toate Tranzactiile' : 'All Transactions'}</h3>
                            <button onClick={fetchAll} className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1">
                                <RefreshCw className="w-3 h-3" /> {isRomanian ? 'Reincarca' : 'Refresh'}
                            </button>
                        </div>
                        <div className="divide-y divide-white/[0.04]">
                            {transactions.map((txn, i) => (
                                <div key={i} className="flex items-center gap-3 p-4 hover:bg-white/[0.02] transition-colors">
                                    <div className="w-10 h-10 rounded-xl bg-white/[0.04] flex items-center justify-center shrink-0">
                                        {getTypeIcon(txn.transaction_type)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-white font-medium truncate">{getTypeLabel(txn.transaction_type)}</p>
                                        <p className="text-xs text-gray-500 truncate">{txn.description || formatDate(txn.created_at)}</p>
                                    </div>
                                    <div className="text-right shrink-0">
                                        <p className={`text-sm font-semibold ${txn.amount >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {txn.amount >= 0 ? '+' : ''}£{Math.abs(txn.amount).toFixed(2)}
                                        </p>
                                        <div className="flex items-center gap-1 justify-end">
                                            {getStatusIcon(txn.status)}
                                            <span className="text-[10px] text-gray-500 capitalize">{txn.status}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {transactions.length === 0 && (
                                <div className="p-12 text-center text-gray-500 text-sm">
                                    {isRomanian ? 'Nicio tranzactie inca. Depune fonduri pentru a incepe!' : 'No transactions yet. Deposit funds to get started!'}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
            <Footer />
        </div>
    );
}
