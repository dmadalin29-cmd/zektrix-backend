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

## Tech Stack
- **Frontend**: React, TailwindCSS, Shadcn/UI
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB Atlas
- **Payments**: Viva Payments (direct card payments)
- **Auth**: Google OAuth + JWT
- **Email**: Resend API

## Bug Fixes Applied (March 6, 2026)

### Python Backend (server.py)
1. ✅ Removed duplicate `AdminUserUpdate` class (lines 273-276)
2. ✅ Fixed undefined function `draw_competition_winner` → changed to `auto_draw_winner`
3. ✅ Fixed 3 f-strings without placeholders
4. ✅ Removed duplicate `health_check` function
5. ✅ All lint errors resolved

### Frontend (React/JavaScript)
- ✅ No ESLint errors found - code is clean

## Deployment Notes
- MongoDB URL: mongodb+srv://X67digital:***@cluster0.eqecncg.mongodb.net
- Backend runs on Railway (https://zektrix-backend-production.up.railway.app)
- Frontend hosted on Hostinger

## Backlog
- P1: Full PWA responsiveness review
- P2: Google Analytics & Facebook Pixel
- P3: Privacy Policy page
