# Zektrix UK - Competition Platform

## 🎯 Description
Modern competition platform where users can win amazing prizes! Built with FastAPI backend, React frontend, and MongoDB.

## 🚀 Features
- User authentication (JWT + Google OAuth)
- Competition system (Instant Win + Classic Draw)
- Wallet system with Viva Payments
- Real-time updates with WebSocket
- AI-generated descriptions and qualification questions
- PWA support (iOS & Android)
- Referral system with £5 bonus
- Multi-language (Romanian default + English)

## 🛠️ Tech Stack
- **Backend**: FastAPI, Motor (MongoDB), Resend, emergentintegrations
- **Frontend**: React, Tailwind CSS, Shadcn UI
- **Database**: MongoDB Atlas
- **Payments**: Viva Payments (Apple Pay, Google Pay supported)
- **AI**: OpenAI GPT-5.2 via emergentintegrations

## 📦 Installation

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Configure .env file
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend Setup
```bash
cd frontend
yarn install
# Configure .env file
yarn start
```

## 🔐 Environment Variables

### Backend (.env)
```env
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=zektrix_db
CORS_ORIGINS=*
JWT_SECRET=your_super_secret_jwt_key
VIVA_CLIENT_ID=your_viva_client_id
VIVA_CLIENT_SECRET=your_viva_client_secret
VIVA_API_URL=https://api.vivapayments.com
VIVA_CHECKOUT_URL=https://www.vivapayments.com/web/checkout
RESEND_API_KEY=your_resend_api_key
EMERGENT_LLM_KEY=your_emergent_llm_key
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://your-backend-url.com
```

## 🚀 Deploy to Railway

1. Create two services: `backend` and `frontend`
2. Set environment variables for each
3. Backend: Set start command to `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Frontend: Build command `yarn build`, start with `serve -s build`

## 🚀 Deploy to Hostinger

### Backend (VPS/Cloud)
1. Upload backend folder
2. Install Python 3.11+
3. Create venv: `python -m venv venv && source venv/bin/activate`
4. Install deps: `pip install -r requirements.txt`
5. Use Gunicorn: `gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001`
6. Configure reverse proxy (Nginx)

### Frontend (Static Hosting)
1. Build: `yarn build`
2. Upload `build` folder to public_html

## 📱 PWA
The app is PWA-ready! Users can install it on:
- iOS: Safari → Share → Add to Home Screen
- Android: Chrome → Menu → Install App

## 📝 License
MIT License
