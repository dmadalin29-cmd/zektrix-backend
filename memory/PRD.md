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
├── server.py          # App orchestrator (~175 lines)
├── config.py          # Environment vars + configuration
├── database.py        # MongoDB connection
├── dependencies.py    # Auth helpers (JWT, get_current_user)
├── helpers.py         # Shared utilities (push wrappers, ticket generator)
├── models.py          # Pydantic models
├── email_service.py   # Email functions
├── push_service.py    # Push notification helpers
├── routes/
│   ├── auth.py         # Auth + password reset
│   ├── competitions.py # Competitions + tickets
│   ├── wallet.py       # Wallet + admin wallet
│   ├── subscriptions.py# Subscriptions
│   ├── referral.py     # Referral system
│   ├── admin.py        # Admin CRUD + stats + settings
│   ├── chat.py         # Chat AI + push + WebSockets
│   ├── webhooks.py     # Viva webhooks + payments
│   ├── public.py       # Public routes + uploads + email mgmt
│   ├── gamification.py # Badge system
│   ├── engagement.py   # Loyalty, Notifications, Reviews, Wheel, Exit Intent
│   └── marketing.py    # Bundle Deals, Push Campaigns, TikTok Live Draw, Advanced Analytics
├── services/
│   └── bots.py         # Background tasks: auto-bot, email, subs, re-engagement
```

## Core Features (All Implemented)
- JWT & Google Auth, Competition browsing, Viva Payments
- AI Chat (Gemini Flash), Push notifications, PWA
- Wallet System, Subscription System, Premium Referral System
- Admin panel with real-time notifications (mark-as-read)
- Countdown Timer, Gamification Badges, Re-engagement Emails
- Enhanced Progress Bar with urgency indicators
- Global UI: mesh gradients, glassmorphism, Outfit font

### Engagement Features (Implemented March 21, 2026)
- **Loyalty Points System**: 10pts/£1, tier-based multipliers (Bronze/Silver/Gold/Diamond), redeem for wallet credit
- **User In-App Notifications**: Bell icon in navbar, real-time unread badges, dropdown with notification list
- **Reviews/Testimonials**: Winners can review, admin approval system, public display on homepage
- **Wheel of Fortune**: One spin per user, 8 prizes (discounts, credits, points), Canvas-based animation
- **Exit Intent Popup**: 15% discount on exit, 24h validity, one-time per user

### Marketing Features (Implemented March 22, 2026)
- **Bundle Deals**: Admin creates ticket packages with % discounts (e.g., 3x 10% OFF). Displayed on paid competition pages with visual pricing comparison
- **Push Campaign Manager**: Admin broadcasts push notifications to all/active/subscriber audiences. Includes audience stats, send form, and campaign history
- **TikTok Live Draw Embed**: When admin enables live draw, a prominent red banner with TikTok link appears on the competition page
- **Advanced Analytics**: KPI dashboard (conversion rate, AOV, retention rate, total revenue), daily revenue bar chart, retention stats, top spenders leaderboard, revenue breakdown by transaction type

## Upcoming Tasks
- **P1:** TikTok Pixel Integration (when running ads)
- **P2:** Bundle Deals with Viva Payment integration (bundle-specific checkout)
- **P2:** SMS Marketing
