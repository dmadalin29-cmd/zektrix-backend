# Zektrix UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, AI-powered live chat with push notifications for admins, and PWA.

## Tech Stack
- **Frontend:** React (Hostinger - zektrix.uk)
- **Backend:** FastAPI (Railway - zektrix-backend-production.up.railway.app)
- **Database:** MongoDB Atlas (DB: ektrix_db)
- **Payments:** Viva Payments
- **AI Chat:** Gemini Flash via emergentintegrations
- **Push Notifications:** pywebpush + VAPID (all users)
- **Auth:** JWT + Google Auth (Emergent-managed)
- **Email:** Resend API

## Architecture (After Refactoring)
```
/app/backend/
├── server.py          # Main FastAPI app + routes (~4600 lines, down from 5150)
├── models.py          # All Pydantic models (extracted)
├── email_service.py   # Email functions (extracted)
├── push_service.py    # Push notification helpers (extracted)
├── uploads/           # Uploaded competition images
├── vapid_private.pem  # Auto-generated from env at startup
└── .env               # All credentials
```

## Core Features (Implemented)
- JWT & Google Auth
- Competition browsing, ticket purchasing via Viva Payments
- Image upload for competitions (admin can upload or paste URL)
- Multi-image gallery for competitions
- "My Account" dashboard with ticket history
- AI Chat (Gemini Flash) with live chat escalation
- Admin panel (user/competition/winner management)
- PWA with service worker
- Push notifications for ALL users (chat replies, winner draws, 70/80/90% alerts)
- Personalized email alerts at 70%/80%/90% competition milestones
- Modern daily digest emails with realistic prize calculations and competition images
- Social sharing (WhatsApp, Facebook, Twitter, copy link)
- Modern floating navbar with glassmorphism
- Bilingual (Romanian/English)
- Free competition "MEGA PREMIU £5.000" with tiered instant prizes
- **Wallet System**: Full deposit/withdraw/history/bonus system
  - Wallet balance in navbar
  - Deposit via Viva Payments with quick amounts (£10-£500)
  - Configurable deposit bonus (% + max cap from Admin)
  - Withdrawal requests with admin approval flow
  - Transaction history with icons and status
  - Admin Wallet Management: stats, bonus config, approve/reject withdrawals, manual fund adjustment
- **Subscription System (NEW)**: 3 fixed plans with auto ticket distribution
  - Abonament 25 (£25/luna, 2 bilete/competitie)
  - Abonament 50 (£50/luna, 5 bilete/competitie) — Cel Mai Popular
  - Abonament 100 (£100/luna, 12 bilete/competitie)
  - Plata din wallet sau cu cardul (Viva Payments)
  - Auto-distribuire bilete la toate competitiile active (pret ≤ £3.99)
  - Auto-distribuire la competitii noi lansate
  - Auto-reinnoire din wallet (sau expira daca fonduri insuficiente)
  - Anulare reinoire oricand
  - Push notifications la distribuire bilete si reinnoire
  - Admin: statistici abonamente, lista abonati, venituri
- Featured Competition (Ofertă Recomandată) customizable from Admin Settings

## Completed This Session (March 20, 2026)
- **FIXED: Push Notifications (P0)** - Synced VAPID keys, pywebpush library, auto-derive public key
- **FIXED: Frontend .env** - Preview URL → production URL
- **FIXED: DB_NAME** - zektrix_db → ektrix_db
- **VERIFIED: Live Chat E2E** - All working
- **NEW: Push notifications for all users** - Chat replies, winner draws, competition alerts
- **NEW: Image upload for competitions** - Admin can upload images directly (not just URLs)
- **NEW: Multi-image gallery** - Multiple images per competition with thumbnail gallery
- **NEW: Personalized milestone emails** - Automated at 70%/80%/90% for participants
- **NEW: Featured Competition (Ofertă Recomandată)** - Admin can select which competition appears as featured on homepage
- **NEW: Wallet System** - Complete wallet with deposit (Viva), withdrawals, history, bonus, admin management
- **NEW: Subscription System** - 3 plans (£25/£50/£100), auto ticket distribution, auto-renewal, Viva + wallet payment
- **REDESIGN: Complete visual modernization**
  - Apple-style mesh gradient backgrounds (animated, subtle)
  - Glassmorphism cards (backdrop-blur, transparent backgrounds)
  - Outfit font for headings, Inter for body
  - Framer Motion animations on cards and sections
  - Removed all hardcoded dark backgrounds → mesh gradient shows through
  - Updated: Navbar, Footer, CompetitionCard, HomePage, CompetitionsPage, WalletPage, SubscriptionsPage, DashboardPage, LoginPage, WinnersPage, FAQPage, PrivacyPage, TermsPage, SearchPage
  - React.memo on CompetitionCard for performance
  - Lazy loading on all images
- **MODERNIZED: Daily digest emails** - Premium design, realistic prize calculation (price×tickets), competition images
- **REFACTORED: server.py** - Extracted models.py, email_service.py, push_service.py (-540 lines)
- **FIXED: Admin Settings crash (March 20)** - `competitions` → `comps` variable reference in Settings tab
- Social sharing already existed (WhatsApp, Facebook, Twitter, Copy Link)
- Terms & Conditions page already complete

## Upcoming Tasks
- **P1:** Facebook Pixel integration
- **P2:** Bundle Deals
- **P2:** SMS Marketing
- **P2:** Leaderboard
- **P2:** Referral System improvements
