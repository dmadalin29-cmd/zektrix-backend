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
- **Email:** Resend API

## Core Features (Implemented)
- JWT & Google Auth
- Competition browsing, ticket purchasing via Viva Payments
- Multi-image gallery for competitions
- AI Chat (Gemini Flash) with live chat escalation
- Admin panel (user/competition/winner management)
- PWA + Push notifications
- Wallet System + Subscription System + Premium Referral System
- Admin Notification Bell with mark-as-read
- Block/Unblock users from admin panel
- **Countdown Timer on competition cards** (March 21, 2026) — shows time remaining until draw_date
- **Gamification Badge System** (March 21, 2026) — 10 achievements: Primul Bilet, Colectionar, Pasionat, Legenda, Castigator, Ambasador, Referral King, High Roller, Explorer, Early Bird
- **Re-engagement Email Bot** (March 21, 2026) — auto-sends emails to users inactive 7+ days, max 1 per 14 days
- **Enhanced Progress Bar** (March 21, 2026) — urgency indicators (>70% HOT, >90% ULTIMELE LOCURI), publicly visible stats on all cards
- Global UI Redesign: Apple-style mesh gradients, glassmorphism, Outfit font, Framer Motion

## Upcoming Tasks
- **P1:** TikTok Pixel Integration
- **P2:** Bundle Deals (ticket packages with discounts)
- **P2:** SMS Marketing
- **P2:** Refactor server.py (~5900 lines -> modular routes)
