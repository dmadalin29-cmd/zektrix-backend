# Zektrix UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform using FastAPI, React, MongoDB. Deployed to Railway (backend) and Hostinger (frontend).

## Architecture
```
/app/
├── Dockerfile              # Root Dockerfile for Railway (uses PORT env var)
├── backend/
│   ├── server.py           # Monolithic FastAPI app (~4400 lines)
│   ├── uploads/            # Uploaded competition images
│   ├── tests/              # Backend test files
│   └── .env                # Backend environment variables
└── frontend/
    └── src/
        ├── App.js          # Routes: /, /competitions, /dashboard, /admin, /privacy, /terms, etc.
        ├── components/
        │   ├── LiveChat.js # WebSocket-based live chat widget
        │   ├── Footer.js   # Footer with Privacy Policy link
        │   └── Navbar.js
        └── pages/
            ├── AdminPage.js            # Admin panel with WS chat
            ├── CompetitionDetailPage.js
            ├── CompetitionsPage.js
            ├── DashboardPage.js
            ├── HomePage.js
            ├── LoginPage.js
            ├── PrivacyPolicyPage.js     # NEW - GDPR Privacy Policy
            └── PaymentSuccessPage.js
```

## Deployment Info
- **Backend:** Railway (auto-deploys from GitHub push)
- **Frontend:** Hostinger via SSH
- **Backend URL:** https://zektrix-backend-production.up.railway.app
- **Frontend URL:** https://zektrix.uk
- **Hostinger SSH:** ssh -p 65002 u485600077@82.25.102.184 (password: Credcada1.)
- **GitHub:** dmadalin29-cmd/zektrix-backend

## Deploy Process
1. Build: `cd /app/frontend && REACT_APP_BACKEND_URL=https://zektrix-backend-production.up.railway.app yarn build`
2. Tar: `cd /app/frontend/build && tar czf /tmp/build.tar.gz .`
3. Upload: `sshpass -p 'Credcada1.' scp -P 65002 /tmp/build.tar.gz u485600077@82.25.102.184:~/build.tar.gz`
4. Deploy: SSH in, backup .htaccess, clean public_html, extract tar, restore .htaccess
5. Backend: `git push origin main` → Railway auto-deploys

## Credentials
- Admin: contact@x67digital.com / Credcada1.

## Completed Features
- Core competition platform (create, list, buy spots)
- Viva Payments integration (GBP)
- Modern Login/Register with Google Auth
- "My Account" section in dashboard
- Currency: GBP (£) across all pages
- Competition image uploads (admin)
- Free competitions feature (is_free flag)
- Admin Analytics with real-time DB data
- PWA with auto-update service worker
- Axios interceptor for token expiration
- **[2026-03-13] Fixed production deployment - frontend pointing to wrong backend**
- **[2026-03-13] Google Analytics (G-G760C5BPRM) integrated**
- **[2026-03-13] Privacy Policy page (GDPR UK compliant) at /privacy**
- **[2026-03-13] WebSocket Live Chat - real-time user↔admin communication**
- **[2026-03-13] Admin panel WebSocket integration for live chat notifications**

## Key API Endpoints
- POST /api/auth/login, /api/auth/register
- GET /api/competitions, /api/competitions/{id}
- POST /api/admin/competitions
- POST /api/tickets/enter-free, /api/tickets/purchase-viva
- GET /api/chat/faq, /api/chat/history
- POST /api/chat/message
- GET /api/admin/chat/messages
- WebSocket: /ws/chat/user?token=TOKEN, /ws/chat/admin?token=TOKEN

## Backlog (Prioritized)
### P0
- Site & PWA Performance Optimization (Lighthouse audit)
- Full PWA & Responsiveness audit (iOS + Android)

### P1
- Refactor server.py (~4400 lines monolith) into routers

### P2
- Bundle Deals, SMS Marketing, Leaderboard, Referral System
