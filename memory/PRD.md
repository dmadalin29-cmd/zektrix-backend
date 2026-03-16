# Zektrix.UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, admin panel, GBP currency, PWA support, real-time chat, and more.

## Tech Stack
- **Frontend:** React + Tailwind CSS + Shadcn/UI (Hostinger - zektrix.uk)
- **Backend:** FastAPI + MongoDB Atlas (Railway - zektrix-backend-production.up.railway.app)
- **Payments:** Viva Payments (GBP)
- **Auth:** JWT + Emergent-managed Google Auth
- **Email:** Resend
- **AI:** Gemini 2.5 Flash via Emergent LLM Key
- **Push:** Web Push API (VAPID) with pywebpush
- **Scheduler:** APScheduler

## Core Features (Implemented)
- User authentication (JWT + Google OAuth via Emergent Auth)
- Competition management (CRUD, auto-draw, instant prizes)
- Viva Payments integration (GBP) with cancel button
- Admin panel with analytics, user/competition management
- AI Chatbot (Gemini Flash) with escalation to live agent
- Push Notifications (VAPID) for admin live chat alerts
- WebSocket live chat with AI-to-live escalation
- PWA with offline support
- My Account profile editing
- Privacy Policy page, Google Analytics

## Session Changes (March 16, 2026)

### Bug Fixes
1. **Chat Duplicate Messages** - Fixed `LiveChat.js`: `loadHistory` now REPLACES messages instead of appending. Added `historyLoadedRef` to prevent double-loading. WebSocket dedup by message ID.
2. **Google Auth Callback** - Improved `AuthCallback.js`: Added `window.location.hash` fallback, better error logging, Romanian UI text.
3. **Push Notifications** - Infrastructure verified: VAPID keys match between PEM and env, pywebpush installed, admin subscription flow works.

### Deployment
- Frontend deployed to Hostinger with production backend URL verified in bundle
- Production backend (Railway) healthy and VAPID key endpoint working

## Important Notes
- Preview and Production use DIFFERENT MongoDB databases (different user counts)
- Admin credentials on preview: admin@zektrix.uk / admin123
- Production admin credentials differ - user manages these on Railway

## Backlog
### P0
- User verification of Google Auth on production (zektrix.uk)
- User verification of Push Notifications (admin needs to subscribe via Settings > Activează Notificări Push)
- User verification of Chat deduplication fix

### P1
- Refactor `server.py` into modular routers (4800+ lines)
- Facebook Pixel integration
- Terms & Conditions page

### P2 - "IDEE BOMBA"
- Bundle Deals, SMS Marketing, Leaderboard, Referral System
