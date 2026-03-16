# Zektrix UK - Competition Platform PRD

## Architecture
- **Backend:** FastAPI + MongoDB on Railway (auto-deploy from GitHub)
- **Frontend:** React on Hostinger (manual deploy via SSH)
- **Backend URL:** https://zektrix-backend-production.up.railway.app
- **Frontend URL:** https://zektrix.uk
- **Hostinger SSH:** ssh -p 65002 u485600077@82.25.102.184

## Deploy Process
1. Build: `cd /app/frontend && REACT_APP_BACKEND_URL=https://zektrix-backend-production.up.railway.app yarn build`
2. `.env.production.local` has highest priority and overrides platform's .env
3. Tar + SCP + Extract on Hostinger
4. Backend: `git push origin main` → Railway auto-deploys

## Credentials
- Admin: contact@x67digital.com / Credcada1.

## Completed Features (Latest: 2026-03-13)
- Core competition platform, Viva Payments (GBP), Google Auth
- Admin panel with real-time analytics from DB (10x optimized)
- Free competitions feature
- PWA with auto-update service worker
- Google Analytics (G-G760C5BPRM)
- Privacy Policy page (/privacy) - GDPR UK compliant
- WebSocket Live Chat (user↔admin real-time)
- Admin chat management: resolve/delete/email reply/filter by status
- **User profile editing** (Contul Meu tab in Dashboard)
- **Instant Prizes** - up to 10 prizes per competition with % thresholds
  - Auto-awards when sold tickets reach threshold
  - Random selection among ticket holders
  - Email notification to winners
  - WebSocket broadcast of award events

## Key API Endpoints
- PUT /api/auth/profile - User self-update profile
- POST /api/admin/competitions - Create with instant_prizes array
- PUT /api/admin/chat/{id}/status - Mark resolved
- DELETE /api/admin/chat/{id} - Delete conversation
- POST /api/admin/chat/reply-email - Reply via email

## Testing
- iteration_7.json: All passed (GA4, Privacy, Chat)
- iteration_8.json: All 27/27 passed (Profile edit, Instant prizes, Full site)

## Backlog
### P0
- Full PWA & Responsiveness audit (iOS + Android)
### P1
- Refactor server.py (~4600 lines) into routers
### P2
- Bundle Deals, SMS Marketing, Leaderboard, Referral System
