import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Mail, MailX, CheckCircle, XCircle, ArrowLeft, RefreshCw } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function UnsubscribePage() {
  const { userId } = useParams();
  const [status, setStatus] = useState('loading'); // loading, subscribed, unsubscribed, error
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    checkStatus();
  }, [userId]);

  const checkStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/email/status/${userId}`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data.subscribed ? 'subscribed' : 'unsubscribed');
        setEmail(data.email);
      } else {
        setStatus('error');
        setMessage('Link invalid sau expirat.');
      }
    } catch (err) {
      setStatus('error');
      setMessage('Eroare de conexiune. Incearca din nou.');
    }
  };

  const handleUnsubscribe = async () => {
    setIsProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/email/unsubscribe/${userId}`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setStatus('unsubscribed');
        setMessage(data.message);
        setEmail(data.email);
      } else {
        setMessage('Eroare la dezabonare. Incearca din nou.');
      }
    } catch (err) {
      setMessage('Eroare de conexiune.');
    }
    setIsProcessing(false);
  };

  const handleResubscribe = async () => {
    setIsProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/email/resubscribe/${userId}`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setStatus('subscribed');
        setMessage(data.message);
        setEmail(data.email);
      } else {
        setMessage('Eroare la reabonare. Incearca din nou.');
      }
    } catch (err) {
      setMessage('Eroare de conexiune.');
    }
    setIsProcessing(false);
  };

  return (
    <div className="min-h-screen bg-[#030014] flex items-center justify-center p-4">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-violet-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-orange-500/10 rounded-full blur-[100px]" />
      </div>

      <div className="relative w-full max-w-lg">
        {/* Card */}
        <div className="bg-gradient-to-br from-[#0f0a1a]/90 to-[#1a1033]/90 backdrop-blur-xl border border-violet-500/20 rounded-3xl p-8 shadow-2xl">
          
          {/* Logo */}
          <div className="text-center mb-8">
            <Link to="/" className="inline-block">
              <h1 className="text-3xl font-black">
                <span className="bg-gradient-to-r from-violet-500 via-fuchsia-500 to-orange-500 bg-clip-text text-transparent">ZEKTRIX</span>
                <span className="text-white">.UK</span>
              </h1>
            </Link>
            <p className="text-gray-500 text-sm mt-2">Gestionare Preferinte Email</p>
          </div>

          {/* Content based on status */}
          {status === 'loading' && (
            <div className="text-center py-12">
              <RefreshCw className="w-12 h-12 text-violet-400 animate-spin mx-auto mb-4" />
              <p className="text-gray-400">Se incarca...</p>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center py-8">
              <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <XCircle className="w-10 h-10 text-red-400" />
              </div>
              <h2 className="text-xl font-bold text-white mb-3">Eroare</h2>
              <p className="text-gray-400 mb-6">{message}</p>
              <Link 
                to="/"
                className="inline-flex items-center gap-2 px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white rounded-xl font-semibold transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                Inapoi la site
              </Link>
            </div>
          )}

          {status === 'subscribed' && (
            <div className="text-center py-8">
              <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse">
                <Mail className="w-10 h-10 text-green-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-3">Esti Abonat</h2>
              <p className="text-gray-400 mb-2">
                Primesti email-uri promotionale la adresa:
              </p>
              <p className="text-violet-400 font-semibold mb-8">{email}</p>
              
              {message && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 mb-6">
                  <p className="text-green-400 text-sm">{message}</p>
                </div>
              )}

              <div className="space-y-4">
                <button
                  onClick={handleUnsubscribe}
                  disabled={isProcessing}
                  className="w-full px-6 py-4 bg-gradient-to-r from-red-600/20 to-red-500/20 hover:from-red-600/30 hover:to-red-500/30 border border-red-500/30 text-red-400 rounded-xl font-semibold transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                >
                  {isProcessing ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : (
                    <MailX className="w-5 h-5" />
                  )}
                  Dezaboneaza-ma de la newsletter
                </button>
                
                <p className="text-gray-500 text-xs">
                  Vei continua sa primesti email-uri importante despre contul tau si castiguri.
                </p>
              </div>
            </div>
          )}

          {status === 'unsubscribed' && (
            <div className="text-center py-8">
              <div className="w-20 h-20 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <MailX className="w-10 h-10 text-orange-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-3">Dezabonat</h2>
              <p className="text-gray-400 mb-2">
                Nu mai primesti email-uri promotionale la:
              </p>
              <p className="text-violet-400 font-semibold mb-8">{email}</p>

              {message && (
                <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4 mb-6">
                  <p className="text-orange-400 text-sm">{message}</p>
                </div>
              )}

              <div className="space-y-4">
                <button
                  onClick={handleResubscribe}
                  disabled={isProcessing}
                  className="w-full px-6 py-4 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white rounded-xl font-semibold transition-all flex items-center justify-center gap-3 shadow-lg shadow-violet-500/25 disabled:opacity-50"
                >
                  {isProcessing ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : (
                    <Mail className="w-5 h-5" />
                  )}
                  Vreau sa ma reabonez!
                </button>

                <p className="text-gray-500 text-xs">
                  Nu rata competitiile cu premii de pana la 5000 RON!
                </p>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-violet-500/10 text-center">
            <Link 
              to="/"
              className="inline-flex items-center gap-2 text-gray-400 hover:text-violet-400 transition-colors text-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              Inapoi la Zektrix.uk
            </Link>
          </div>
        </div>

        {/* GDPR Notice */}
        <div className="mt-6 text-center">
          <p className="text-gray-600 text-xs">
            Conform GDPR, ai dreptul sa iti gestionezi preferintele de comunicare.
            <br />
            Datele tale sunt in siguranta si nu sunt partajate cu terti.
          </p>
        </div>
      </div>
    </div>
  );
}
