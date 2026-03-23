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

## Backend Architecture
```
/app/backend/
├── server.py          # App orchestrator (~175 lines)
├── config.py          # Shared config (UPLOAD_DIR, JWT, VAPID, etc.)
├── routes/
│   ├── auth.py, competitions.py, wallet.py, subscriptions.py, referral.py
│   ├── admin.py, chat.py, webhooks.py, public.py
│   ├── gamification.py, engagement.py
│   └── marketing.py   # Bundle Deals, Push Campaigns, TikTok Live Draw, Advanced Analytics
```

## Completed Features
- JWT & Google Auth, Competition browsing, Viva Payments
- AI Chat (Gemini Flash), Push notifications, PWA
- Wallet System, Subscription System, Premium Referral System
- Admin panel with real-time notifications
- Gamification Badges, Re-engagement Emails
- Loyalty Points, User Notifications, Reviews, Wheel of Fortune, Exit Intent
- **Bundle Deals** with discount pricing on competition pages
- **Push Campaign Manager** (admin broadcasts to all/active/subscribers)
- **TikTok Live Draw Embed** (live banner with @x67digital link)
- **Advanced Analytics** (KPI dashboard, daily revenue, retention, top spenders)
- **Full bilingual RO/EN support** across entire site (AdminPage, all pages, components)
- **Image Upload Fix** (path mismatch corrected + HEIC/iPhone support added) - Mar 2026

## Upcoming Tasks
- **P1:** TikTok Pixel Integration (when running ads)
- **P2:** SMS Marketing
- **P2:** Refactor AdminPage.js (2300+ lines → smaller sub-components)
