# Zektrix.UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, admin panel, GBP currency, PWA support, real-time chat, and more.

## Tech Stack
- **Frontend:** React + Tailwind CSS + Shadcn/UI (Hostinger)
- **Backend:** FastAPI + MongoDB (Railway)
- **Payments:** Viva Payments (GBP)
- **Auth:** JWT + Emergent-managed Google Auth
- **Email:** Resend
- **Scheduler:** APScheduler

## Core Features (Implemented)
- User authentication (JWT + Google OAuth)
- Competition management (CRUD, auto-draw, instant prizes)
- Viva Payments integration (GBP) with cancel button support
- Admin panel with analytics, user/competition management
- WebSocket live chat system
- PWA with offline support
- My Account profile editing
- Privacy Policy page
- Google Analytics integration
- Deployment script (deploy.sh)

## Bug Fixes Completed (March 2026)
1. **AUTODRAW vs DRAW badges** - Visual differentiation: green AUTODRAW (instant_win) vs violet DRAW (draw) on all pages
2. **Autodraw filter** - Correctly filters only instant_win competitions
3. **Mașini filter** - Fixed to match `category=auto` from database
4. **Dashboard tabs** - Added missing routes for `/dashboard/locs` and `/dashboard/account`
5. **Free competition limit** - Backend enforces one entry per user
6. **Viva Cancel Button** - Added `cancelUrl` + PaymentCancelPage for customer cancellation
7. **Frontend .env** - Set production backend URL permanently

## Key Architecture
- Backend: Monolithic `server.py` (~4600 lines) - NEEDS REFACTORING
- Frontend: Pages in `src/pages/`, Components in `src/components/`
- Deploy: Always use `/app/deploy.sh` for frontend production builds

## Backlog (Prioritized)
### P0
- User verification of PWA/Responsiveness on iOS/Android

### P1
- Refactor `server.py` into modular routers
- Facebook Pixel integration
- Terms & Conditions page

### P2 - "IDEE BOMBA"
- Bundle Deals
- SMS Marketing
- Leaderboard
- Referral System
