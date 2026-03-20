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

## Architecture
```
/app/backend/
├── server.py          # Main FastAPI app + routes (~5600+ lines)
├── models.py          # All Pydantic models
├── email_service.py   # Email functions
├── push_service.py    # Push notification helpers
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
- **Subscription System**: 3 fixed plans with auto ticket distribution
  - Abonament 25/50/100 (£25/£50/£100 luna)
  - Auto-distribuire bilete la competitii active
  - Auto-reinnoire din wallet
  - Push notifications la distribuire si reinnoire
  - Admin: statistici abonamente, lista abonati, venituri
- **Premium Referral System** (COMPLETED March 20, 2026)
  - £3 credit for referrer, £2 for referred on first purchase
  - Custom referral code (3-15 chars, alphanumeric)
  - Share via WhatsApp + Copy Link
  - Referral leaderboard (top referrers)
  - Invited friends list with status (pending/completed)
  - How it Works 3-step guide
  - Guest-accessible /referral page with sign-up CTA
  - Admin referral stats endpoint
  - Backend: /api/referral/my, /api/referral/customize, /api/referral/leaderboard, /api/admin/referral/stats
- Featured Competition (Ofertă Recomandată) customizable from Admin Settings
- **Global UI Redesign**: Apple-style mesh gradients, glassmorphism, Outfit font, Framer Motion animations

## Upcoming Tasks
- **P1:** TikTok Pixel Integration (when user starts running ads)
- **P2:** Countdown Timer on competitions
- **P2:** Bundle Deals (ticket packages with discounts)
- **P2:** SMS Marketing
- **P2:** Refactor `server.py` (~5600+ lines → modular routes)
