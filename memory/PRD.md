# Zektrix UK - Competition Platform PRD

## Architecture
```
/app/
├── backend/server.py      # FastAPI monolith (~4500 lines)
├── frontend/src/
│   ├── App.js             # Routes
│   ├── components/LiveChat.js  # WebSocket live chat
│   ├── pages/AdminPage.js      # Admin panel (optimized)
│   ├── pages/PrivacyPolicyPage.js  # GDPR Privacy Policy
│   └── pages/*.js
```

## Deploy
- **Backend:** `git push origin main` → Railway auto-deploys
- **Frontend:** Build with `REACT_APP_BACKEND_URL=https://zektrix-backend-production.up.railway.app yarn build`, then tar+SCP+extract to Hostinger
- **Hostinger SSH:** `ssh -p 65002 u485600077@82.25.102.184` (pass: Credcada1.)
- **Admin:** contact@x67digital.com / Credcada1.

## Completed Features (Latest: 2026-03-13)
- Core competition platform, Viva Payments (GBP), Google Auth
- Admin panel with real-time analytics from DB
- Free competitions, PWA with auto-update
- **[NEW] Google Analytics (G-G760C5BPRM)**
- **[NEW] Privacy Policy page (/privacy) - GDPR UK compliant**
- **[NEW] WebSocket Live Chat (real-time user↔admin)**
- **[NEW] Admin chat management: resolve/delete/email reply**
- **[NEW] Admin panel 10x faster (batch DB queries, aggregation pipelines)**
  - admin/tickets: 7.9s → 0.7s
  - admin/analytics: 1.9s → 1.1s
  - admin/chat: 1.6s → 0.6s

## Backlog
### P0
- Full PWA & Responsiveness audit (iOS + Android)
### P1  
- Refactor server.py (~4500 lines) into routers
### P2
- Bundle Deals, SMS Marketing, Leaderboard, Referral System
