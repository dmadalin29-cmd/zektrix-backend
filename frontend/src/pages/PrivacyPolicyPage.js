import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Shield, Mail, Cookie, Eye, UserCheck, Server, Scale, Clock } from 'lucide-react';

const Section = ({ icon: Icon, title, children }) => (
    <div className="mb-10">
        <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" 
                style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(124, 58, 237, 0.2))' }}>
                <Icon className="w-5 h-5 text-violet-400" />
            </div>
            <h2 className="text-xl font-bold text-white">{title}</h2>
        </div>
        <div className="text-gray-400 leading-relaxed space-y-3 pl-[52px]">
            {children}
        </div>
    </div>
);

const PrivacyPolicyPage = () => {
    const { isRomanian } = useLanguage();

    return (
        <div className="min-h-screen" data-testid="privacy-policy-page">
            <Navbar />
            <main className="pt-24 pb-16">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6"
                            style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(124, 58, 237, 0.15))', border: '1px solid rgba(139, 92, 246, 0.4)' }}>
                            <Shield className="w-4 h-4 text-violet-400" />
                            <span className="text-sm font-bold text-violet-400">Privacy Policy</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black text-white mb-4">
                            {isRomanian ? 'Politica de Confidențialitate' : 'Privacy Policy'}
                        </h1>
                        <p className="text-gray-500">
                            {isRomanian ? 'Ultima actualizare: Martie 2026' : 'Last updated: March 2026'}
                        </p>
                    </div>

                    <div className="rounded-2xl p-6 md:p-10"
                        style={{ background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9), rgba(10, 6, 20, 0.95))', border: '1px solid rgba(139, 92, 246, 0.15)' }}>

                        <p className="text-gray-400 mb-8 leading-relaxed">
                            {isRomanian
                                ? <>Zektrix UK Ltd ("noi", "al nostru", "Zektrix") respectă confidențialitatea vizitatorilor și utilizatorilor platformei noastre <strong className="text-white">zektrix.uk</strong>. Această politică descrie cum colectăm, utilizăm și protejăm datele tale personale în conformitate cu <strong className="text-white">UK GDPR</strong> și <strong className="text-white">Data Protection Act 2018</strong>.</>
                                : <>Zektrix UK Ltd ("we", "our", "Zektrix") respects the privacy of visitors and users of our platform <strong className="text-white">zektrix.uk</strong>. This policy describes how we collect, use and protect your personal data in accordance with the <strong className="text-white">UK GDPR</strong> and <strong className="text-white">Data Protection Act 2018</strong>.</>
                            }
                        </p>

                        <Section icon={UserCheck} title={isRomanian ? '1. Cine suntem' : '1. Who we are'}>
                            <p><strong className="text-white">{isRomanian ? 'Operator de date:' : 'Data controller:'}</strong> Zektrix UK Ltd</p>
                            <p><strong className="text-white">{isRomanian ? 'Adresă:' : 'Address:'}</strong> c/o Bartle House, Oxford Court, Manchester, M2 3WQ, United Kingdom</p>
                            <p><strong className="text-white">{isRomanian ? 'Email contact:' : 'Contact email:'}</strong> support@zektrix.uk</p>
                        </Section>

                        <Section icon={Eye} title={isRomanian ? '2. Ce date colectăm' : '2. What data we collect'}>
                            <p>{isRomanian ? 'Colectăm următoarele categorii de date personale:' : 'We collect the following categories of personal data:'}</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">{isRomanian ? 'Date de identificare:' : 'Identification data:'}</strong> {isRomanian ? 'nume, prenume, adresă de email, număr de telefon' : 'name, surname, email address, phone number'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Date de autentificare:' : 'Authentication data:'}</strong> {isRomanian ? 'parolă (criptată), token-uri de sesiune' : 'password (encrypted), session tokens'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Date de tranzacție:' : 'Transaction data:'}</strong> {isRomanian ? 'istoricul achizițiilor, sumele plătite, biletele cumpărate' : 'purchase history, amounts paid, tickets purchased'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Date tehnice:' : 'Technical data:'}</strong> {isRomanian ? 'adresă IP, tip browser, sistem de operare, date despre dispozitiv' : 'IP address, browser type, operating system, device data'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Date de utilizare:' : 'Usage data:'}</strong> {isRomanian ? 'paginile vizitate, acțiunile pe platformă, preferințele' : 'pages visited, platform actions, preferences'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Date de comunicare:' : 'Communication data:'}</strong> {isRomanian ? 'mesaje trimise prin chat-ul de suport' : 'messages sent through support chat'}</li>
                            </ul>
                        </Section>

                        <Section icon={Scale} title={isRomanian ? '3. Baza legală a prelucrării' : '3. Legal basis for processing'}>
                            <p>{isRomanian ? 'Prelucrăm datele tale pe baza:' : 'We process your data based on:'}</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">{isRomanian ? 'Executarea contractului' : 'Contract performance'}</strong> — {isRomanian ? 'pentru a furniza serviciile platformei și procesarea plăților' : 'to provide platform services and payment processing'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Consimțământul tău' : 'Your consent'}</strong> — {isRomanian ? 'pentru comunicări de marketing și cookie-uri opționale' : 'for marketing communications and optional cookies'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Interes legitim' : 'Legitimate interest'}</strong> — {isRomanian ? 'pentru prevenirea fraudei, îmbunătățirea platformei și securitate' : 'for fraud prevention, platform improvement and security'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Obligații legale' : 'Legal obligations'}</strong> — {isRomanian ? 'conform legislației UK privind jocurile de noroc și fiscalitatea' : 'in accordance with UK gambling and tax legislation'}</li>
                            </ul>
                        </Section>

                        <Section icon={Server} title={isRomanian ? '4. Cum folosim datele' : '4. How we use data'}>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>{isRomanian ? 'Crearea și gestionarea contului tău' : 'Creating and managing your account'}</li>
                                <li>{isRomanian ? 'Procesarea plăților și achizițiilor de bilete prin Viva Payments' : 'Processing payments and ticket purchases via Viva Payments'}</li>
                                <li>{isRomanian ? 'Trimiterea confirmărilor de tranzacție și notificărilor despre competiții' : 'Sending transaction confirmations and competition notifications'}</li>
                                <li>{isRomanian ? 'Furnizarea suportului prin chat și email' : 'Providing support via chat and email'}</li>
                                <li>{isRomanian ? 'Îmbunătățirea performanței și funcționalității platformei' : 'Improving platform performance and functionality'}</li>
                                <li>{isRomanian ? 'Prevenirea fraudei și asigurarea securității' : 'Fraud prevention and security assurance'}</li>
                                <li>{isRomanian ? 'Conformarea cu cerințele legale și de reglementare' : 'Compliance with legal and regulatory requirements'}</li>
                            </ul>
                        </Section>

                        <Section icon={Shield} title={isRomanian ? '5. Partajarea datelor' : '5. Data sharing'}>
                            <p>{isRomanian ? 'Nu vindem datele tale personale. Partajăm date doar cu:' : 'We do not sell your personal data. We only share data with:'}</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">Viva Payments</strong> — {isRomanian ? 'procesarea plăților (PCI DSS compliant)' : 'payment processing (PCI DSS compliant)'}</li>
                                <li><strong className="text-white">Google Analytics</strong> — {isRomanian ? 'analiza traficului (date anonimizate)' : 'traffic analysis (anonymised data)'}</li>
                                <li><strong className="text-white">Resend</strong> — {isRomanian ? 'trimiterea email-urilor tranzacționale' : 'sending transactional emails'}</li>
                                <li><strong className="text-white">MongoDB Atlas</strong> — {isRomanian ? 'stocarea securizată a datelor' : 'secure data storage'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Autoritățile legale' : 'Legal authorities'}</strong> — {isRomanian ? 'când suntem obligați prin lege' : 'when required by law'}</li>
                            </ul>
                        </Section>

                        <Section icon={Cookie} title={isRomanian ? '6. Cookie-uri' : '6. Cookies'}>
                            <p>{isRomanian ? 'Folosim următoarele tipuri de cookie-uri:' : 'We use the following types of cookies:'}</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">{isRomanian ? 'Necesare:' : 'Necessary:'}</strong> {isRomanian ? 'autentificare, preferințe de limbă, coș de cumpărături' : 'authentication, language preferences, shopping cart'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Analitice:' : 'Analytics:'}</strong> {isRomanian ? 'Google Analytics pentru înțelegerea traficului (cu consimțământ)' : 'Google Analytics for understanding traffic (with consent)'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Funcționale:' : 'Functional:'}</strong> {isRomanian ? 'memorarea preferințelor și setărilor tale' : 'remembering your preferences and settings'}</li>
                            </ul>
                            <p>{isRomanian ? 'Poți gestiona preferințele de cookie-uri din banner-ul afișat pe site.' : 'You can manage your cookie preferences from the banner displayed on the site.'}</p>
                        </Section>

                        <Section icon={Clock} title={isRomanian ? '7. Retenția datelor' : '7. Data retention'}>
                            <p>{isRomanian ? 'Păstrăm datele tale personale atât timp cât contul tău este activ sau cât este necesar pentru scopurile descrise. Perioadele specifice:' : 'We retain your personal data for as long as your account is active or as necessary for the purposes described. Specific periods:'}</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">{isRomanian ? 'Date de cont:' : 'Account data:'}</strong> {isRomanian ? 'până la ștergerea contului + 30 zile' : 'until account deletion + 30 days'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Date de tranzacție:' : 'Transaction data:'}</strong> {isRomanian ? '7 ani (cerințe fiscale UK)' : '7 years (UK tax requirements)'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Loguri tehnice:' : 'Technical logs:'}</strong> {isRomanian ? '90 de zile' : '90 days'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Mesaje de suport:' : 'Support messages:'}</strong> {isRomanian ? '2 ani' : '2 years'}</li>
                            </ul>
                        </Section>

                        <Section icon={UserCheck} title={isRomanian ? '8. Drepturile tale' : '8. Your rights'}>
                            <p>{isRomanian ? 'Conform UK GDPR, ai următoarele drepturi:' : 'Under UK GDPR, you have the following rights:'}</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">{isRomanian ? 'Dreptul de acces' : 'Right of access'}</strong> — {isRomanian ? 'poți solicita o copie a datelor tale' : 'you can request a copy of your data'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Dreptul la rectificare' : 'Right to rectification'}</strong> — {isRomanian ? 'poți corecta datele inexacte' : 'you can correct inaccurate data'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Dreptul la ștergere' : 'Right to erasure'}</strong> — {isRomanian ? 'poți solicita ștergerea datelor ("dreptul de a fi uitat")' : 'you can request deletion of data ("right to be forgotten")'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Dreptul la restricționare' : 'Right to restriction'}</strong> — {isRomanian ? 'poți limita prelucrarea datelor' : 'you can limit data processing'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Dreptul la portabilitate' : 'Right to portability'}</strong> — {isRomanian ? 'poți primi datele într-un format standard' : 'you can receive data in a standard format'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Dreptul de opoziție' : 'Right to object'}</strong> — {isRomanian ? 'poți te opune prelucrării în anumite cazuri' : 'you can object to processing in certain cases'}</li>
                                <li><strong className="text-white">{isRomanian ? 'Retragerea consimțământului' : 'Withdrawal of consent'}</strong> — {isRomanian ? 'poți retrage consimțământul oricând' : 'you can withdraw consent at any time'}</li>
                            </ul>
                            <p className="mt-3">
                                {isRomanian
                                    ? <>Pentru exercitarea drepturilor, contactează-ne la <strong className="text-violet-400">support@zektrix.uk</strong>. Vom răspunde în maximum 30 de zile.</>
                                    : <>To exercise your rights, contact us at <strong className="text-violet-400">support@zektrix.uk</strong>. We will respond within 30 days.</>
                                }
                            </p>
                        </Section>

                        <Section icon={Shield} title={isRomanian ? '9. Securitatea datelor' : '9. Data security'}>
                            <p>{isRomanian ? 'Implementăm măsuri tehnice și organizatorice adecvate pentru protejarea datelor:' : 'We implement appropriate technical and organisational measures to protect data:'}</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>{isRomanian ? 'Criptare SSL/TLS pentru toate comunicațiile' : 'SSL/TLS encryption for all communications'}</li>
                                <li>{isRomanian ? 'Parole stocate cu hashing securizat (bcrypt)' : 'Passwords stored with secure hashing (bcrypt)'}</li>
                                <li>{isRomanian ? 'Acces restricționat la baza de date' : 'Restricted database access'}</li>
                                <li>{isRomanian ? 'Monitorizare continuă a securității' : 'Continuous security monitoring'}</li>
                                <li>{isRomanian ? 'Backup-uri regulate și criptate' : 'Regular encrypted backups'}</li>
                            </ul>
                        </Section>

                        <Section icon={Mail} title={isRomanian ? '10. Contact & Plângeri' : '10. Contact & Complaints'}>
                            <p>{isRomanian ? 'Pentru întrebări despre această politică sau prelucrarea datelor tale:' : 'For questions about this policy or processing of your data:'}</p>
                            <p><strong className="text-white">Email:</strong> <span className="text-violet-400">support@zektrix.uk</span></p>
                            <p><strong className="text-white">{isRomanian ? 'Adresă:' : 'Address:'}</strong> Zektrix UK Ltd, c/o Bartle House, Oxford Court, Manchester, M2 3WQ</p>
                            <p className="mt-3">
                                {isRomanian
                                    ? <>Dacă nu ești mulțumit de răspunsul nostru, ai dreptul să depui o plângere la <strong className="text-white">Information Commissioner's Office (ICO)</strong>:</>
                                    : <>If you are not satisfied with our response, you have the right to lodge a complaint with the <strong className="text-white">Information Commissioner's Office (ICO)</strong>:</>
                                }
                            </p>
                            <p><strong className="text-white">Website:</strong> <a href="https://ico.org.uk" target="_blank" rel="noopener noreferrer" className="text-violet-400 hover:underline">ico.org.uk</a></p>
                            <p><strong className="text-white">{isRomanian ? 'Telefon:' : 'Phone:'}</strong> 0303 123 1113</p>
                        </Section>

                        <div className="mt-8 pt-6 border-t border-white/10 text-center">
                            <p className="text-gray-500 text-sm">
                                {isRomanian
                                    ? 'Această politică poate fi actualizată periodic. Te rugăm să verifici această pagină regulat pentru modificări.'
                                    : 'This policy may be updated periodically. Please check this page regularly for changes.'}
                            </p>
                            <p className="text-gray-600 text-xs mt-2">&copy; 2026 Zektrix UK Ltd. {isRomanian ? 'Toate drepturile rezervate.' : 'All rights reserved.'}</p>
                        </div>
                    </div>
                </div>
            </main>
            <Footer />
        </div>
    );
};

export default PrivacyPolicyPage;
