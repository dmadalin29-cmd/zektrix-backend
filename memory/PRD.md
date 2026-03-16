# Zektrix UK - Competition Platform PRD

## Architecture
- **Backend:** FastAPI + MongoDB on Railway
- **Frontend:** React on Hostinger  
- **Backend URL:** https://zektrix-backend-production.up.railway.app
- **Frontend URL:** https://zektrix.uk

## Completed Features (2026-03-16)
- Core platform, Viva Payments (GBP currencyCode 826), Google Auth
- Admin panel (10x optimized), real-time analytics
- Free competitions, PWA with auto-update
- Google Analytics (G-G760C5BPRM), Privacy Policy (/privacy)
- WebSocket Live Chat, Admin chat management
- User profile editing (Contul Meu)
- Instant Prizes (up to 10 per competition, auto-awarded at % thresholds)
- **[2026-03-16] PWA Optimization Complete:**
  - 13 optimized icons (72-512px, iOS + Android)
  - Service Worker v5: stratified caching (static/images/HTML)
  - iOS safe areas, standalone mode adjustments
  - CSS: overscroll-behavior, reduced motion, input zoom fix
  - Manifest: portrait orientation, maskable icons, categories

## Backlog
### P1
- Refactor server.py (~4600 lines) into routers
### P2
- Bundle Deals, SMS Marketing, Leaderboard, Referral System
