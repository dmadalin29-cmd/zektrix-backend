import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Card, CardContent } from '../components/ui/card';
import { Mail, MapPin, FileText, Shield, Users, Truck, Scale, AlertTriangle } from 'lucide-react';

const TermsPage = () => {
    const { isRomanian } = useLanguage();

    return (
        <div className="min-h-screen bg-background flex flex-col">
            <Navbar />
            
            <main className="flex-1 pt-24 pb-16">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/30 mb-6">
                            <FileText className="w-4 h-4 text-primary" />
                            <span className="text-sm font-medium">Document Legal</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black mb-4">
                            <span className="gradient-text">Termeni & Condiții</span>
                        </h1>
                        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                            Regulile oficiale privind eligibilitatea, rutele de participare (inclusiv intrarea poștală gratuită), 
                            anunțarea rezultatelor, politica de nerambursare și livrarea premiilor pe platforma Zektrix UK.
                        </p>
                        <p className="text-sm text-muted-foreground mt-4">
                            Ultima actualizare: 1 Martie 2026
                        </p>
                    </div>

                    {/* Content */}
                    <div className="space-y-8">
                        {/* Section 1 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">1</span>
                                    Introducere
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>
                                        X67 Digital LTD („Zektrix UK", „noi") operează o platformă digitală pentru competiții promoționale transparente. 
                                        Acești Termeni reprezintă acordul legal dintre utilizator și operator.
                                    </p>
                                    <p>
                                        Prin crearea unui cont, utilizarea produselor digitale sau trimiterea unei intrări poștale gratuite confirmați 
                                        că ați citit și acceptat Termenii, Politica de Confidențialitate și regulile specifice fiecărei competiții promoționale.
                                    </p>
                                    <p>
                                        Competițiile noastre promoționale includ întotdeauna o întrebare de cunoștințe sau un element de skill și o metodă 
                                        alternativă de participare gratuită („rută poștală"). <strong>Nu este necesară nicio achiziție pentru a participa, 
                                        iar efectuarea unei plăți nu crește șansele de a fi selectat ca premiant.</strong>
                                    </p>
                                    <p className="text-sm italic">
                                        Apple nu este sponsorul acestei promoții și nu este implicată în niciun fel în acest concurs. 
                                        Apple nu este responsabilă pentru organizarea concursului sau pentru selectarea ori acordarea premiilor.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 2 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">2</span>
                                    Eligibilitate
                                </h2>
                                <ul className="text-muted-foreground space-y-3">
                                    <li className="flex items-start gap-3">
                                        <Users className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                                        <span>Participanții trebuie să aibă minimum 18 ani și rezidență în jurisdicțiile unde competițiile promoționale sunt permise.</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <Shield className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                                        <span>Putem solicita documente KYC/AML (act de identitate, dovadă de adresă) înainte de activarea contului sau validarea unui premiu.</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                                        <span>Angajații, colaboratorii și partenerii direcți ai X67 Digital LTD, precum și membrii familiilor lor, nu pot participa la campaniile interne.</span>
                                    </li>
                                </ul>
                            </CardContent>
                        </Card>

                        {/* Section 3 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">3</span>
                                    Conturi și Securitate
                                </h2>
                                <ul className="text-muted-foreground space-y-3">
                                    <li>• Utilizatorii sunt responsabili pentru confidențialitatea datelor de autentificare și pentru toate acțiunile din cont.</li>
                                    <li>• Putem suspenda sau închide conturi care încalcă Termenii, folosesc metode automate sau încearcă să fraudeze platforma ori ceilalți participanți.</li>
                                    <li>• Datele din profil trebuie să fie reale și verificabile; conturile duplicate sau identitățile false pot fi șterse fără notificare.</li>
                                </ul>
                            </CardContent>
                        </Card>

                        {/* Section 4 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">4</span>
                                    Rute de Participare și Intrare Poștală
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>
                                        Fiecare competiție promoțională afișează numărul total de participări disponibile, eventualele limite per utilizator, 
                                        metodele de plată acceptate și, după caz, întrebarea de calificare. Participarea se poate înregistra în două moduri echivalente:
                                    </p>
                                    <div className="grid md:grid-cols-2 gap-4">
                                        <div className="p-4 rounded-xl bg-primary/10 border border-primary/30">
                                            <h4 className="font-bold mb-2">A) Intrare Poștală Gratuită</h4>
                                            <p className="text-sm">Trimite o scrisoare cu datele tale la adresa noastră. Este întotdeauna disponibilă și tratată în același mod.</p>
                                        </div>
                                        <div className="p-4 rounded-xl bg-secondary/10 border border-secondary/30">
                                            <h4 className="font-bold mb-2">B) Produse Digitale / Credit</h4>
                                            <p className="text-sm">Utilizarea produselor digitale sau a creditului din cont, care pot include înregistrarea automată a unei participări.</p>
                                        </div>
                                    </div>
                                    <p className="text-sm bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
                                        <strong>⚠️ Important:</strong> Achiziția de produse digitale sau credit este opțională și nu oferă niciun avantaj și nicio 
                                        probabilitate mai mare de a fi selectat premiant față de participarea gratuită prin poștă.
                                    </p>
                                    <p>
                                        Intrările incomplete, ilizibile, trimise târziu sau cu instrucțiuni nerespectate (inclusiv răspunsuri greșite la întrebarea 
                                        de calificare) sunt anulate.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 5 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">5</span>
                                    Programul Anunțării Rezultatelor
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>
                                        Fiecare competiție promoțională are o dată estimată de închidere și un moment pentru anunțarea rezultatelor, 
                                        care poate fi însoțit de o prezentare live sau înregistrată.
                                    </p>
                                    <p>
                                        Putem devansa sau amâna anunțarea în funcție de cât de repede se ocupă locurile disponibile și de timpul necesar verificărilor de conformitate.
                                    </p>
                                    <p>
                                        Modificările de program sunt anunțate în aplicație și, dacă este posibil, prin e-mail. 
                                        Participările valide existente rămân eligibile, iar nerambursarea nu se datorează exclusiv schimbării datei sau formatului de anunțare a rezultatelor.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 6 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">6</span>
                                    Plăți și Politica de Nerambursare
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>
                                        Plățile sunt procesate securizat de furnizori autorizați (procesatori de card, Apple Pay, Google Pay etc.). 
                                        De regulă, plățile se referă la produse digitale, servicii sau credit intern utilizabil pe platformă.
                                    </p>
                                    <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                                        <p className="font-bold text-red-400 mb-2">Politica de Nerambursare</p>
                                        <p className="text-sm">
                                            După confirmarea unui produs digital sau a creditului în cont, suma devine nerambursabilă, 
                                            chiar dacă ulterior decideți să nu îl folosiți sau dacă o campanie promoțională se reprogramează.
                                        </p>
                                    </div>
                                    <p>
                                        Această regulă nu afectează posibilitatea de a participa gratuit prin ruta poștală. 
                                        Excepții de la nerambursare pot exista doar dacă o competiție este anulată definitiv fără reprogramare.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 7 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">7</span>
                                    Selecția Premianților, Verificare și Corectitudine
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>
                                        Selecția premianților respectă regulile publicate pe pagina fiecărei competiții și include numai participările 
                                        care au urmat corect instrucțiunile și, după caz, au răspuns corect la întrebarea de calificare.
                                    </p>
                                    <p className="font-bold text-white">
                                        Nicio plată, sold al contului sau tip de participare (printr-un produs digital sau rută poștală) nu crește probabilitatea de a fi selectat premiant.
                                    </p>
                                    <ul className="space-y-2">
                                        <li>• Procedurile de desemnare a premianților sunt concepute pentru a fi transparente și verificabile și pot include transmisii publice, înregistrări, observatori independenți sau instrumente auditate.</li>
                                        <li>• Premianții sunt anunțați prin e-mail și în cont și trebuie să răspundă în maximum 14 zile.</li>
                                        <li>• Nerespectarea termenului sau refuzul / imposibilitatea de a furniza documentele solicitate duce la pierderea premiului și alegerea unui alt participant.</li>
                                    </ul>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 8 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">8</span>
                                    Livrarea Premiilor și Obligații Fiscale
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>
                                        Premiile fizice sunt expediate după verificarea identității și semnarea documentelor de acceptare. 
                                        Transportul standard este suportat de noi, însă taxele vamale, impozitele locale, înmatricularea sau asigurarea 
                                        revin în sarcina premiantului, dacă nu se precizează altfel pe pagina competiției.
                                    </p>
                                    <p>
                                        Premiile în bani sunt transferate în contul bancar verificat, în moneda anunțată pe pagina competiției. 
                                        Sunteți responsabil(ă) pentru declararea și plata eventualelor taxe datorate în țara de rezidență.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 9 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">9</span>
                                    Conduită și Utilizări Interzise
                                </h2>
                                <ul className="text-muted-foreground space-y-3">
                                    <li className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                                        <span>Este interzisă folosirea de boți, scripturi, conturi multiple sau distribuirea răspunsurilor la întrebări pentru obținerea de avantaje neloiale.</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                                        <span>Hărțuirea, limbajul ofensator sau comportamentul abuziv la adresa echipei și a celorlalți participanți (chat, e-mail, social media) sunt interzise.</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                                        <span>Încălcările grave pot duce la ban permanent și raportarea către autoritățile competente.</span>
                                    </li>
                                </ul>
                            </CardContent>
                        </Card>

                        {/* Section 10-14 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6 space-y-6">
                                <div>
                                    <h2 className="text-xl font-bold mb-3 flex items-center gap-3">
                                        <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">10</span>
                                        Limitarea Răspunderii
                                    </h2>
                                    <p className="text-muted-foreground">
                                        Platforma este furnizată „ca atare". Nu garantăm disponibilitate continuă și nu răspundem pentru pierderi indirecte 
                                        sau de oportunitate cauzate de mentenanță, întreruperi sau evenimente de forță majoră. Răspunderea totală a X67 Digital LTD 
                                        față de un utilizator nu va depăși valoarea plătită pentru produse digitale sau credit intern în ultimele 12 luni.
                                    </p>
                                </div>

                                <div>
                                    <h2 className="text-xl font-bold mb-3 flex items-center gap-3">
                                        <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">11</span>
                                        Proprietate Intelectuală
                                    </h2>
                                    <p className="text-muted-foreground">
                                        Mărcile, logo-urile și materialele publicate aparțin X67 Digital LTD sau partenerilor. 
                                        Reproducerea sau distribuirea fără acord scris este interzisă.
                                    </p>
                                </div>

                                <div>
                                    <h2 className="text-xl font-bold mb-3 flex items-center gap-3">
                                        <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">12</span>
                                        Suspendare și Reziliere
                                    </h2>
                                    <p className="text-muted-foreground">
                                        Putem suspenda, modifica sau închide platforma ori anumite competiții promoționale atunci când este necesar pentru 
                                        protejarea integrității, prevenirea abuzurilor sau respectarea obligațiilor legale.
                                    </p>
                                </div>

                                <div>
                                    <h2 className="text-xl font-bold mb-3 flex items-center gap-3">
                                        <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">13</span>
                                        Legea Aplicabilă și Dispute
                                    </h2>
                                    <p className="text-muted-foreground">
                                        Acești Termeni sunt guvernați de legislația Angliei și Țării Galilor. 
                                        Litigiile se soluționează de instanțele competente din Manchester, Regatul Unit. 
                                        Încurajăm contactarea mai întâi a echipei de suport pentru o rezolvare amiabilă.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Contact Section */}
                        <Card className="glass border-primary/30 bg-gradient-to-br from-primary/10 to-secondary/10">
                            <CardContent className="p-8">
                                <h2 className="text-2xl font-bold mb-6 text-center">
                                    <span className="gradient-text">14. Contact</span>
                                </h2>
                                <p className="text-muted-foreground text-center mb-6">
                                    Solicitările legale pot fi trimise la adresa de mai jos sau pe e-mail. 
                                    Ne rezervăm dreptul de a actualiza periodic acești Termeni; versiunea activă este publicată pe această pagină.
                                </p>
                                <div className="grid md:grid-cols-2 gap-6">
                                    <div className="flex items-start gap-4 p-4 rounded-xl bg-black/30">
                                        <MapPin className="w-6 h-6 text-primary flex-shrink-0" />
                                        <div>
                                            <h4 className="font-bold mb-1">Adresă</h4>
                                            <p className="text-sm text-muted-foreground">
                                                X67 Digital LTD<br />
                                                c/o Bartle House, Oxford Court<br />
                                                Manchester, M23 WQ<br />
                                                United Kingdom
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-start gap-4 p-4 rounded-xl bg-black/30">
                                        <Mail className="w-6 h-6 text-primary flex-shrink-0" />
                                        <div>
                                            <h4 className="font-bold mb-1">E-mail</h4>
                                            <a href="mailto:contact@x67digital.com" className="text-primary hover:underline">
                                                contact@x67digital.com
                                            </a>
                                            <p className="text-sm text-muted-foreground mt-2">
                                                Echipa juridică răspunde în maximum 3 zile lucrătoare.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </main>

            <Footer />
        </div>
    );
};

export default TermsPage;
