# Zektrix UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, AI-powered live chat, push notifications, and PWA.

## Tech Stack
- **Frontend:** React (Hostinger - zektrix.uk)
- **Backend:** FastAPI modular (Railway)
- **Database:** MongoDB Atlas (DB: ektrix_db)
- **Payments:** Viva Payments
- **AI Chat:** Gemini Flash via emergentintegrations
- **Push Notifications:** pywebpush + VAPID
- **Auth:** JWT + Google Auth (Emergent-managed)
- **Email:** Resend API

## Backend Architecture (Refactored March 21, 2026)
```
/app/backend/
├── server.py          # App orchestrator (165 lines)
├── config.py          # Environment vars + configuration
├── database.py        # MongoDB connection
├── dependencies.py    # Auth helpers (JWT, get_current_user)
├── helpers.py         # Shared utilities (push wrappers, ticket generator)
├── models.py          # Pydantic models
├── email_service.py   # Email functions
├── push_service.py    # Push notification helpers
├── routes/
│   ├── auth.py         # Auth + password reset (241 lines)
│   ├── competitions.py # Competitions + tickets (754 lines)
│   ├── wallet.py       # Wallet + admin wallet (588 lines)
│   ├── subscriptions.py# Subscriptions (416 lines)
│   ├── referral.py     # Referral system (230 lines)
│   ├── admin.py        # Admin CRUD + stats + settings (1002 lines)
│   ├── chat.py         # Chat AI + push + WebSockets (904 lines)
│   ├── webhooks.py     # Viva webhooks + payments (314 lines)
│   ├── public.py       # Public routes + uploads + email mgmt (191 lines)
│   └── gamification.py # Badge system (108 lines)
├── services/
│   └── bots.py         # Background tasks: auto-bot, email, subs, re-engagement (1110 lines)
```

## Core Features (All Implemented)
- JWT & Google Auth, Competition browsing, Viva Payments
- AI Chat (Gemini Flash), Push notifications, PWA
- Wallet System, Subscription System, Premium Referral System
- Admin panel with real-time notifications (mark-as-read)
- Countdown Timer, Gamification Badges, Re-engagement Emails
- Enhanced Progress Bar with urgency indicators
- Global UI: mesh gradients, glassmorphism, Outfit font, Framer Motion

## Upcoming Tasks
- **P1:** TikTok Pixel Integration
- **P2:** Bundle Deals (ticket packages with discounts)
- **P2:** SMS Marketing
