import React, { Suspense, lazy } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LanguageProvider } from "./context/LanguageContext";
import { CartProvider } from "./context/CartContext";
import { Toaster } from "./components/ui/sonner";

// Pages - Eagerly loaded (critical path)
import LoginPage from "./pages/LoginPage";
import AuthCallback from "./pages/AuthCallback";

// Pages - Lazy loaded (better performance)
const HomePage = lazy(() => import("./pages/HomePage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const CompetitionsPage = lazy(() => import("./pages/CompetitionsPage"));
const CompetitionDetailPage = lazy(() => import("./pages/CompetitionDetailPage"));
const WinnersPage = lazy(() => import("./pages/WinnersPage"));
const SearchTicketsPage = lazy(() => import("./pages/SearchTicketsPage"));
const FAQPage = lazy(() => import("./pages/FAQPage"));
const TermsPage = lazy(() => import("./pages/TermsPage"));
const AdminPage = lazy(() => import("./pages/AdminPage"));
const ReferralPage = lazy(() => import("./pages/ReferralPage"));
const CartPage = lazy(() => import("./pages/CartPage"));
const PaymentSuccessPage = lazy(() => import("./pages/PaymentSuccessPage"));
const PaymentFailedPage = lazy(() => import("./pages/PaymentFailedPage"));
// Lucky Wheel removed
const ForgotPasswordPage = lazy(() => import("./pages/ForgotPasswordPage"));
const ResetPasswordPage = lazy(() => import("./pages/ResetPasswordPage"));
const UnsubscribePage = lazy(() => import("./pages/UnsubscribePage"));
const CompleteProfilePage = lazy(() => import("./pages/CompleteProfilePage"));

// Global Components
import InstallPrompt from "./components/InstallPrompt";
import CookieConsent from "./components/CookieConsent";
import ScrollToTop from "./components/ScrollToTop";
import LiveChat from "./components/LiveChat";

// Loading fallback component
const PageLoader = () => (
    <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
    </div>
);

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false }) => {
    const { isAuthenticated, isAdmin, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    if (adminOnly && !isAdmin) {
        return <Navigate to="/dashboard" replace />;
    }

    return children;
};

// App Router with session_id detection
const AppRouter = () => {
    const location = useLocation();

    // Check URL fragment (not query params) for session_id
    // This must happen BEFORE ProtectedRoute to handle OAuth callback
    if (location.hash?.includes('session_id=')) {
        return <AuthCallback />;
    }

    return (
        <Suspense fallback={<PageLoader />}>
            <Routes>
                {/* Public Routes */}
                <Route path="/" element={<HomePage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/auth/callback" element={<AuthCallback />} />
                <Route path="/competitions" element={<CompetitionsPage />} />
                <Route path="/competitions/:id" element={<CompetitionDetailPage />} />
                <Route path="/cart" element={<CartPage />} />
                <Route path="/winners" element={<WinnersPage />} />
                <Route path="/search" element={<SearchTicketsPage />} />
                <Route path="/faq" element={<FAQPage />} />
                <Route path="/terms" element={<TermsPage />} />
                <Route path="/payment/success" element={<PaymentSuccessPage />} />
                <Route path="/payment/failed" element={<PaymentFailedPage />} />
                {/* Lucky Wheel removed */}
                <Route path="/unsubscribe/:userId" element={<UnsubscribePage />} />
                <Route path="/complete-profile" element={<CompleteProfilePage />} />

                {/* Protected Routes */}
                <Route
                    path="/dashboard"
                    element={
                        <ProtectedRoute>
                            <DashboardPage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/dashboard/tickets"
                    element={
                        <ProtectedRoute>
                            <DashboardPage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/dashboard/history"
                    element={
                        <ProtectedRoute>
                            <DashboardPage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/dashboard/referral"
                    element={
                        <ProtectedRoute>
                            <ReferralPage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/referral"
                    element={
                        <ProtectedRoute>
                            <ReferralPage />
                        </ProtectedRoute>
                    }
                />

                {/* Admin Routes */}
                <Route
                    path="/admin"
                    element={
                        <ProtectedRoute adminOnly>
                            <AdminPage />
                        </ProtectedRoute>
                    }
                />

                {/* Catch all - redirect to home */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </Suspense>
    );
};

function App() {
    return (
        <LanguageProvider>
            <AuthProvider>
                <CartProvider>
                    <div className="App dark">
                        <BrowserRouter>
                            <ScrollToTop />
                            <AppRouter />
                            <LiveChat />
                        </BrowserRouter>
                        <Toaster position="top-right" richColors closeButton />
                        <InstallPrompt />
                        <CookieConsent />
                    </div>
                </CartProvider>
            </AuthProvider>
        </LanguageProvider>
    );
}

export default App;
