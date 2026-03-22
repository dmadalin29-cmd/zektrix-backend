import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Card, CardContent } from '../components/ui/card';
import { Mail, MapPin, FileText, Shield, Users, Truck, Scale, AlertTriangle } from 'lucide-react';

const TermsPage = () => {
    const { isRomanian } = useLanguage();

    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />
            
            <main className="flex-1 pt-24 pb-16">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/30 mb-6">
                            <FileText className="w-4 h-4 text-primary" />
                            <span className="text-sm font-medium">{isRomanian ? 'Document Legal' : 'Legal Document'}</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black mb-4">
                            <span className="gradient-text">{isRomanian ? 'Termeni & Condiții' : 'Terms & Conditions'}</span>
                        </h1>
                        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                            {isRomanian
                                ? 'Regulile oficiale privind eligibilitatea, rutele de participare (inclusiv intrarea poștală gratuită), anunțarea rezultatelor, politica de nerambursare și livrarea premiilor pe platforma Zektrix UK.'
                                : 'Official rules regarding eligibility, entry routes (including free postal entry), result announcements, no-refund policy and prize delivery on the Zektrix UK platform.'}
                        </p>
                        <p className="text-sm text-muted-foreground mt-4">
                            {isRomanian ? 'Ultima actualizare: 1 Martie 2026' : 'Last updated: 1 March 2026'}
                        </p>
                    </div>

                    {/* Content */}
                    <div className="space-y-8">
                        {/* Section 1 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">1</span>
                                    {isRomanian ? 'Introducere' : 'Introduction'}
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>
                                        {isRomanian
                                            ? 'X67 Digital LTD („Zektrix UK", „noi") operează o platformă digitală pentru competiții promoționale transparente. Acești Termeni reprezintă acordul legal dintre utilizator și operator.'
                                            : 'X67 Digital LTD ("Zektrix UK", "we") operates a digital platform for transparent promotional competitions. These Terms constitute the legal agreement between the user and the operator.'}
                                    </p>
                                    <p>
                                        {isRomanian
                                            ? 'Prin crearea unui cont, utilizarea produselor digitale sau trimiterea unei intrări poștale gratuite confirmați că ați citit și acceptat Termenii, Politica de Confidențialitate și regulile specifice fiecărei competiții promoționale.'
                                            : 'By creating an account, using digital products or submitting a free postal entry, you confirm that you have read and accepted the Terms, Privacy Policy and specific rules of each promotional competition.'}
                                    </p>
                                    <p>
                                        {isRomanian
                                            ? <>Competițiile noastre promoționale includ întotdeauna o întrebare de cunoștințe sau un element de skill și o metodă alternativă de participare gratuită („rută poștală"). <strong>Nu este necesară nicio achiziție pentru a participa, iar efectuarea unei plăți nu crește șansele de a fi selectat ca premiant.</strong></>
                                            : <>Our promotional competitions always include a knowledge question or skill element and an alternative free entry method ("postal route"). <strong>No purchase is necessary to enter, and making a payment does not increase the chances of being selected as a winner.</strong></>}
                                    </p>
                                    <p className="text-sm italic">
                                        {isRomanian
                                            ? 'Apple nu este sponsorul acestei promoții și nu este implicată în niciun fel în acest concurs. Apple nu este responsabilă pentru organizarea concursului sau pentru selectarea ori acordarea premiilor.'
                                            : 'Apple is not a sponsor of this promotion and is not involved in any way in this contest. Apple is not responsible for the organisation of the contest or the selection or awarding of prizes.'}
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 2 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">2</span>
                                    {isRomanian ? 'Eligibilitate' : 'Eligibility'}
                                </h2>
                                <ul className="text-muted-foreground space-y-3">
                                    <li className="flex items-start gap-3">
                                        <Users className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                                        <span>{isRomanian ? 'Participanții trebuie să aibă minimum 18 ani și rezidență în jurisdicțiile unde competițiile promoționale sunt permise.' : 'Participants must be at least 18 years old and reside in jurisdictions where promotional competitions are permitted.'}</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <Shield className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                                        <span>{isRomanian ? 'Putem solicita documente KYC/AML (act de identitate, dovadă de adresă) înainte de activarea contului sau validarea unui premiu.' : 'We may request KYC/AML documents (ID, proof of address) before activating your account or validating a prize.'}</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                                        <span>{isRomanian ? 'Angajații, colaboratorii și partenerii direcți ai X67 Digital LTD, precum și membrii familiilor lor, nu pot participa la campaniile interne.' : 'Employees, collaborators and direct partners of X67 Digital LTD, as well as their family members, cannot participate in internal campaigns.'}</span>
                                    </li>
                                </ul>
                            </CardContent>
                        </Card>

                        {/* Section 3 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">3</span>
                                    {isRomanian ? 'Conturi și Securitate' : 'Accounts & Security'}
                                </h2>
                                <ul className="text-muted-foreground space-y-3">
                                    <li>• {isRomanian ? 'Utilizatorii sunt responsabili pentru confidențialitatea datelor de autentificare și pentru toate acțiunile din cont.' : 'Users are responsible for the confidentiality of their login credentials and all account activity.'}</li>
                                    <li>• {isRomanian ? 'Putem suspenda sau închide conturi care încalcă Termenii, folosesc metode automate sau încearcă să fraudeze platforma ori ceilalți participanți.' : 'We may suspend or close accounts that violate the Terms, use automated methods or attempt to defraud the platform or other participants.'}</li>
                                    <li>• {isRomanian ? 'Datele din profil trebuie să fie reale și verificabile; conturile duplicate sau identitățile false pot fi șterse fără notificare.' : 'Profile data must be real and verifiable; duplicate accounts or false identities may be deleted without notice.'}</li>
                                </ul>
                            </CardContent>
                        </Card>

                        {/* Section 4 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">4</span>
                                    {isRomanian ? 'Rute de Participare și Intrare Poștală' : 'Entry Routes & Free Postal Entry'}
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>
                                        {isRomanian
                                            ? 'Fiecare competiție promoțională afișează numărul total de participări disponibile, eventualele limite per utilizator, metodele de plată acceptate și, după caz, întrebarea de calificare. Participarea se poate înregistra în două moduri echivalente:'
                                            : 'Each promotional competition displays the total number of available entries, any per-user limits, accepted payment methods and, where applicable, the qualifying question. Entry can be registered in two equivalent ways:'}
                                    </p>
                                    <div className="grid md:grid-cols-2 gap-4">
                                        <div className="p-4 rounded-xl bg-primary/10 border border-primary/30">
                                            <h4 className="font-bold mb-2">{isRomanian ? 'A) Intrare Poștală Gratuită' : 'A) Free Postal Entry'}</h4>
                                            <p className="text-sm">{isRomanian ? 'Trimite o scrisoare cu datele tale la adresa noastră. Este întotdeauna disponibilă și tratată în același mod.' : 'Send a letter with your details to our address. Always available and treated the same way.'}</p>
                                        </div>
                                        <div className="p-4 rounded-xl bg-secondary/10 border border-secondary/30">
                                            <h4 className="font-bold mb-2">{isRomanian ? 'B) Produse Digitale / Credit' : 'B) Digital Products / Credit'}</h4>
                                            <p className="text-sm">{isRomanian ? 'Utilizarea produselor digitale sau a creditului din cont, care pot include înregistrarea automată a unei participări.' : 'Use of digital products or account credit, which may include automatic registration of an entry.'}</p>
                                        </div>
                                    </div>
                                    <p className="text-sm bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
                                        <strong>{isRomanian ? '⚠️ Important:' : '⚠️ Important:'}</strong> {isRomanian
                                            ? 'Achiziția de produse digitale sau credit este opțională și nu oferă niciun avantaj și nicio probabilitate mai mare de a fi selectat premiant față de participarea gratuită prin poștă.'
                                            : 'Purchase of digital products or credit is optional and provides no advantage or higher probability of being selected as a winner compared to free postal entry.'}
                                    </p>
                                    <p>
                                        {isRomanian
                                            ? 'Intrările incomplete, ilizibile, trimise târziu sau cu instrucțiuni nerespectate (inclusiv răspunsuri greșite la întrebarea de calificare) sunt anulate.'
                                            : 'Incomplete, illegible, late entries or those that do not follow instructions (including incorrect answers to the qualifying question) are void.'}
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 5 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">5</span>
                                    {isRomanian ? 'Programul Anunțării Rezultatelor' : 'Result Announcement Schedule'}
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>{isRomanian ? 'Fiecare competiție promoțională are o dată estimată de închidere și un moment pentru anunțarea rezultatelor, care poate fi însoțit de o prezentare live sau înregistrată.' : 'Each promotional competition has an estimated closing date and a time for result announcement, which may be accompanied by a live or recorded presentation.'}</p>
                                    <p>{isRomanian ? 'Putem devansa sau amâna anunțarea în funcție de cât de repede se ocupă locurile disponibile și de timpul necesar verificărilor de conformitate.' : 'We may bring forward or postpone the announcement depending on how quickly available spots fill and the time needed for compliance checks.'}</p>
                                    <p>{isRomanian ? 'Modificările de program sunt anunțate în aplicație și, dacă este posibil, prin e-mail. Participările valide existente rămân eligibile, iar nerambursarea nu se datorează exclusiv schimbării datei sau formatului de anunțare a rezultatelor.' : 'Schedule changes are announced in the app and, where possible, by email. Existing valid entries remain eligible, and the no-refund policy is not solely due to a change in the date or format of result announcements.'}</p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 6 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">6</span>
                                    {isRomanian ? 'Plăți și Politica de Nerambursare' : 'Payments & No-Refund Policy'}
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>{isRomanian ? 'Plățile sunt procesate securizat de furnizori autorizați (procesatori de card, Apple Pay, Google Pay etc.). De regulă, plățile se referă la produse digitale, servicii sau credit intern utilizabil pe platformă.' : 'Payments are securely processed by authorised providers (card processors, Apple Pay, Google Pay, etc.). Payments generally relate to digital products, services or internal credit usable on the platform.'}</p>
                                    <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                                        <p className="font-bold text-red-400 mb-2">{isRomanian ? 'Politica de Nerambursare' : 'No-Refund Policy'}</p>
                                        <p className="text-sm">{isRomanian ? 'După confirmarea unui produs digital sau a creditului în cont, suma devine nerambursabilă, chiar dacă ulterior decideți să nu îl folosiți sau dacă o campanie promoțională se reprogramează.' : 'Once a digital product or account credit is confirmed, the amount becomes non-refundable, even if you subsequently decide not to use it or a promotional campaign is rescheduled.'}</p>
                                    </div>
                                    <p>{isRomanian ? 'Această regulă nu afectează posibilitatea de a participa gratuit prin ruta poștală. Excepții de la nerambursare pot exista doar dacă o competiție este anulată definitiv fără reprogramare.' : 'This rule does not affect the possibility of entering free via the postal route. Exceptions to the no-refund policy may only exist if a competition is permanently cancelled without rescheduling.'}</p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 7 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">7</span>
                                    {isRomanian ? 'Selecția Premianților, Verificare și Corectitudine' : 'Winner Selection, Verification & Fairness'}
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>{isRomanian ? 'Selecția premianților respectă regulile publicate pe pagina fiecărei competiții și include numai participările care au urmat corect instrucțiunile și, după caz, au răspuns corect la întrebarea de calificare.' : 'Winner selection follows the rules published on each competition page and includes only entries that correctly followed instructions and, where applicable, correctly answered the qualifying question.'}</p>
                                    <p className="font-bold text-white">{isRomanian ? 'Nicio plată, sold al contului sau tip de participare (printr-un produs digital sau rută poștală) nu crește probabilitatea de a fi selectat premiant.' : 'No payment, account balance or type of entry (via digital product or postal route) increases the probability of being selected as a winner.'}</p>
                                    <ul className="space-y-2">
                                        <li>• {isRomanian ? 'Procedurile de desemnare a premianților sunt concepute pentru a fi transparente și verificabile și pot include transmisii publice, înregistrări, observatori independenți sau instrumente auditate.' : 'Winner selection procedures are designed to be transparent and verifiable and may include public broadcasts, recordings, independent observers or audited tools.'}</li>
                                        <li>• {isRomanian ? 'Premianții sunt anunțați prin e-mail și în cont și trebuie să răspundă în maximum 14 zile.' : 'Winners are notified by email and in their account and must respond within 14 days.'}</li>
                                        <li>• {isRomanian ? 'Nerespectarea termenului sau refuzul / imposibilitatea de a furniza documentele solicitate duce la pierderea premiului și alegerea unui alt participant.' : 'Failure to respond within the deadline or refusal/inability to provide requested documents results in forfeiture of the prize and selection of another participant.'}</li>
                                    </ul>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 8 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">8</span>
                                    {isRomanian ? 'Livrarea Premiilor și Obligații Fiscale' : 'Prize Delivery & Tax Obligations'}
                                </h2>
                                <div className="text-muted-foreground space-y-4">
                                    <p>{isRomanian ? 'Premiile fizice sunt expediate după verificarea identității și semnarea documentelor de acceptare. Transportul standard este suportat de noi, însă taxele vamale, impozitele locale, înmatricularea sau asigurarea revin în sarcina premiantului, dacă nu se precizează altfel pe pagina competiției.' : 'Physical prizes are shipped after identity verification and signing of acceptance documents. Standard shipping is covered by us, but customs duties, local taxes, registration or insurance are the responsibility of the winner, unless otherwise stated on the competition page.'}</p>
                                    <p>{isRomanian ? 'Premiile în bani sunt transferate în contul bancar verificat, în moneda anunțată pe pagina competiției. Sunteți responsabil(ă) pentru declararea și plata eventualelor taxe datorate în țara de rezidență.' : 'Cash prizes are transferred to the verified bank account in the currency announced on the competition page. You are responsible for declaring and paying any taxes due in your country of residence.'}</p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Section 9 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-3">
                                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold">9</span>
                                    {isRomanian ? 'Conduită și Utilizări Interzise' : 'Conduct & Prohibited Uses'}
                                </h2>
                                <ul className="text-muted-foreground space-y-3">
                                    <li className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                                        <span>{isRomanian ? 'Este interzisă folosirea de boți, scripturi, conturi multiple sau distribuirea răspunsurilor la întrebări pentru obținerea de avantaje neloiale.' : 'The use of bots, scripts, multiple accounts or sharing answers to questions for unfair advantage is prohibited.'}</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                                        <span>{isRomanian ? 'Hărțuirea, limbajul ofensator sau comportamentul abuziv la adresa echipei și a celorlalți participanți (chat, e-mail, social media) sunt interzise.' : 'Harassment, offensive language or abusive behaviour towards the team and other participants (chat, email, social media) is prohibited.'}</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                                        <span>{isRomanian ? 'Încălcările grave pot duce la ban permanent și raportarea către autoritățile competente.' : 'Serious violations may result in a permanent ban and reporting to the relevant authorities.'}</span>
                                    </li>
                                </ul>
                            </CardContent>
                        </Card>

                        {/* Section 10-13 */}
                        <Card className="glass border-white/10">
                            <CardContent className="p-6 space-y-6">
                                <div>
                                    <h2 className="text-xl font-bold mb-3 flex items-center gap-3">
                                        <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">10</span>
                                        {isRomanian ? 'Limitarea Răspunderii' : 'Limitation of Liability'}
                                    </h2>
                                    <p className="text-muted-foreground">{isRomanian ? 'Platforma este furnizată „ca atare". Nu garantăm disponibilitate continuă și nu răspundem pentru pierderi indirecte sau de oportunitate cauzate de mentenanță, întreruperi sau evenimente de forță majoră. Răspunderea totală a X67 Digital LTD față de un utilizator nu va depăși valoarea plătită pentru produse digitale sau credit intern în ultimele 12 luni.' : 'The platform is provided "as is". We do not guarantee continuous availability and are not liable for indirect losses or lost opportunities caused by maintenance, interruptions or force majeure events. The total liability of X67 Digital LTD to a user shall not exceed the amount paid for digital products or internal credit in the last 12 months.'}</p>
                                </div>

                                <div>
                                    <h2 className="text-xl font-bold mb-3 flex items-center gap-3">
                                        <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">11</span>
                                        {isRomanian ? 'Proprietate Intelectuală' : 'Intellectual Property'}
                                    </h2>
                                    <p className="text-muted-foreground">{isRomanian ? 'Mărcile, logo-urile și materialele publicate aparțin X67 Digital LTD sau partenerilor. Reproducerea sau distribuirea fără acord scris este interzisă.' : 'Trademarks, logos and published materials belong to X67 Digital LTD or its partners. Reproduction or distribution without written agreement is prohibited.'}</p>
                                </div>

                                <div>
                                    <h2 className="text-xl font-bold mb-3 flex items-center gap-3">
                                        <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">12</span>
                                        {isRomanian ? 'Suspendare și Reziliere' : 'Suspension & Termination'}
                                    </h2>
                                    <p className="text-muted-foreground">{isRomanian ? 'Putem suspenda, modifica sau închide platforma ori anumite competiții promoționale atunci când este necesar pentru protejarea integrității, prevenirea abuzurilor sau respectarea obligațiilor legale.' : 'We may suspend, modify or close the platform or certain promotional competitions when necessary to protect integrity, prevent abuse or comply with legal obligations.'}</p>
                                </div>

                                <div>
                                    <h2 className="text-xl font-bold mb-3 flex items-center gap-3">
                                        <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">13</span>
                                        {isRomanian ? 'Legea Aplicabilă și Dispute' : 'Governing Law & Disputes'}
                                    </h2>
                                    <p className="text-muted-foreground">{isRomanian ? 'Acești Termeni sunt guvernați de legislația Angliei și Țării Galilor. Litigiile se soluționează de instanțele competente din Manchester, Regatul Unit. Încurajăm contactarea mai întâi a echipei de suport pentru o rezolvare amiabilă.' : 'These Terms are governed by the laws of England and Wales. Disputes are resolved by the competent courts of Manchester, United Kingdom. We encourage contacting our support team first for an amicable resolution.'}</p>
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
                                    {isRomanian
                                        ? 'Solicitările legale pot fi trimise la adresa de mai jos sau pe e-mail. Ne rezervăm dreptul de a actualiza periodic acești Termeni; versiunea activă este publicată pe această pagină.'
                                        : 'Legal requests can be sent to the address below or by email. We reserve the right to periodically update these Terms; the active version is published on this page.'}
                                </p>
                                <div className="grid md:grid-cols-2 gap-6">
                                    <div className="flex items-start gap-4 p-4 rounded-xl bg-black/30">
                                        <MapPin className="w-6 h-6 text-primary flex-shrink-0" />
                                        <div>
                                            <h4 className="font-bold mb-1">{isRomanian ? 'Adresă' : 'Address'}</h4>
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
                                                {isRomanian ? 'Echipa juridică răspunde în maximum 3 zile lucrătoare.' : 'The legal team responds within 3 working days.'}
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
