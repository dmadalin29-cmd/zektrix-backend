# Zektrix UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, AI-powered live chat with push notifications for admins, and PWA.

## Tech Stack
- **Frontend:** React (Hostinger - zektrix.uk)
- **Backend:** FastAPI (Railway - zektrix-backend-production.up.railway.app)
- **Database:** MongoDB Atlas (DB: ektrix_db)
- **Payments:** Viva Payments
- **AI Chat:** Gemini Flash via emergentintegrations
- **Push Notifications:** pywebpush + VAPID (for ALL users)
- **Auth:** JWT + Google Auth (Emergent-managed)

## Core Features (Implemented)
- JWT & Google Auth
- Competition browsing, ticket purchasing via Viva Payments
- "My Account" dashboard with ticket history
- AI Chat (Gemini Flash) with live chat escalation
- Admin panel (user/competition/winner management)
- PWA with service worker
- Push notifications for ALL users:
  - Admins: live chat requests
  - Users: chat reply notifications, winner announcements, competition 80% alerts
- Modern floating navbar with glassmorphism
- Bilingual (Romanian/English)
- Free competition "MEGA PREMIU £5.000" with tiered instant prizes
- Robust deployment scripts (deploy_production.sh)
- Terms & Conditions page, FAQ page, Public ticket search

## Completed This Session (March 19, 2026)
- **FIXED: Push Notifications (P0)** - Synced VAPID keys, replaced manual crypto with pywebpush, auto-derive public key at runtime
- **FIXED: Frontend .env** - Preview URL → production URL
- **FIXED: DB_NAME** - zektrix_db → ektrix_db (production)
- **VERIFIED: Live Chat E2E** - All components tested and working
- **NEW: Push notifications for all users** - Chat replies, winner draws, competition 80% alerts
  - Subscribe prompt in LiveChat widget and Dashboard overview
  - `/api/push/status` endpoint to check subscription state
  - `/api/push/subscribe` now open to all authenticated users
  - `notify_user_push()` and `notify_competition_participants_push()` helpers
- **Deployed** both frontend (Hostinger) and backend (Railway)

## Upcoming Tasks
- **P1:** Integrate Facebook Pixel
- **P1:** Terms & Conditions page improvements

## Future Tasks (P2)
- **CRITICAL REFACTOR:** server.py is 5000+ lines - needs routing
- "IDEE BOMBA": Bundle Deals, SMS Marketing, Leaderboard, Referral System

## Key Architecture Notes
- VAPID keys derived at runtime from private key PEM
- PEM file auto-generated from env at startup
- Push subscribe open to all users (role stored in subscription doc)
- Admin notifications filter by role=admin
- Competition alerts sent to participants only
