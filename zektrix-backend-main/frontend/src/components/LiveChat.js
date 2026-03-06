import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { MessageCircle, X, Send, Bot, User, HelpCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const LiveChat = () => {
    const { user, token } = useAuth();
    const { isRomanian } = useLanguage();
    const [isOpen, setIsOpen] = useState(false);
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [faqList, setFaqList] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showFaq, setShowFaq] = useState(true);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        fetchFaqList();
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const fetchFaqList = async () => {
        try {
            const response = await axios.get(`${API}/api/chat/faq`);
            setFaqList(response.data);
        } catch (error) {
            console.error('Failed to fetch FAQ');
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleFaqClick = async (keyword) => {
        setShowFaq(false);
        const userMsg = faqList.find(f => f.keyword === keyword)?.question || keyword;
        
        setMessages(prev => [...prev, { type: 'user', text: userMsg }]);
        setLoading(true);

        try {
            const response = await axios.post(`${API}/api/chat/message`, 
                { message: keyword, is_faq: true },
                { headers: token ? { Authorization: `Bearer ${token}` } : {} }
            );
            
            setMessages(prev => [...prev, { 
                type: 'bot', 
                text: response.data.response 
            }]);
        } catch (error) {
            setMessages(prev => [...prev, { 
                type: 'bot', 
                text: isRomanian ? 'Eroare la încărcare. Încearcă din nou.' : 'Failed to load. Please try again.' 
            }]);
        } finally {
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

        try {
            const response = await axios.post(`${API}/api/chat/message`, 
                { message: userMessage },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            
            setMessages(prev => [...prev, { 
                type: 'bot', 
                text: response.data.response,
                isSupport: response.data.type === 'support'
            }]);
        } catch (error) {
            setMessages(prev => [...prev, { 
                type: 'bot', 
                text: isRomanian ? 'Eroare. Încearcă din nou.' : 'Error. Please try again.' 
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <>
            {/* Chat Button - More subtle */}
            <button
                onClick={() => setIsOpen(true)}
                className={`fixed bottom-4 right-4 z-50 w-12 h-12 rounded-full bg-gradient-to-r from-primary to-secondary shadow-lg flex items-center justify-center hover:scale-105 transition-transform ${isOpen ? 'hidden' : ''}`}
                data-testid="chat-btn"
            >
                <MessageCircle className="w-5 h-5 text-white" />
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-background"></span>
            </button>

            {/* Chat Window - Smaller on mobile */}
            {isOpen && (
                <div className="fixed bottom-4 right-4 z-50 w-[320px] sm:w-[360px] h-[450px] sm:h-[500px] bg-card border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-primary to-secondary p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="font-bold text-white">{isRomanian ? 'Asistent Zektrix' : 'Zektrix Assistant'}</h3>
                                <p className="text-xs text-white/70">{isRomanian ? 'Online acum' : 'Online now'}</p>
                            </div>
                        </div>
                        <button onClick={() => setIsOpen(false)} className="text-white/70 hover:text-white">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {/* Welcome Message */}
                        {messages.length === 0 && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-primary/20 flex-shrink-0 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-primary" />
                                </div>
                                <div className="bg-muted rounded-2xl rounded-tl-none p-3 max-w-[80%]">
                                    <p className="text-sm">
                                        {isRomanian 
                                            ? '👋 Salut! Sunt asistentul Zektrix. Cum te pot ajuta?' 
                                            : '👋 Hi! I\'m the Zektrix assistant. How can I help you?'}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* FAQ Buttons */}
                        {showFaq && messages.length === 0 && (
                            <div className="space-y-2">
                                <p className="text-xs text-muted-foreground px-2">{isRomanian ? 'Întrebări frecvente:' : 'Quick questions:'}</p>
                                <div className="flex flex-wrap gap-2">
                                    {faqList.slice(0, 6).map((faq, index) => (
                                        <button
                                            key={index}
                                            onClick={() => handleFaqClick(faq.keyword)}
                                            className="text-xs px-3 py-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-primary/50 transition-all"
                                        >
                                            {faq.question}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Message History */}
                        {messages.map((msg, index) => (
                            <div key={index} className={`flex gap-3 ${msg.type === 'user' ? 'flex-row-reverse' : ''}`}>
                                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                                    msg.type === 'user' ? 'bg-secondary/20' : 'bg-primary/20'
                                }`}>
                                    {msg.type === 'user' ? (
                                        <User className="w-4 h-4 text-secondary" />
                                    ) : (
                                        <Bot className="w-4 h-4 text-primary" />
                                    )}
                                </div>
                                <div className={`rounded-2xl p-3 max-w-[80%] ${
                                    msg.type === 'user' 
                                        ? 'bg-secondary/20 rounded-tr-none' 
                                        : 'bg-muted rounded-tl-none'
                                }`}>
                                    <p className="text-sm whitespace-pre-line">{msg.text}</p>
                                    {msg.isSupport && (
                                        <p className="text-xs text-green-500 mt-2">✓ {isRomanian ? 'Mesaj trimis echipei' : 'Sent to team'}</p>
                                    )}
                                </div>
                            </div>
                        ))}

                        {loading && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-primary/20 flex-shrink-0 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-primary" />
                                </div>
                                <div className="bg-muted rounded-2xl rounded-tl-none p-3">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Quick FAQ */}
                    {!showFaq && messages.length > 0 && (
                        <div className="px-4 py-2 border-t border-white/10">
                            <button 
                                onClick={() => { setShowFaq(true); setMessages([]); }}
                                className="text-xs text-primary hover:underline flex items-center gap-1"
                            >
                                <HelpCircle className="w-3 h-3" /> {isRomanian ? 'Vezi întrebări frecvente' : 'View FAQ'}
                            </button>
                        </div>
                    )}

                    {/* Input */}
                    <div className="p-4 border-t border-white/10">
                        <div className="flex gap-2">
                            <Input
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={isRomanian ? 'Scrie un mesaj...' : 'Type a message...'}
                                className="input-modern flex-1"
                                data-testid="chat-input"
                            />
                            <Button 
                                onClick={sendMessage} 
                                disabled={!message.trim() || loading}
                                className="btn-primary px-4"
                                data-testid="chat-send-btn"
                            >
                                <Send className="w-4 h-4" />
                            </Button>
                        </div>
                        {!user && (
                            <p className="text-xs text-muted-foreground mt-2 text-center">
                                {isRomanian ? 'Autentifică-te pentru a trimite mesaje la suport' : 'Login to send messages to support'}
                            </p>
                        )}
                    </div>
                </div>
            )}
        </>
    );
};

export default LiveChat;
