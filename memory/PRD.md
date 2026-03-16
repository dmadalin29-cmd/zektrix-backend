# Zektrix.UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, admin panel, GBP currency, PWA support, real-time chat, and more.

## Tech Stack
- **Frontend:** React + Tailwind CSS + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Hosting:** Railway (backend), Hostinger (frontend)
- **Payments:** Viva Payments (GBP)
- **Auth:** JWT + Emergent-managed Google Auth
- **Email:** Resend
- **Scheduler:** APScheduler

## Core Features (Implemented)
- User authentication (JWT + Google OAuth)
- Competition management (CRUD, auto-draw, instant prizes)
- Viva Payments integration (GBP)
- Admin panel with analytics, user/competition management
- WebSocket live chat system
- PWA with offline support
- My Account profile editing
- Privacy Policy page
- Google Analytics integration
- Deployment script (deploy.sh)

## Key Architecture
- Backend: Monolithic `server.py` (~4600 lines) - NEEDS REFACTORING
- Frontend: Pages in `src/pages/`, Components in `src/components/`
- Routes: `/api` prefix for all backend endpoints

## Critical Deployment Note
Always use `/app/deploy.sh` for frontend production deployments to prevent wrong backend URL bug.

## Bug Fixes Completed (March 2026)
1. AUTODRAW badge - Now conditional on `competition_type === 'instant_win'`
2. Autodraw filter - Renamed from "Instant" to "Autodraw", filters correctly
3. Dashboard tabs - Added missing routes for `/dashboard/locs` and `/dashboard/account`
4. Free competition limit - Backend already enforces one entry per user

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
