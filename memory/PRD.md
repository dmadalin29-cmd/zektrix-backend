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

## Credentials
- Admin: contact@x67digital.com
- GitHub Repo: dmadalin29-cmd/zektrix-backend

## Completed Features
- ✅ Core competition platform (create, list, buy spots)
- ✅ Viva Payments integration (sole payment method)
- ✅ Wallet & Lucky Wheel REMOVED
- ✅ Terminology: bilet→loc everywhere
- ✅ Modern Login/Register page with Google Auth
- ✅ Profile completion step for Google users (phone required)
- ✅ "My Account" section in dashboard
- ✅ Currency switch RON → GBP (£) across ALL pages
- ✅ Competition image uploads (admin)
- ✅ Dynamic competition badges (DRAW/INSTANT WIN)
- ✅ Dashboard bugs fixed (API endpoints, navigation)
- ✅ Railway deployment stabilization (PORT env var fix)
- ✅ Added axios interceptor for token expiration handling
- ✅ FAQ & Terms integration
- ✅ FREE COMPETITIONS feature (is_free field, /api/tickets/enter-free endpoint)
- ✅ Fixed max_locuri/sold_locuri → max_tickets/sold_tickets (field name mismatch)
- ✅ Fixed "1locuri" → "1 loc" singular/plural in Dashboard
- ✅ Dockerfile PORT fix for Railway (${PORT:-8080})

## Key API Endpoints
- POST /api/auth/login, /api/auth/register
- PUT /api/auth/profile
- GET /api/competitions, /api/competitions/{id}
- POST /api/admin/competitions (supports is_free flag)
- POST /api/admin/upload-image
- POST /api/tickets/enter-free (free competition entry, 1 per user)
- POST /api/tickets/purchase-viva

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
