import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { MessageCircle, X, Send, Bot, User, HelpCircle, Loader2, Wifi, WifiOff } from 'lucide-react';
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
    const [faqList, setFaqList] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showFaq, setShowFaq] = useState(true);
    const [connected, setConnected] = useState(false);
    const [hasUnread, setHasUnread] = useState(false);
    const messagesEndRef = useRef(null);
    const wsRef = useRef(null);
    const reconnectTimer = useRef(null);

    useEffect(() => {
        fetchFaqList();
    }, []);

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    // Connect WebSocket when chat opens and user is logged in
    useEffect(() => {
        if (isOpen && user && token) {
            connectWebSocket();
            loadHistory();
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
    }, [isOpen, user, token]);

    const connectWebSocket = useCallback(() => {
        if (!token || !WS_URL) return;
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

        try {
            const ws = new WebSocket(`${WS_URL}/ws/chat/user?token=${token}`);

            ws.onopen = () => {
                setConnected(true);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'admin_reply') {
                    setMessages(prev => [...prev, {
                        type: 'admin',
                        text: data.reply,
                        repliedBy: data.replied_by,
                        messageId: data.message_id,
                        timestamp: data.timestamp
                    }]);
                    if (!isOpen) setHasUnread(true);
                } else if (data.type === 'faq_response') {
                    setMessages(prev => [...prev, {
                        type: 'bot',
                        text: data.message,
                        timestamp: data.timestamp
                    }]);
                    setLoading(false);
                } else if (data.type === 'message_sent') {
                    setLoading(false);
                }
            };

            ws.onclose = () => {
                setConnected(false);
                wsRef.current = null;
                if (isOpen && user) {
                    reconnectTimer.current = setTimeout(connectWebSocket, 3000);
                }
            };

            ws.onerror = () => {
                ws.close();
            };

            wsRef.current = ws;
        } catch (e) {
            console.error('WS connect error:', e);
        }
    }, [token, isOpen, user]);

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
                    historyMsgs.push({
                        type: 'user',
                        text: m.message,
                        messageId: m.message_id,
                        timestamp: m.created_at
                    });
                    if (m.admin_reply) {
                        historyMsgs.push({
                            type: 'admin',
                            text: m.admin_reply,
                            repliedBy: m.replied_by || 'Admin',
                            messageId: m.message_id,
                            timestamp: m.replied_at || m.created_at
                        });
                    }
                });
                setMessages(historyMsgs);
                if (historyMsgs.length > 0) setShowFaq(false);
            }
        } catch (e) {
            console.error('Failed to load chat history');
        }
    };

    const fetchFaqList = async () => {
        try {
            const response = await axios.get(`${API}/chat/faq`);
            setFaqList(response.data);
        } catch (error) {
            console.error('Failed to fetch FAQ');
        }
    };

    const handleFaqClick = async (keyword) => {
        setShowFaq(false);
        const userMsg = faqList.find(f => f.keyword === keyword)?.question || keyword;
        setMessages(prev => [...prev, { type: 'user', text: userMsg }]);
        setLoading(true);

        // Try WebSocket first
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'message', message: keyword }));
        } else {
            try {
                const response = await axios.post(`${API}/chat/message`,
                    { message: keyword, is_faq: true },
                    { headers: token ? { Authorization: `Bearer ${token}` } : {} }
                );
                setMessages(prev => [...prev, { type: 'bot', text: response.data.response }]);
            } catch {
                setMessages(prev => [...prev, { type: 'bot', text: 'Eroare. Încearcă din nou.' }]);
            }
            setLoading(false);
        }
    };

    const sendMessage = async () => {
        if (!message.trim()) return;
        if (!user) {
            toast.error(isRomanian ? 'Autentifică-te pentru a trimite mesaje' : 'Login to send messages');
            return;
        }

        setShowFaq(false);
        const userMessage = message.trim();
        setMessage('');
        setMessages(prev => [...prev, { type: 'user', text: userMessage }]);
        setLoading(true);

        // Try WebSocket first
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'message', message: userMessage }));
        } else {
            // Fallback to HTTP
            try {
                const response = await axios.post(`${API}/chat/message`,
                    { message: userMessage },
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                setMessages(prev => [...prev, {
                    type: 'bot',
                    text: response.data.response,
                    isSupport: response.data.type === 'support'
                }]);
            } catch {
                setMessages(prev => [...prev, { type: 'bot', text: 'Eroare. Încearcă din nou.' }]);
            }
            setLoading(false);
        }
    };

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
                <div className="fixed bottom-4 right-4 z-50 w-[340px] sm:w-[380px] h-[480px] sm:h-[520px] rounded-2xl shadow-2xl flex flex-col overflow-hidden"
                    style={{ background: 'linear-gradient(135deg, #0f0a1e 0%, #0a0614 100%)', border: '1px solid rgba(139, 92, 246, 0.2)' }}
                    data-testid="chat-window"
                >
                    {/* Header */}
                    <div className="p-4 flex items-center justify-between" style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' }}>
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="font-bold text-white text-sm">Suport Zektrix</h3>
                                <div className="flex items-center gap-1">
                                    {connected ? (
                                        <><Wifi className="w-3 h-3 text-green-300" /><span className="text-xs text-green-200">Live</span></>
                                    ) : (
                                        <><WifiOff className="w-3 h-3 text-white/50" /><span className="text-xs text-white/60">Offline</span></>
                                    )}
                                </div>
                            </div>
                        </div>
                        <button onClick={() => setIsOpen(false)} className="text-white/70 hover:text-white" data-testid="chat-close-btn">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                        {messages.length === 0 && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 flex-shrink-0 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-violet-400" />
                                </div>
                                <div className="rounded-2xl rounded-tl-none p-3 max-w-[80%]" style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.15)' }}>
                                    <p className="text-sm text-gray-300">
                                        Salut! Sunt asistentul Zektrix. Cum te pot ajuta?
                                    </p>
                                </div>
                            </div>
                        )}

                        {showFaq && messages.length === 0 && (
                            <div className="space-y-2 mt-2">
                                <p className="text-xs text-gray-500 px-2">Întrebări frecvente:</p>
                                <div className="flex flex-wrap gap-2">
                                    {faqList.slice(0, 6).map((faq, i) => (
                                        <button key={i} onClick={() => handleFaqClick(faq.keyword)}
                                            className="text-xs px-3 py-2 rounded-full transition-all text-gray-400 hover:text-violet-300"
                                            style={{ background: 'rgba(139, 92, 246, 0.08)', border: '1px solid rgba(139, 92, 246, 0.15)' }}
                                            data-testid={`faq-btn-${i}`}
                                        >
                                            {faq.question}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {messages.map((msg, i) => (
                            <div key={i} className={`flex gap-2 ${msg.type === 'user' ? 'flex-row-reverse' : ''}`}>
                                <div className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center ${
                                    msg.type === 'user' ? 'bg-orange-500/20' : msg.type === 'admin' ? 'bg-emerald-500/20' : 'bg-violet-500/20'
                                }`}>
                                    {msg.type === 'user' ? <User className="w-3.5 h-3.5 text-orange-400" /> :
                                     msg.type === 'admin' ? <User className="w-3.5 h-3.5 text-emerald-400" /> :
                                     <Bot className="w-3.5 h-3.5 text-violet-400" />}
                                </div>
                                <div className={`rounded-2xl p-3 max-w-[80%] ${
                                    msg.type === 'user' ? 'rounded-tr-none' : 'rounded-tl-none'
                                }`} style={{
                                    background: msg.type === 'user' ? 'rgba(249, 115, 22, 0.1)' :
                                               msg.type === 'admin' ? 'rgba(16, 185, 129, 0.1)' :
                                               'rgba(139, 92, 246, 0.1)',
                                    border: msg.type === 'user' ? '1px solid rgba(249, 115, 22, 0.15)' :
                                            msg.type === 'admin' ? '1px solid rgba(16, 185, 129, 0.15)' :
                                            '1px solid rgba(139, 92, 246, 0.15)'
                                }}>
                                    {msg.type === 'admin' && (
                                        <p className="text-[10px] text-emerald-400 mb-1 font-bold">{msg.repliedBy || 'Admin'}</p>
                                    )}
                                    <p className="text-sm text-gray-300 whitespace-pre-line">{msg.text}</p>
                                    {msg.isSupport && (
                                        <p className="text-xs text-emerald-400 mt-1">Mesaj trimis echipei</p>
                                    )}
                                </div>
                            </div>
                        ))}

                        {loading && (
                            <div className="flex gap-2">
                                <div className="w-7 h-7 rounded-full bg-violet-500/20 flex-shrink-0 flex items-center justify-center">
                                    <Bot className="w-3.5 h-3.5 text-violet-400" />
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

                    {!showFaq && messages.length > 0 && (
                        <div className="px-4 py-2 border-t border-white/5">
                            <button onClick={() => { setShowFaq(true); setMessages([]); }}
                                className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1">
                                <HelpCircle className="w-3 h-3" /> Întrebări frecvente
                            </button>
                        </div>
                    )}

                    <div className="p-3 border-t border-white/10">
                        <div className="flex gap-2">
                            <Input
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={user ? 'Scrie un mesaj...' : 'Loghează-te pentru a trimite...'}
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
