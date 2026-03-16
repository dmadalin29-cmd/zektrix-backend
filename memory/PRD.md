# Zektrix UK - Competition Platform PRD

## Architecture
- **Backend:** FastAPI + MongoDB on Railway (auto-deploy from GitHub)
- **Frontend:** React on Hostinger (manual deploy via SSH)
- **Backend URL:** https://zektrix-backend-production.up.railway.app
- **Frontend URL:** https://zektrix.uk
- **Hostinger SSH:** ssh -p 65002 u485600077@82.25.102.184
- **Deploy:** .env.production.local overrides platform's .env during builds

## Credentials
- Admin: contact@x67digital.com / Credcada1.

## Completed Features (Latest: 2026-03-16)
- Core competition platform, Viva Payments (GBP, currencyCode 826), Google Auth
- Admin panel with real-time analytics (10x optimized)
- Free competitions, PWA with auto-update
- Google Analytics (G-G760C5BPRM)
- Privacy Policy (/privacy) - UK GDPR compliant
- WebSocket Live Chat (user↔admin real-time)
- Admin chat management: resolve/delete/email reply/filter
- User profile editing (Contul Meu tab)
- **Instant Prizes** - up to 10 per competition, auto-awarded at % thresholds
- **[2026-03-16] Fixed Viva Payments currency from RON to GBP (currencyCode: 826)**
- **[2026-03-16] Fixed competition creation modal positioning**
- **[2026-03-16] Removed all remaining RON references**

## Testing
- iteration_7.json: All passed
- iteration_8.json: All 27/27 passed

## Backlog
### P0
- Full PWA & Responsiveness audit (iOS + Android)
### P1
- Refactor server.py (~4600 lines) into routers
### P2
- Bundle Deals, SMS Marketing, Leaderboard, Referral System
