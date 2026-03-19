# Zektrix UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, AI-powered live chat with push notifications for admins, and PWA.

## Tech Stack
- **Frontend:** React (Hostinger - zektrix.uk)
- **Backend:** FastAPI (Railway - zektrix-backend-production.up.railway.app)
- **Database:** MongoDB Atlas (DB: ektrix_db)
- **Payments:** Viva Payments
- **AI Chat:** Gemini Flash via emergentintegrations
- **Push Notifications:** pywebpush + VAPID
- **Auth:** JWT + Google Auth (Emergent-managed)

## Core Features (Implemented)
- JWT & Google Auth
- Competition browsing, ticket purchasing via Viva Payments
- "My Account" dashboard with ticket history
- AI Chat (Gemini Flash) with live chat escalation
- Admin panel (user/competition/winner management)
- PWA with service worker
- Push notifications for admins (live chat alerts)
- Modern floating navbar with glassmorphism
- Bilingual (Romanian/English)
- Free competition "MEGA PREMIU £5.000" with tiered instant prizes
- Robust deployment scripts (deploy_production.sh)
- Terms & Conditions page
- FAQ page
- Public ticket search

## Completed This Session (March 19, 2026)
- **FIXED: Push Notifications (P0)** - Root cause: 3 different VAPID keys that didn't match each other. Solution: generated new synchronized key pair, replaced manual crypto with pywebpush library, auto-derive public key from private key at runtime, cleared stale subscriptions.
- **FIXED: Frontend .env** - Had old preview URL, replaced with production Railway URL
- **FIXED: DB_NAME** - Changed from zektrix_db (dev) to ektrix_db (production)
- **Deployed** both frontend (Hostinger) and backend (Railway)

## Upcoming Tasks (P1)
- Verify Live Chat reliability end-to-end
- Integrate Facebook Pixel
- Add dedicated Terms & Conditions page improvements

## Future Tasks (P2)
- **CRITICAL REFACTOR:** server.py is 5000+ lines monolithic file - needs routing
- "IDEE BOMBA" features:
  - Bundle Deals
  - SMS Marketing
  - Leaderboard
  - Referral System

## Key Architecture Notes
- VAPID keys are derived at runtime from private key PEM (ensures sync)
- PEM file auto-generated from VAPID_PRIVATE_KEY env var at server startup
- deploy_production.sh handles safe frontend deployment
- Railway auto-deploys from GitHub main branch
