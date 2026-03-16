import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { MessageCircle, X, Send, Bot, User, Headphones, Loader2, Wifi, WifiOff, ArrowLeft, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const WS_URL = process.env.REACT_APP_BACKEND_URL?.replace('https://', 'wss://').replace('http://', 'ws://');

const LiveChat = () => {
    const { user, token } = useAuth();
    const { isRomanian } = useLanguage();
    const [isOpen, setIsOpen] = useState(false);
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [hasUnread, setHasUnread] = useState(false);
    const [mode, setMode] = useState('ai'); // 'ai' or 'live'
    const [connected, setConnected] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const messagesEndRef = useRef(null);
    const wsRef = useRef(null);
    const reconnectTimer = useRef(null);

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    // Connect WebSocket only in live mode
    const historyLoadedRef = useRef(false);
    useEffect(() => {
        if (isOpen && user && token && mode === 'live') {
            connectWebSocket();
            if (!historyLoadedRef.current) {
                loadHistory();
                historyLoadedRef.current = true;
            }
        }
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
            if (reconnectTimer.current) {
                clearTimeout(reconnectTimer.current);
            }
        };
    }, [isOpen, user, token, mode]);

    const connectWebSocket = useCallback(() => {
        if (!token || !WS_URL) return;
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

        try {
            const ws = new WebSocket(`${WS_URL}/ws/chat/user?token=${token}`);
            ws.onopen = () => setConnected(true);
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'admin_reply') {
                    const replyId = data.message_id + '_reply_' + data.timestamp;
                    setMessages(prev => {
                        // Prevent duplicate admin replies
                        if (prev.some(m => m.id === replyId)) return prev;
                        return [...prev, {
                            type: 'admin',
                            text: data.reply,
                            repliedBy: data.replied_by,
                            timestamp: data.timestamp,
                            id: replyId
                        }];
                    });
                    if (!isOpen) setHasUnread(true);
                } else if (data.type === 'faq_response') {
                    setMessages(prev => [...prev, { type: 'bot', text: data.message, timestamp: data.timestamp }]);
                    setLoading(false);
                } else if (data.type === 'message_sent') {
                    setLoading(false);
                }
            };
            ws.onclose = () => {
                setConnected(false);
                wsRef.current = null;
                if (isOpen && user && mode === 'live') {
                    reconnectTimer.current = setTimeout(connectWebSocket, 3000);
                }
            };
            ws.onerror = () => ws.close();
            wsRef.current = ws;
        } catch (e) {
            console.error('WS connect error:', e);
        }
    }, [token, isOpen, user, mode]);

    const loadHistory = async () => {
        try {
            const authToken = token || localStorage.getItem('zektrix_token');
            if (!authToken) return;
            const res = await axios.get(`${API}/chat/history`, {
                headers: { Authorization: `Bearer ${authToken}` }
            });
            if (res.data && res.data.length > 0) {
                const historyMsgs = [];
                res.data.forEach(m => {
                    historyMsgs.push({ type: 'user', text: m.message, timestamp: m.created_at, id: m.message_id });
                    if (m.admin_reply) {
                        historyMsgs.push({ type: 'admin', text: m.admin_reply, repliedBy: m.replied_by || 'Admin', timestamp: m.replied_at || m.created_at, id: m.message_id + '_reply' });
                    }
                });
                // Replace messages instead of appending to avoid duplicates
                setMessages(historyMsgs);
            }
        } catch (e) {
            console.error('Failed to load chat history');
        }
    };

    const sendAIMessage = async () => {
        if (!message.trim()) return;
        if (!user) {
            toast.error(isRomanian ? 'Autentifică-te pentru a trimite mesaje' : 'Login to send messages');
            return;
        }

        const userMessage = message.trim();
        setMessage('');
        setMessages(prev => [...prev, { type: 'user', text: userMessage }]);
        setLoading(true);

        try {
            const res = await axios.post(`${API}/chat/ai`,
                { message: userMessage, session_id: sessionId },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setSessionId(res.data.session_id);
            setMessages(prev => [...prev, {
                type: 'ai',
                text: res.data.response,
                needs_escalation: res.data.needs_escalation
            }]);
        } catch {
            setMessages(prev => [...prev, {
                type: 'ai',
                text: 'Îmi pare rău, am o problemă tehnică. Poți vorbi cu un operator live.',
                needs_escalation: true
            }]);
        }
        setLoading(false);
    };

    const sendLiveMessage = async () => {
        if (!message.trim() || !user) return;
        const userMessage = message.trim();
        setMessage('');
        setMessages(prev => [...prev, { type: 'user', text: userMessage }]);
        setLoading(true);

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'message', message: userMessage }));
        } else {
            setLoading(false);
            toast.error('Nu sunt conectat. Încerc reconectarea...');
            connectWebSocket();
        }
    };

    const escalateToLive = async () => {
        const lastUserMsg = [...messages].reverse().find(m => m.type === 'user');
        const msgText = lastUserMsg?.text || 'Utilizatorul dorește asistență live';

        setMessages(prev => [...prev, {
            type: 'system',
            text: 'Te conectăm cu un operator live. Vei primi o notificare când răspunde.'
        }]);

        try {
            await axios.post(`${API}/chat/escalate`,
                { message: msgText },
                { headers: { Authorization: `Bearer ${token}` } }
            );
        } catch (e) {
            console.error('Escalation error:', e);
        }

        setMode('live');
    };

    const sendMessage = mode === 'ai' ? sendAIMessage : sendLiveMessage;

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const openChat = () => {
        setIsOpen(true);
        setHasUnread(false);
    };

    const quickQuestions = [
        'Cum funcționează competițiile?',
        'Cum plătesc?',
        'Ce este Autodraw?',
        'Cum văd biletele mele?',
    ];

    return (
        <>
            <button
                onClick={openChat}
                className={`fixed bottom-4 right-4 z-50 w-12 h-12 rounded-full shadow-lg flex items-center justify-center hover:scale-105 transition-transform ${isOpen ? 'hidden' : ''}`}
                style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}
                data-testid="chat-btn"
            >
                <MessageCircle className="w-5 h-5 text-white" />
                {hasUnread && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full border-2 border-[#030014] flex items-center justify-center">
                        <span className="text-[8px] text-white font-bold">!</span>
                    </span>
                )}
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-[#030014]" style={{ display: hasUnread ? 'none' : 'block' }} />
            </button>

            {isOpen && (
                <div className="fixed bottom-4 right-4 z-50 w-[340px] sm:w-[380px] h-[500px] sm:h-[540px] rounded-2xl shadow-2xl flex flex-col overflow-hidden"
                    style={{ background: 'linear-gradient(135deg, #0f0a1e 0%, #0a0614 100%)', border: '1px solid rgba(139, 92, 246, 0.2)' }}
                    data-testid="chat-window"
                >
                    {/* Header */}
                    <div className="p-3 flex items-center justify-between" style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}>
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
                                {mode === 'ai' ? <Sparkles className="w-4 h-4 text-white" /> : <Headphones className="w-4 h-4 text-white" />}
                            </div>
                            <div>
                                <h3 className="font-bold text-white text-sm">
                                    {mode === 'ai' ? 'Asistent AI Zektrix' : 'Chat Live'}
                                </h3>
                                <span className="text-[10px] text-white/70">
                                    {mode === 'ai' ? 'Răspuns instant' : (connected ? '🟢 Conectat' : '🔴 Se reconectează...')}
                                </span>
                            </div>
                        </div>
                        <div className="flex items-center gap-1">
                            {mode === 'live' && (
                                <button onClick={() => setMode('ai')} className="text-white/70 hover:text-white p-1" title="Înapoi la AI">
                                    <ArrowLeft className="w-4 h-4" />
                                </button>
                            )}
                            <button onClick={() => setIsOpen(false)} className="text-white/70 hover:text-white p-1" data-testid="chat-close-btn">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-3 space-y-3">
                        {messages.length === 0 && mode === 'ai' && (
                            <>
                                <div className="flex gap-2">
                                    <div className="w-7 h-7 rounded-full bg-violet-500/20 flex-shrink-0 flex items-center justify-center">
                                        <Sparkles className="w-3.5 h-3.5 text-violet-400" />
                                    </div>
                                    <div className="rounded-2xl rounded-tl-none p-3 max-w-[85%]" style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.15)' }}>
                                        <p className="text-sm text-gray-300">
                                            Salut! Sunt asistentul AI Zektrix. Pot răspunde la orice întrebare despre competiții, plăți sau contul tău. Cu ce te pot ajuta?
                                        </p>
                                    </div>
                                </div>
                                <div className="space-y-1.5 mt-2 pl-9">
                                    {quickQuestions.map((q, i) => (
                                        <button key={i} onClick={() => { setMessage(q); }}
                                            className="block w-full text-left text-xs px-3 py-2 rounded-lg transition-all text-gray-400 hover:text-violet-300 hover:bg-violet-500/10"
                                            style={{ border: '1px solid rgba(139, 92, 246, 0.12)' }}
                                            data-testid={`quick-q-${i}`}
                                        >
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}

                        {messages.map((msg, i) => (
                            <div key={i}>
                                {msg.type === 'system' ? (
                                    <div className="text-center py-2">
                                        <span className="text-[11px] text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/20">
                                            {msg.text}
                                        </span>
                                    </div>
                                ) : (
                                    <div className={`flex gap-2 ${msg.type === 'user' ? 'flex-row-reverse' : ''}`}>
                                        <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center ${
                                            msg.type === 'user' ? 'bg-orange-500/20' :
                                            msg.type === 'admin' ? 'bg-emerald-500/20' : 'bg-violet-500/20'
                                        }`}>
                                            {msg.type === 'user' ? <User className="w-3.5 h-3.5 text-orange-400" /> :
                                             msg.type === 'admin' ? <Headphones className="w-3.5 h-3.5 text-emerald-400" /> :
                                             <Sparkles className="w-3.5 h-3.5 text-violet-400" />}
                                        </div>
                                        <div className={`rounded-2xl p-3 max-w-[80%] ${msg.type === 'user' ? 'rounded-tr-none' : 'rounded-tl-none'}`}
                                            style={{
                                                background: msg.type === 'user' ? 'rgba(249, 115, 22, 0.1)' :
                                                           msg.type === 'admin' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(139, 92, 246, 0.1)',
                                                border: msg.type === 'user' ? '1px solid rgba(249, 115, 22, 0.15)' :
                                                        msg.type === 'admin' ? '1px solid rgba(16, 185, 129, 0.15)' : '1px solid rgba(139, 92, 246, 0.15)'
                                            }}>
                                            {msg.type === 'admin' && (
                                                <p className="text-[10px] text-emerald-400 mb-1 font-bold">{msg.repliedBy || 'Operator'}</p>
                                            )}
                                            <p className="text-sm text-gray-300 whitespace-pre-line">{msg.text}</p>
                                        </div>
                                    </div>
                                )}

                                {/* Escalation button after AI suggests it */}
                                {msg.type === 'ai' && msg.needs_escalation && i === messages.length - 1 && mode === 'ai' && (
                                    <div className="pl-9 mt-2">
                                        <button onClick={escalateToLive}
                                            className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all"
                                            data-testid="escalate-btn"
                                        >
                                            <Headphones className="w-3.5 h-3.5" /> Vorbește cu un operator live
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}

                        {loading && (
                            <div className="flex gap-2">
                                <div className="w-7 h-7 rounded-full bg-violet-500/20 flex-shrink-0 flex items-center justify-center">
                                    <Sparkles className="w-3.5 h-3.5 text-violet-400" />
                                </div>
                                <div className="rounded-2xl rounded-tl-none p-3" style={{ background: 'rgba(139, 92, 246, 0.1)' }}>
                                    <div className="flex gap-1">
                                        <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Live chat escalation button (always visible in AI mode) */}
                    {mode === 'ai' && messages.length > 0 && (
                        <div className="px-3 py-1.5 border-t border-white/5">
                            <button onClick={escalateToLive}
                                className="text-[11px] text-gray-500 hover:text-emerald-400 flex items-center gap-1 transition-colors"
                                data-testid="escalate-footer-btn"
                            >
                                <Headphones className="w-3 h-3" /> Vorbește cu un operator live
                            </button>
                        </div>
                    )}

                    {/* Input */}
                    <div className="p-3 border-t border-white/10">
                        <div className="flex gap-2">
                            <Input
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={user ? (mode === 'ai' ? 'Întreabă-mă orice...' : 'Scrie mesajul...') : 'Loghează-te pentru chat'}
                                className="flex-1 bg-white/5 border-white/10 text-sm"
                                disabled={!user}
                                data-testid="chat-input"
                            />
                            <Button
                                onClick={sendMessage}
                                disabled={!message.trim() || loading || !user}
                                className="px-3"
                                style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}
                                data-testid="chat-send-btn"
                            >
                                <Send className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default LiveChat;
