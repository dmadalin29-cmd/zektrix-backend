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
├── server.py          # Main FastAPI app + routes (~5700+ lines)
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
- Push notifications for ALL users
- Personalized email alerts at 70%/80%/90% competition milestones
- Modern daily digest emails
- Social sharing (WhatsApp, Facebook, Twitter, copy link)
- Modern floating navbar with glassmorphism
- Bilingual (Romanian/English)
- Free competition "MEGA PREMIU £5.000" with tiered instant prizes
- **Wallet System**: Full deposit/withdraw/history/bonus system
- **Subscription System**: 3 fixed plans with auto ticket distribution
- **Premium Referral System**: £3 referrer / £2 referred on first purchase, customizable code, leaderboard
- **Admin Notification Bell** (FIXED March 21, 2026): Mark-as-read functionality
  - Badge shows unread count, disappears after opening dropdown
  - Backend: POST /api/admin/notifications/read saves timestamp
  - GET /api/admin/notifications returns unread_count based on read_at
- Featured Competition customizable from Admin Settings
- **Global UI Redesign**: Apple-style mesh gradients, glassmorphism, Outfit font, Framer Motion animations

## Upcoming Tasks
- **P1:** TikTok Pixel Integration (when user starts running ads)
- **P2:** Countdown Timer on competitions
- **P2:** Bundle Deals (ticket packages with discounts)
- **P2:** SMS Marketing
- **P2:** Refactor `server.py` (~5700+ lines -> modular routes)
