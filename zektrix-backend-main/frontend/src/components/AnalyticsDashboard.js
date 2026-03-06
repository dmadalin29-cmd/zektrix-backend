import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Loader2, TrendingUp, Users, Ticket, Trophy, PoundSterling, Gift, BarChart3 } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AnalyticsDashboard = () => {
    const { token } = useAuth();
    const { isRomanian } = useLanguage();
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchAnalytics();
    }, []);

    const fetchAnalytics = async () => {
        try {
            const response = await axios.get(`${API}/admin/analytics`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setAnalytics(response.data);
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    const stats = [
        { 
            label: isRomanian ? 'Venit Total' : 'Total Revenue', 
            value: `RON ${analytics?.total_revenue?.toFixed(2) || 0}`, 
            icon: PoundSterling, 
            color: 'text-green-500',
            bg: 'bg-green-500/20'
        },
        { 
            label: isRomanian ? 'Total Utilizatori' : 'Total Users', 
            value: analytics?.total_users || 0, 
            icon: Users, 
            color: 'text-blue-500',
            bg: 'bg-blue-500/20'
        },
        { 
            label: isRomanian ? 'Total Locuri' : 'Total Spots', 
            value: analytics?.total_tickets || 0, 
            icon: Ticket, 
            color: 'text-purple-500',
            bg: 'bg-purple-500/20'
        },
        { 
            label: isRomanian ? 'Competiții Active' : 'Active Competitions', 
            value: analytics?.active_competitions || 0, 
            icon: Trophy, 
            color: 'text-yellow-500',
            bg: 'bg-yellow-500/20'
        },
        { 
            label: isRomanian ? 'Competiții Completate' : 'Completed', 
            value: analytics?.completed_competitions || 0, 
            icon: TrendingUp, 
            color: 'text-secondary',
            bg: 'bg-secondary/20'
        },
        { 
            label: isRomanian ? 'Total Premianți' : 'Total Winners', 
            value: analytics?.total_winners || 0, 
            icon: Trophy, 
            color: 'text-primary',
            bg: 'bg-primary/20'
        },
        { 
            label: isRomanian ? 'Referrals Completate' : 'Completed Referrals', 
            value: analytics?.total_referrals || 0, 
            icon: Gift, 
            color: 'text-pink-500',
            bg: 'bg-pink-500/20'
        },
        { 
            label: isRomanian ? 'Locuri/Utilizator' : 'Avg Spots/User', 
            value: analytics?.avg_tickets_per_user?.toFixed(1) || 0, 
            icon: BarChart3, 
            color: 'text-cyan-500',
            bg: 'bg-cyan-500/20'
        }
    ];

    return (
        <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {stats.map((stat, index) => (
                    <Card key={index} className="glass border-white/10">
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center`}>
                                    <stat.icon className={`w-5 h-5 ${stat.color}`} />
                                </div>
                                <div>
                                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                                    <p className="text-xl font-bold">{stat.value}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Top Competitions */}
            <Card className="glass border-white/10">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Trophy className="w-5 h-5 text-primary" />
                        {isRomanian ? 'Top Competiții' : 'Top Competitions'}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {analytics?.top_competitions?.slice(0, 5).map((comp, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-xl">
                                <div className="flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-sm font-bold">
                                        {index + 1}
                                    </span>
                                    <div>
                                        <p className="font-medium">{comp.title}</p>
                                        <p className="text-sm text-muted-foreground">
                                            {comp.sold}/{comp.max} {isRomanian ? 'locuri' : 'spots'}
                                        </p>
                                    </div>
                                </div>
                                <Badge className="badge-secondary">RON {comp.revenue?.toFixed(2)}</Badge>
                            </div>
                        ))}
                        {(!analytics?.top_competitions || analytics.top_competitions.length === 0) && (
                            <p className="text-center text-muted-foreground py-4">
                                {isRomanian ? 'Nicio competiție încă' : 'No competitions yet'}
                            </p>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Revenue by Day Chart (Simple) */}
            {analytics?.revenue_by_day?.length > 0 && (
                <Card className="glass border-white/10">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-secondary" />
                            {isRomanian ? 'Venit pe Zi (Ultimele 30 Zile)' : 'Revenue by Day (Last 30 Days)'}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-48 flex items-end gap-1">
                            {analytics.revenue_by_day.slice(-30).map((day, index) => {
                                const maxRevenue = Math.max(...analytics.revenue_by_day.map(d => d.revenue));
                                const height = maxRevenue > 0 ? (day.revenue / maxRevenue) * 100 : 0;
                                return (
                                    <div 
                                        key={index} 
                                        className="flex-1 bg-gradient-to-t from-primary to-secondary rounded-t-sm transition-all hover:opacity-80"
                                        style={{ height: `${Math.max(height, 2)}%` }}
                                        title={`${day.date}: RON ${day.revenue.toFixed(2)}`}
                                    />
                                );
                            })}
                        </div>
                        <div className="flex justify-between text-xs text-muted-foreground mt-2">
                            <span>{analytics.revenue_by_day[0]?.date}</span>
                            <span>{analytics.revenue_by_day[analytics.revenue_by_day.length - 1]?.date}</span>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* User Growth */}
            {analytics?.user_growth?.length > 0 && (
                <Card className="glass border-white/10">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Users className="w-5 h-5 text-blue-500" />
                            {isRomanian ? 'Creștere Utilizatori' : 'User Growth'}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {analytics.user_growth.slice(-7).map((day, index) => (
                                <div key={index} className="flex items-center gap-4">
                                    <span className="text-sm text-muted-foreground w-24">{day.date}</span>
                                    <div className="flex-1 bg-muted/30 rounded-full h-4">
                                        <div 
                                            className="bg-gradient-to-r from-blue-500 to-cyan-500 h-full rounded-full"
                                            style={{ width: `${(day.users / Math.max(...analytics.user_growth.map(d => d.users))) * 100}%` }}
                                        />
                                    </div>
                                    <span className="text-sm font-medium w-8">{day.users}</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default AnalyticsDashboard;
