# Zektrix.UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, admin panel, GBP currency, PWA support, real-time chat, and more.

## Tech Stack
- **Frontend:** React + Tailwind CSS + Shadcn/UI (Hostinger - zektrix.uk)
- **Backend:** FastAPI + MongoDB Atlas (Railway - zektrix-backend-production.up.railway.app)
- **Payments:** Viva Payments (GBP)
- **Auth:** JWT + Emergent-managed Google Auth
- **Email:** Resend
- **AI:** Gemini Flash via Emergent LLM Key
- **Push:** Web Push API (VAPID) with pywebpush
- **Scheduler:** APScheduler

## Core Features (Implemented)
- User authentication (JWT + Google OAuth via Emergent Auth)
- Competition management (CRUD, auto-draw, instant prizes)
- Viva Payments integration (GBP) with cancel button
- Admin panel with analytics, user/competition management
- AI Chatbot (Gemini Flash) with escalation to live agent
- Push Notifications (VAPID) for admin live chat alerts
- WebSocket live chat + REST API fallback + polling
- PWA with offline support
- My Account profile editing

## Session Changes (March 16, 2026)

### Bug Fixes Applied
1. **Chat Duplicate Messages** - LiveChat.js: loadHistory REPLACES messages, historyLoadedRef prevents double-loading, WebSocket dedup by message ID
2. **Live Chat Not Working** - Added REST API fallback (POST /chat/message) when WebSocket unavailable. User-side polling every 5s, admin-side polling every 8s for new messages
3. **Google Auth Callback** - Added window.location.hash fallback, better error logging, Romanian UI text
4. **WebSocket Session Token** - verify_ws_token now supports both JWT and session tokens for Google Auth users
5. **Push Notifications** - Infrastructure verified, VAPID keys match, pywebpush working

### Deployments
- Frontend deployed to Hostinger with production backend URL
- Backend pushed to GitHub → Railway auto-deploy
- All .env files use production URLs

## Important Notes
- Preview and Production may use DIFFERENT MongoDB databases
- WebSocket connections may not work through Kubernetes ingress (preview) but work on Railway (production)
- REST API polling fallback ensures chat works without WebSocket

## Backlog
### P0
- User verification of all fixes on production site

### P1
- Refactor server.py into modular routers (4800+ lines)
- Facebook Pixel integration
- Terms & Conditions page

### P2 - "IDEE BOMBA"
- Bundle Deals, SMS Marketing, Leaderboard, Referral System
