import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../components/ui/accordion';
import { Badge } from '../components/ui/badge';
import { HelpCircle, Mail, MessageCircle, Phone, Sparkles } from 'lucide-react';

const FAQPage = () => {
    const { t, isRomanian } = useLanguage();

    const faqs = [
        { q: t('faq_1_q'), a: t('faq_1_a') },
        { q: t('faq_2_q'), a: t('faq_2_a') },
        { q: t('faq_3_q'), a: t('faq_3_a') },
        { q: t('faq_4_q'), a: t('faq_4_a') },
        { q: t('faq_5_q'), a: t('faq_5_a') },
        { q: t('faq_6_q'), a: t('faq_6_a') },
        { q: t('faq_7_q'), a: t('faq_7_a') },
        { q: t('faq_8_q'), a: t('faq_8_a') },
        { q: t('faq_9_q'), a: t('faq_9_a') },
        { q: t('faq_10_q'), a: t('faq_10_a') }
    ];

    return (
        <div className="min-h-screen bg-[#030014]" data-testid="faq-page">
            <Navbar />
            
            <main className="pt-24 pb-16">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="text-center mb-12">
                        <Badge className="mb-6 px-4 py-2 text-sm font-bold"
                            style={{
                                background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(8, 145, 178, 0.15) 100%)',
                                border: '1px solid rgba(6, 182, 212, 0.4)',
                                color: '#06b6d4'
                            }}>
                            <HelpCircle className="w-4 h-4 mr-2" /> {t('help_center')}
                        </Badge>
                        <h1 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight mb-4">
                            <span className="text-white">{isRomanian ? 'Întrebări ' : 'Frequently Asked '}</span>
                            <span className="bg-gradient-to-r from-cyan-400 to-violet-500 bg-clip-text text-transparent">
                                {isRomanian ? 'Frecvente' : 'Questions'}
                            </span>
                        </h1>
                        <p className="text-gray-400 max-w-xl mx-auto text-lg">
                            {t('faq_subtitle')}
                        </p>
                    </div>

                    {/* FAQ Accordion */}
                    <div className="rounded-2xl p-6 md:p-8"
                        style={{
                            background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                            border: '1px solid rgba(139, 92, 246, 0.15)'
                        }}>
                        <Accordion type="single" collapsible className="w-full space-y-2">
                            {faqs.map((faq, index) => (
                                <AccordionItem 
                                    key={index} 
                                    value={`item-${index}`} 
                                    className="border-0 rounded-xl overflow-hidden"
                                    style={{ background: 'rgba(255,255,255,0.03)' }}
                                    data-testid={`faq-item-${index}`}
                                >
                                    <AccordionTrigger className="text-left hover:no-underline px-5 py-4 text-white font-medium hover:text-violet-400 transition-colors [&[data-state=open]]:text-violet-400">
                                        {faq.q}
                                    </AccordionTrigger>
                                    <AccordionContent className="px-5 pb-4 text-gray-400 leading-relaxed">
                                        {faq.a}
                                    </AccordionContent>
                                </AccordionItem>
                            ))}
                        </Accordion>
                    </div>

                    {/* Contact Section */}
                    <div className="mt-8 rounded-2xl p-8 text-center"
                        style={{
                            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(249, 115, 22, 0.05) 100%)',
                            border: '1px solid rgba(139, 92, 246, 0.2)'
                        }}>
                        <div className="w-16 h-16 rounded-2xl mx-auto mb-6 flex items-center justify-center"
                            style={{ background: 'linear-gradient(135deg, #8b5cf6, #f97316)', boxShadow: '0 0 30px rgba(139, 92, 246, 0.4)' }}>
                            <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">{t('still_questions')}</h3>
                        <p className="text-gray-400 mb-6 max-w-md mx-auto">
                            {t('support_here')}
                        </p>
                        
                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <a href="mailto:support@zektrix.uk" 
                                className="inline-flex items-center justify-center gap-3 px-6 py-4 rounded-xl transition-all duration-300 hover:scale-[1.02]"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(124, 58, 237, 0.15) 100%)',
                                    border: '1px solid rgba(139, 92, 246, 0.3)'
                                }}>
                                <Mail className="w-5 h-5 text-violet-400" />
                                <span className="font-medium text-white">support@zektrix.uk</span>
                            </a>
                            <a href="https://wa.me/40730268067" target="_blank" rel="noopener noreferrer"
                                className="inline-flex items-center justify-center gap-3 px-6 py-4 rounded-xl transition-all duration-300 hover:scale-[1.02]"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(22, 163, 74, 0.15) 100%)',
                                    border: '1px solid rgba(34, 197, 94, 0.3)'
                                }}>
                                <MessageCircle className="w-5 h-5 text-green-400" />
                                <span className="font-medium text-white">WhatsApp</span>
                            </a>
                        </div>
                    </div>

                    {/* Quick Help Cards */}
                    <div className="grid md:grid-cols-3 gap-4 mt-8">
                        <div className="rounded-2xl p-5"
                            style={{
                                background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                border: '1px solid rgba(139, 92, 246, 0.15)'
                            }}>
                            <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center mb-3">
                                <HelpCircle className="w-5 h-5 text-violet-400" />
                            </div>
                            <h4 className="font-bold text-white mb-1">{isRomanian ? 'Ghid Rapid' : 'Quick Guide'}</h4>
                            <p className="text-sm text-gray-500">{isRomanian ? 'Află cum funcționează platforma' : 'Learn how the platform works'}</p>
                        </div>
                        <div className="rounded-2xl p-5"
                            style={{
                                background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                border: '1px solid rgba(139, 92, 246, 0.15)'
                            }}>
                            <div className="w-10 h-10 rounded-xl bg-orange-500/20 flex items-center justify-center mb-3">
                                <Phone className="w-5 h-5 text-orange-400" />
                            </div>
                            <h4 className="font-bold text-white mb-1">{isRomanian ? 'Suport Live' : 'Live Support'}</h4>
                            <p className="text-sm text-gray-500">{isRomanian ? 'Răspundem în max 24h' : 'We respond within 24h'}</p>
                        </div>
                        <div className="rounded-2xl p-5"
                            style={{
                                background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9) 0%, rgba(10, 6, 20, 0.95) 100%)',
                                border: '1px solid rgba(139, 92, 246, 0.15)'
                            }}>
                            <div className="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center mb-3">
                                <MessageCircle className="w-5 h-5 text-cyan-400" />
                            </div>
                            <h4 className="font-bold text-white mb-1">{isRomanian ? 'Comunitate' : 'Community'}</h4>
                            <p className="text-sm text-gray-500">{isRomanian ? 'Intră în grupul nostru' : 'Join our community'}</p>
                        </div>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default FAQPage;
