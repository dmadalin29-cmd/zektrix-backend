# Zektrix.UK - Competition Platform PRD

## Original Problem Statement
Full-stack competition platform with Viva Payments, modern UI, AI-powered live chat with push notifications for admins, and PWA.

## Core Architecture
- **Frontend**: React (CRA) deployed on Hostinger (zektrix.uk)
- **Backend**: FastAPI deployed on Railway (auto-deploy from GitHub main branch)
- **Database**: MongoDB Atlas (production DB: `ektrix_db`, preview DB: `zektrix_db`)
- **PWA**: Service worker with network-first caching strategy

## What's Been Implemented

### Authentication
- JWT + Google Auth (Emergent-managed)
- Admin and user roles

### Competitions
- Browse, search, filter competitions
- Ticket purchase via Viva Payments
- Free competition entry
- Instant prizes at percentage thresholds (auto-awarded to different users)
- Auto-draw when max tickets reached (both paid and free entries)
- Flash sales

### User Dashboard
- My Tickets/Locs with ticket numbers
- Transaction history
- Profile management

### AI Chat & Live Chat
- Gemini Flash AI chatbot for initial queries
- Escalation to live chat with admin
- REST API fallback + polling for reliability
- Push notifications to admin for new chat requests
- Email notifications to admin

### Admin Panel
- Competition CRUD
- User management
- Live chat interface
- Push notification subscription + test button
- Analytics dashboard

### Push Notifications
- VAPID key-based web push (pywebpush)
- Real browser push subscription via pushManager
- Test endpoint: POST /api/push/test
- Auto-cleanup of expired subscriptions

### Deployment
- `deploy_production.sh` script: GitHub push + Hostinger clean deploy
- Service worker cache busting with versioning
- Production URL verification in build

### UI/UX
- Floating ultra-modern navbar with Lucide icons, glassmorphism
- Properly centered dialog/modal using flexbox (works on iOS PWA, Android, Desktop)
- Dark theme with violet/orange accents

## Key API Endpoints
- POST /api/push/vapid-key - Get VAPID public key
- POST /api/push/subscribe - Subscribe to push (admin only)
- POST /api/push/test - Send test push notification
- POST /api/chat/message - REST fallback for chat messages
- POST /api/chat/escalate - Escalate AI chat to live
- POST /api/chat/ai - AI chatbot endpoint

## 3rd Party Integrations
- Viva Payments (payment processing)
- Emergent Google Auth
- Resend (email)
- Gemini Flash via emergentintegrations (AI chat)
- pywebpush (push notifications)
- apscheduler (scheduled tasks)

## Prioritized Backlog

### P0 (Critical)
- User must re-subscribe to push notifications from admin panel
- Verify push notifications work end-to-end

### P1 (Important)
- Verify live chat reliability on production
- Refactor server.py (4800+ lines) into modules

### P2 (Nice to have)
- Facebook Pixel integration
- Terms & Conditions page

### P3 (Future - IDEE BOMBA)
- Bundle Deals
- SMS Marketing
- Leaderboard
- Referral System
