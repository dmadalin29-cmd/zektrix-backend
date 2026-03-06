# Zektrix UK - Competition Platform PRD

## Overview
UK's premier online competition platform where users can enter competitions to win exciting prizes. Direct card payments via Viva Payments.

## Core Features (ACTIVE)

### Implemented & Working
- **User Authentication**: Google OAuth + Email/Password
- **Competitions**: Two types - Instant Win (auto-draw at 100%) and Classic Draw (manual draw)
- **Direct Payments**: Viva Payments integration (Visa, Mastercard, Apple Pay, Google Pay)
- **Ticket System**: Random ticket numbers, qualification questions, postal entry option
- **Admin Panel**: Full CRUD for competitions, users, tickets, winners
- **Dashboard**: User tickets, transaction history, referral program
- **Winners Page**: Verified winners display
- **Public Search**: Find tickets by username
- **Daily Email Bot**: Sends digest emails twice daily (9:00, 18:00)
- **GDPR Compliance**: Unsubscribe system, compliant email footer
- **PWA Support**: Installable as mobile app
- **Live Chat**: Contact support system
- **Cookie Consent**: GDPR compliant
- **Multi-language**: Romanian (default) and English
- **Health Endpoint**: /api/health for Railway monitoring

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
│   ├── server.py          # Main backend (3941 lines)
│   └── requirements.txt   # Backend dependencies
└── frontend/
    └── ... (deployed to Hostinger)
```

## Key Endpoints
- `/api/health` - Health check for Railway
- `/api/competitions/*` - Competition CRUD
- `/api/tickets/*` - Ticket operations
- `/api/tickets/purchase-viva` - Direct Viva payment
- `/api/admin/*` - Admin operations
- `/api/webhooks/viva` - Payment webhook

## Changelog

### March 2, 2026 - Major Cleanup
- ✅ Removed Lucky Wheel completely (3 endpoints)
- ✅ Removed wallet/deposit endpoint
- ✅ Added /api/health endpoint
- ✅ Fixed Railway deployment with correct Dockerfile
- ✅ Frontend updated on Hostinger (no wallet/lucky wheel UI)
- ✅ FAQ & Terms updated (no wallet references)

## Credentials
- Admin: contact@x67digital.com / Credcada1.
- Hostinger SSH: ssh -p 65002 u485600077@82.25.102.184 / Credcada1.
- GitHub: dmadalin29-cmd/zektrix-backend

## Backlog
- P1: Full PWA responsiveness review
- P2: Refactor server.py (3941 lines - still large)
- P2: Google Analytics & Facebook Pixel
- P3: Privacy Policy page
