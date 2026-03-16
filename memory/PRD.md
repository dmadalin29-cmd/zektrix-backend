# Zektrix.UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, admin panel, GBP currency, PWA support, real-time chat, and more.

## Tech Stack
- **Frontend:** React + Tailwind CSS + Shadcn/UI (Hostinger)
- **Backend:** FastAPI + MongoDB (Railway)
- **Payments:** Viva Payments (GBP)
- **Auth:** JWT + Emergent-managed Google Auth
- **Email:** Resend
- **AI:** Gemini 2.5 Flash via Emergent LLM Key
- **Push:** Web Push API (VAPID)
- **Scheduler:** APScheduler

## Core Features (Implemented)
- User authentication (JWT + Google OAuth)
- Competition management (CRUD, auto-draw, instant prizes)
- Viva Payments integration (GBP) with cancel button
- Admin panel with analytics, user/competition management
- **AI Chatbot** - Gemini Flash, answers questions about Zektrix in Romanian
- **Push Notifications** - Admin receives push + email when user needs live help
- WebSocket live chat with AI-to-live escalation
- PWA with offline support
- My Account profile editing
- Privacy Policy page, Google Analytics

## Latest Session Changes (March 2026)
1. AUTODRAW vs DRAW badge differentiation on all pages
2. Fixed Mașini filter (category=auto match)
3. Fixed Dashboard tabs (missing routes)
4. Viva cancel button + PaymentCancelPage
5. AI Chatbot (Gemini Flash) with escalation to live chat
6. Push notifications (VAPID) + email alerts for admin

## Backlog
### P0
- User verification of PWA/Responsiveness on iOS/Android

### P1
- Refactor `server.py` into modular routers
- Facebook Pixel integration
- Terms & Conditions page

### P2 - "IDEE BOMBA"
- Bundle Deals, SMS Marketing, Leaderboard, Referral System
