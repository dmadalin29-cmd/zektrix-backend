import React from 'react';
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
    return (
        <div className="min-h-screen bg-[#030014]" data-testid="privacy-policy-page">
            <Navbar />
            <main className="pt-24 pb-16">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6"
                            style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(124, 58, 237, 0.15))', border: '1px solid rgba(139, 92, 246, 0.4)' }}>
                            <Shield className="w-4 h-4 text-violet-400" />
                            <span className="text-sm font-bold text-violet-400">Privacy Policy</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black text-white mb-4">Politica de Confidențialitate</h1>
                        <p className="text-gray-500">Ultima actualizare: Martie 2026</p>
                    </div>

                    <div className="rounded-2xl p-6 md:p-10"
                        style={{ background: 'linear-gradient(135deg, rgba(15, 10, 30, 0.9), rgba(10, 6, 20, 0.95))', border: '1px solid rgba(139, 92, 246, 0.15)' }}>

                        <p className="text-gray-400 mb-8 leading-relaxed">
                            Zektrix UK Ltd ("noi", "al nostru", "Zektrix") respectă confidențialitatea vizitatorilor și utilizatorilor platformei noastre <strong className="text-white">zektrix.uk</strong>. Această politică descrie cum colectăm, utilizăm și protejăm datele tale personale în conformitate cu <strong className="text-white">UK GDPR</strong> și <strong className="text-white">Data Protection Act 2018</strong>.
                        </p>

                        <Section icon={UserCheck} title="1. Cine suntem">
                            <p><strong className="text-white">Operator de date:</strong> Zektrix UK Ltd</p>
                            <p><strong className="text-white">Adresă:</strong> c/o Bartle House, Oxford Court, Manchester, M2 3WQ, United Kingdom</p>
                            <p><strong className="text-white">Email contact:</strong> support@zektrix.uk</p>
                        </Section>

                        <Section icon={Eye} title="2. Ce date colectăm">
                            <p>Colectăm următoarele categorii de date personale:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">Date de identificare:</strong> nume, prenume, adresă de email, număr de telefon</li>
                                <li><strong className="text-white">Date de autentificare:</strong> parolă (criptată), token-uri de sesiune</li>
                                <li><strong className="text-white">Date de tranzacție:</strong> istoricul achizițiilor, sumele plătite, biletele cumpărate</li>
                                <li><strong className="text-white">Date tehnice:</strong> adresă IP, tip browser, sistem de operare, date despre dispozitiv</li>
                                <li><strong className="text-white">Date de utilizare:</strong> paginile vizitate, acțiunile pe platformă, preferințele</li>
                                <li><strong className="text-white">Date de comunicare:</strong> mesaje trimise prin chat-ul de suport</li>
                            </ul>
                        </Section>

                        <Section icon={Scale} title="3. Baza legală a prelucrării">
                            <p>Prelucrăm datele tale pe baza:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">Executarea contractului</strong> — pentru a furniza serviciile platformei și procesarea plăților</li>
                                <li><strong className="text-white">Consimțământul tău</strong> — pentru comunicări de marketing și cookie-uri opționale</li>
                                <li><strong className="text-white">Interes legitim</strong> — pentru prevenirea fraudei, îmbunătățirea platformei și securitate</li>
                                <li><strong className="text-white">Obligații legale</strong> — conform legislației UK privind jocurile de noroc și fiscalitatea</li>
                            </ul>
                        </Section>

                        <Section icon={Server} title="4. Cum folosim datele">
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>Crearea și gestionarea contului tău</li>
                                <li>Procesarea plăților și achizițiilor de bilete prin Viva Payments</li>
                                <li>Trimiterea confirmărilor de tranzacție și notificărilor despre competiții</li>
                                <li>Furnizarea suportului prin chat și email</li>
                                <li>Îmbunătățirea performanței și funcționalității platformei</li>
                                <li>Prevenirea fraudei și asigurarea securității</li>
                                <li>Conformarea cu cerințele legale și de reglementare</li>
                            </ul>
                        </Section>

                        <Section icon={Shield} title="5. Partajarea datelor">
                            <p>Nu vindem datele tale personale. Partajăm date doar cu:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">Viva Payments</strong> — procesarea plăților (PCI DSS compliant)</li>
                                <li><strong className="text-white">Google Analytics</strong> — analiza traficului (date anonimizate)</li>
                                <li><strong className="text-white">Resend</strong> — trimiterea email-urilor tranzacționale</li>
                                <li><strong className="text-white">MongoDB Atlas</strong> — stocarea securizată a datelor</li>
                                <li><strong className="text-white">Autoritățile legale</strong> — când suntem obligați prin lege</li>
                            </ul>
                        </Section>

                        <Section icon={Cookie} title="6. Cookie-uri">
                            <p>Folosim următoarele tipuri de cookie-uri:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">Necesare:</strong> autentificare, preferințe de limbă, coș de cumpărături</li>
                                <li><strong className="text-white">Analitice:</strong> Google Analytics pentru înțelegerea traficului (cu consimțământ)</li>
                                <li><strong className="text-white">Funcționale:</strong> memorarea preferințelor și setărilor tale</li>
                            </ul>
                            <p>Poți gestiona preferințele de cookie-uri din banner-ul afișat pe site.</p>
                        </Section>

                        <Section icon={Clock} title="7. Retenția datelor">
                            <p>Păstrăm datele tale personale atât timp cât contul tău este activ sau cât este necesar pentru scopurile descrise. Perioadele specifice:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">Date de cont:</strong> până la ștergerea contului + 30 zile</li>
                                <li><strong className="text-white">Date de tranzacție:</strong> 7 ani (cerințe fiscale UK)</li>
                                <li><strong className="text-white">Loguri tehnice:</strong> 90 de zile</li>
                                <li><strong className="text-white">Mesaje de suport:</strong> 2 ani</li>
                            </ul>
                        </Section>

                        <Section icon={UserCheck} title="8. Drepturile tale">
                            <p>Conform UK GDPR, ai următoarele drepturi:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li><strong className="text-white">Dreptul de acces</strong> — poți solicita o copie a datelor tale</li>
                                <li><strong className="text-white">Dreptul la rectificare</strong> — poți corecta datele inexacte</li>
                                <li><strong className="text-white">Dreptul la ștergere</strong> — poți solicita ștergerea datelor ("dreptul de a fi uitat")</li>
                                <li><strong className="text-white">Dreptul la restricționare</strong> — poți limita prelucrarea datelor</li>
                                <li><strong className="text-white">Dreptul la portabilitate</strong> — poți primi datele într-un format standard</li>
                                <li><strong className="text-white">Dreptul de opoziție</strong> — poți te opune prelucrării în anumite cazuri</li>
                                <li><strong className="text-white">Retragerea consimțământului</strong> — poți retrage consimțământul oricând</li>
                            </ul>
                            <p className="mt-3">Pentru exercitarea drepturilor, contactează-ne la <strong className="text-violet-400">support@zektrix.uk</strong>. Vom răspunde în maximum 30 de zile.</p>
                        </Section>

                        <Section icon={Shield} title="9. Securitatea datelor">
                            <p>Implementăm măsuri tehnice și organizatorice adecvate pentru protejarea datelor:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>Criptare SSL/TLS pentru toate comunicațiile</li>
                                <li>Parole stocate cu hashing securizat (bcrypt)</li>
                                <li>Acces restricționat la baza de date</li>
                                <li>Monitorizare continuă a securității</li>
                                <li>Backup-uri regulate și criptate</li>
                            </ul>
                        </Section>

                        <Section icon={Mail} title="10. Contact & Plângeri">
                            <p>Pentru întrebări despre această politică sau prelucrarea datelor tale:</p>
                            <p><strong className="text-white">Email:</strong> <span className="text-violet-400">support@zektrix.uk</span></p>
                            <p><strong className="text-white">Adresă:</strong> Zektrix UK Ltd, c/o Bartle House, Oxford Court, Manchester, M2 3WQ</p>
                            <p className="mt-3">Dacă nu ești mulțumit de răspunsul nostru, ai dreptul să depui o plângere la <strong className="text-white">Information Commissioner's Office (ICO)</strong>:</p>
                            <p><strong className="text-white">Website:</strong> <a href="https://ico.org.uk" target="_blank" rel="noopener noreferrer" className="text-violet-400 hover:underline">ico.org.uk</a></p>
                            <p><strong className="text-white">Telefon:</strong> 0303 123 1113</p>
                        </Section>

                        <div className="mt-8 pt-6 border-t border-white/10 text-center">
                            <p className="text-gray-500 text-sm">
                                Această politică poate fi actualizată periodic. Te rugăm să verifici această pagină regulat pentru modificări.
                            </p>
                            <p className="text-gray-600 text-xs mt-2">© 2026 Zektrix UK Ltd. Toate drepturile rezervate.</p>
                        </div>
                    </div>
                </div>
            </main>
            <Footer />
        </div>
    );
};

export default PrivacyPolicyPage;
