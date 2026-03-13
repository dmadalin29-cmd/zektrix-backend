# Zektrix UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform using FastAPI, React, MongoDB. Deployed to Railway (backend) and Hostinger (frontend).

## Architecture
```
/app/
├── Dockerfile              # Root Dockerfile for Railway (uses PORT env var)
├── backend/
│   ├── server.py           # Monolithic FastAPI app (~4200 lines)
│   ├── uploads/            # Uploaded competition images
│   ├── Dockerfile          # Backend-specific Dockerfile
│   ├── Procfile            # Railway Procfile
│   └── .env                # Backend environment variables
└── frontend/
    └── src/
        ├── App.js
        ├── lib/axios.js    # Global Axios interceptor
        ├── context/
        │   ├── AuthContext.js
        │   └── LanguageContext.js
        └── pages/
            ├── AdminPage.js
            ├── CompetitionDetailPage.js
            ├── CompetitionsPage.js
            ├── DashboardPage.js
            ├── HomePage.js
            ├── LoginPage.js
            ├── CartPage.js
            ├── ReferralPage.js
            └── PaymentSuccessPage.js
```

## Key Technical Details
- **Authentication:** JWT + Emergent Google Auth
- **Payments:** Viva Payments (GBP, currencyCode 826)
- **Currency:** GBP (£) across entire platform
- **Terminology:** "loc/locuri" (spot/spots) not "bilet/ticket"
- **Deployment:** Railway (backend) + Hostinger (frontend)
- **Backend URL:** https://zektrix-backend-production.up.railway.app
- **Frontend URL:** https://zektrix.uk
- **Hostinger SSH:** ssh -p 65002 u485600077@82.25.102.184

## Deployment Process
1. Make code changes in /app/frontend/
2. Build: `cd /app/frontend && REACT_APP_BACKEND_URL=https://zektrix-backend-production.up.railway.app yarn build`
3. Verify URL: `grep -o '"https://[^"]*"' /app/frontend/build/static/js/main.*.js | sort -u`
4. Create tar: `cd /app/frontend/build && tar czf /tmp/build.tar.gz .`
5. Upload: `sshpass -p 'Credcada1.' scp -P 65002 /tmp/build.tar.gz u485600077@82.25.102.184:~/build.tar.gz`
6. Deploy: SSH in, backup .htaccess, clean public_html, extract tar, restore .htaccess

## Credentials
- Admin: contact@x67digital.com / Credcada1.
- GitHub Repo: dmadalin29-cmd/zektrix-backend
- Hostinger SSH: u485600077@82.25.102.184:65002 / Credcada1.

## Completed Features
- Core competition platform (create, list, buy spots)
- Viva Payments integration (sole payment method)
- Wallet & Lucky Wheel REMOVED
- Terminology: bilet->loc everywhere
- Modern Login/Register page with Google Auth
- Profile completion step for Google users (phone required)
- "My Account" section in dashboard
- Currency switch RON -> GBP (£) across ALL pages
- Competition image uploads (admin)
- Dynamic competition badges (DRAW/INSTANT WIN)
- Dashboard bugs fixed (API endpoints, navigation)
- Railway deployment stabilization (PORT env var fix)
- Added axios interceptor for token expiration handling
- FAQ & Terms integration
- FREE COMPETITIONS feature (is_free field, /api/tickets/enter-free endpoint)
- Fixed max_locuri/sold_locuri -> max_tickets/sold_tickets (field name mismatch)
- Fixed "1locuri" -> "1 loc" singular/plural in Dashboard
- Dockerfile PORT fix for Railway
- Admin Analytics with real-time data from DB
- PWA with auto-update service worker
- **[2026-03-13] Fixed production deployment - frontend was pointing to wrong backend (free-draw-preview.preview.emergentagent.com instead of zektrix-backend-production.up.railway.app). Rebuilt and deployed to Hostinger.**

## Key API Endpoints
- POST /api/auth/login, /api/auth/register
- PUT /api/auth/profile
- GET /api/competitions, /api/competitions/{id}
- POST /api/admin/competitions (supports is_free flag)
- POST /api/admin/upload-image
- POST /api/tickets/enter-free (free competition entry, 1 per user)
- POST /api/tickets/purchase-viva
- GET /api/stats
- GET /api/activity/recent
- GET /api/settings/tiktok-live

## DB Schema Notes
- competitions: includes `is_free: bool` field
- tickets: includes `is_free_entry: bool` for free entries

## Backlog (Prioritized)
### P0
- Site & PWA Performance Optimization
- Full PWA & Responsiveness audit (iOS + Android)

### P1
- Complete Live Chat (WebSocket-based, currently email-only)
- Refactor server.py (~4200 lines monolith) into routers

### P2
- Google Analytics & Facebook Pixel integration
- Privacy Policy & Terms dedicated pages
- Bundle Deals, SMS Marketing, Leaderboard, Referral System enhancements
