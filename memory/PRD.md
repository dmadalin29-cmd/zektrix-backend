# Zektrix UK - Competition Platform PRD

## Overview
UK's premier online competition platform where users can enter competitions to win exciting prizes. Direct card payments via Viva Payments.

## Core Features (ACTIVE)

### Implemented & Working
- **User Authentication**: Google OAuth + Email/Password
- **Competitions**: Two types - Instant Win (auto-draw at 100%) and Classic Draw (manual draw)
- **Direct Payments**: Viva Payments integration (Visa, Mastercard, Apple Pay, Google Pay)
- **Spot System**: Random spot numbers (loc/locuri), qualification questions, postal entry option
- **Admin Panel**: Full CRUD for competitions, users, spots, winners + TikTok LIVE toggle
- **Dashboard**: User spots, transaction history, referral program
- **Winners Page**: Verified winners display
- **Public Search**: Find spots by username
- **Daily Email Bot**: Sends digest emails twice daily (9:00, 18:00)
- **GDPR Compliance**: Unsubscribe system, compliant email footer
- **PWA Support**: Installable as mobile app
- **Live Chat**: Contact support system
- **Cookie Consent**: GDPR compliant
- **Multi-language**: Romanian (default) and English
- **Health Endpoint**: /api/health for Railway monitoring
- **Live Activity Ticker**: Shows recent activity (real + fake data) on homepage
- **Permanent Competition Bot**: Auto-recreates special competition when completed
- **Progress Bars**: All competitions display progress bars

### REMOVED Features (March 2, 2026)
- ~~Wallet System~~ - Users now pay directly with card for each purchase
- ~~Lucky Wheel~~ - Spin-to-win feature completely removed
- ~~Wallet Deposit~~ - No more wallet top-ups

### KEPT from Wallet System
- /api/wallet/balance - For checking any remaining balance
- /api/wallet/transactions - For transaction history
- /api/wallet/webhook - For Viva payment processing
- /api/wallet/payment-status - For payment verification

## Tech Stack
- **Frontend**: React, TailwindCSS, Shadcn/UI
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB
- **Payments**: Viva Payments (direct card payments)
- **Auth**: Google OAuth + JWT
- **Email**: Resend API
- **Deployment**: Railway (backend), Hostinger (frontend)

## Deployment Structure
```
/app/
├── Dockerfile              # Railway build config
├── requirements.txt        # Python dependencies (root)
├── backend/
│   ├── server.py          # Main backend (~4100 lines)
│   └── .env               # Environment variables
└── frontend/
    ├── src/
    │   ├── lib/axios.js   # Axios interceptor for token expiration
    │   └── ... (React components)
    └── ... (deployed to Hostinger)
```

## Key Endpoints
- `/api/health` - Health check for Railway
- `/api/competitions/*` - Competition CRUD
- `/api/tickets/*` - Spot operations (still named tickets internally)
- `/api/tickets/purchase-viva` - Direct Viva payment
- `/api/admin/*` - Admin operations
- `/api/settings/tiktok-live` - TikTok LIVE status
- `/api/stats` - Site statistics
- `/api/activity/recent` - Recent activity for ticker
- `/api/webhooks/viva` - Payment webhook

## Terminology Change (March 3, 2026)
- **Old**: bilet, bilete, ticket, tickets
- **New**: loc, locuri, spot, spots
- Applied to: All user-facing text, email templates, UI labels

## Changelog

### March 3, 2026 - Terminology Update & Production Deploy
- ✅ Changed all "bilet/ticket" terminology to "loc/spot" across entire app
- ✅ Fixed DashboardPage `Loc` icon import error → `Ticket`
- ✅ Added axios interceptor for token expiration handling
- ✅ Deployed backend to Railway via GitHub push
- ✅ Deployed frontend to Hostinger via SSH/rsync
- ✅ Verified production site at zektrix.uk

### March 2, 2026 - Major Cleanup
- ✅ Removed Lucky Wheel completely (3 endpoints)
- ✅ Removed wallet/deposit endpoint
- ✅ Added /api/health endpoint
- ✅ Fixed Railway deployment with correct Dockerfile
- ✅ Frontend updated on Hostinger (no wallet/lucky wheel UI)
- ✅ FAQ & Terms updated (no wallet references)

## Credentials
- Admin: contact@x67digital.com
- GitHub Repo: dmadalin29-cmd/zektrix-backend
- Production Backend: https://zektrix-backend-production.up.railway.app
- Production Frontend: https://zektrix.uk

## Backlog (Prioritized)
### P0 - Critical
- None currently

### P1 - High Priority
- Full PWA responsiveness review (iOS/Android)
- Performance optimization ("faster than sound")

### P2 - Medium Priority
- Refactor server.py (~4100 lines - technical debt)
- Google Analytics & Facebook Pixel integration
- WebSocket-based live chat (current sends email)

### P3 - Low Priority/Future
- Privacy Policy dedicated page
- Terms dedicated page
- Bundle Deals ("IDEE BOMBA")
- SMS Marketing
- Leaderboard system
- Referral rewards enhancement
