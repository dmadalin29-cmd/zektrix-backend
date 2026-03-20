# -*- coding: utf-8 -*-
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, Query, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles

# Import models from separate module
try:
    from models import (
        UserCreate, UserLogin, UserResponse, QualificationQuestion, PostalEntry,
        CompetitionCreate, CompetitionUpdate, CompetitionResponse,
        TicketPurchase, CartItem, CartPurchase, TicketResponse,
        WalletDeposit, TransactionResponse, WinnerCreate, WinnerResponse,
        AdminUserUpdate, TicketSearchResult, ReferralCreate, ReferralResponse,
        AnalyticsResponse, PushSubscription, NotificationPreferences,
        SpinResult, FlashSaleCreate, ChatMessage, PasswordResetRequest,
        PasswordResetConfirm, ProfileUpdate, ChatReplyModel
    )
    from email_service import (
        send_winner_notification_email, send_welcome_email,
        send_password_reset_email, send_competition_75_percent_email
    )
    from push_service import (
        send_web_push, notify_user_push as _notify_user_push,
        notify_competition_participants_push as _notify_comp_push,
        notify_admins_push as _notify_admins_push
    )
except ImportError:
    from backend.models import (
        UserCreate, UserLogin, UserResponse, QualificationQuestion, PostalEntry,
        CompetitionCreate, CompetitionUpdate, CompetitionResponse,
        TicketPurchase, CartItem, CartPurchase, TicketResponse,
        WalletDeposit, TransactionResponse, WinnerCreate, WinnerResponse,
        AdminUserUpdate, TicketSearchResult, ReferralCreate, ReferralResponse,
        AnalyticsResponse, PushSubscription, NotificationPreferences,
        SpinResult, FlashSaleCreate, ChatMessage, PasswordResetRequest,
        PasswordResetConfirm, ProfileUpdate, ChatReplyModel
    )
    from backend.email_service import (
        send_winner_notification_email, send_welcome_email,
        send_password_reset_email, send_competition_75_percent_email
    )
    from backend.push_service import (
        send_web_push, notify_user_push as _notify_user_push,
        notify_competition_participants_push as _notify_comp_push,
        notify_admins_push as _notify_admins_push
    )
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import subprocess
import sys
import json
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import random
import httpx
import base64
from passlib.context import CryptContext
import jwt
import resend
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback_secret')

# AI Config
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Viva Payments Config
VIVA_CLIENT_ID = os.environ.get('VIVA_CLIENT_ID', '')
VIVA_CLIENT_SECRET = os.environ.get('VIVA_CLIENT_SECRET', '')
VIVA_API_URL = os.environ.get('VIVA_API_URL', 'https://api.vivapayments.com')
# IMPORTANT: Checkout URL must be www.vivapayments.com NOT api.vivapayments.com
VIVA_CHECKOUT_URL = 'https://www.vivapayments.com/web/checkout'  # Hardcoded to prevent misconfiguration
VIVA_SOURCE_CODE = os.environ.get('VIVA_SOURCE_CODE', '9806')  # Terminal/Source code
VIVA_WEBHOOK_KEY = os.environ.get('VIVA_WEBHOOK_KEY', '475FFE73819D67134BBB2D6690A9023714C14E2E')  # Verification key from Viva

# Resend Email Config
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# VAPID Push Notification Config
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '').replace('\\n', '\n')
VAPID_MAILTO = os.environ.get('VAPID_MAILTO', 'mailto:support@zektrix.uk')

# Write VAPID PEM file from env variable
vapid_pem_path = os.path.join(os.path.dirname(__file__), "vapid_private.pem")
if VAPID_PRIVATE_KEY and VAPID_PRIVATE_KEY.startswith('-----BEGIN'):
    with open(vapid_pem_path, 'w') as f:
        f.write(VAPID_PRIVATE_KEY.strip() + '\n')

# Derive VAPID public key from private key (ensures they always match)
VAPID_PUBLIC_KEY = ''
if os.path.exists(vapid_pem_path):
    try:
        from cryptography.hazmat.primitives import serialization as _ser
        with open(vapid_pem_path, 'rb') as f:
            _pk = _ser.load_pem_private_key(f.read(), password=None)
        VAPID_PUBLIC_KEY = base64.urlsafe_b64encode(
            _pk.public_key().public_bytes(_ser.Encoding.X962, _ser.PublicFormat.UncompressedPoint)
        ).rstrip(b'=').decode()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to derive VAPID public key: {e}")
        VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')

# Helper function to generate random unique ticket numbers
async def generate_random_ticket_number(competition_id: str, max_tickets: int) -> int:
    """Generate a random ticket number that hasn't been used yet for this competition"""
    # Get all existing ticket numbers for this competition
    existing_tickets = await db.tickets.find(
        {"competition_id": competition_id},
        {"ticket_number": 1, "_id": 0}
    ).to_list(max_tickets)
    
    used_numbers = set(t["ticket_number"] for t in existing_tickets)
    
    # Generate random number until we find one that's not used
    max_attempts = 1000
    for _ in range(max_attempts):
        random_num = random.randint(1, max_tickets)
        if random_num not in used_numbers:
            return random_num
    
    # Fallback: find first available number
    all_numbers = set(range(1, max_tickets + 1))
    available = all_numbers - used_numbers
    if available:
        return random.choice(list(available))
    
    # No numbers available
    raise Exception("No ticket numbers available")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str = "general"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str = "general"):
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
    
    async def broadcast(self, message: dict, channel: str = "general"):
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass
    
    async def broadcast_all(self, message: dict):
        for channel in self.active_connections:
            await self.broadcast(message, channel)

ws_manager = ConnectionManager()

app = FastAPI(title="Zektrix UK Competition Platform")
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS (imported from models.py) ====================
# ==================== EMAIL HELPERS (imported from email_service.py) ====================
# ==================== PUSH HELPERS ====================

# Wrap push functions to auto-pass db
async def notify_user_push(user_id, title, body, url="https://zektrix.uk"):
    await _notify_user_push(db, user_id, title, body, url)

async def notify_competition_participants_push(competition_id, title, body, url=None):
    await _notify_comp_push(db, competition_id, title, body, url)

# ==================== AUTH HELPERS ====================

# ==================== AUTH HELPERS ====================

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {"user_id": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    token = None
    if credentials:
        token = credentials.credentials
    elif request:
        token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if it's a session token (from Google OAuth)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if session:
        expires_at = session.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
        user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        # Check if user is blocked
        if user.get("is_blocked"):
            raise HTTPException(status_code=403, detail="Contul tău a fost blocat. Contactează suportul.")
        return user
    
    # Try JWT token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        # Check if user is blocked
        if user.get("is_blocked"):
            raise HTTPException(status_code=403, detail="Contul tău a fost blocat. Contactează suportul.")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=dict)
async def register(user: UserCreate, referral_code: Optional[str] = None):
    existing = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_referral_code = f"ZEK{user_id[-6:].upper()}"
    
    user_doc = {
        "user_id": user_id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "password_hash": hash_password(user.password),
        "balance": 0.0,
        "role": "user",
        "picture": None,
        "referral_code": user_referral_code,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Handle referral if code provided
    if referral_code:
        referrer = await db.users.find_one({"referral_code": referral_code.upper()}, {"_id": 0})
        if referrer and referrer["user_id"] != user_id:
            await db.referrals.insert_one({
                "referral_id": f"ref_{uuid.uuid4().hex[:12]}",
                "referrer_id": referrer["user_id"],
                "referred_id": user_id,
                "status": "pending",
                "bonus_amount": 5.0,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Send welcome email (non-blocking)
    asyncio.create_task(send_welcome_email(user.email, user.username, user_referral_code))
    
    token = create_access_token(user_id, "user")
    return {"token": token, "user": {k: v for k, v in user_doc.items() if k != "password_hash" and k != "_id"}}

@api_router.post("/auth/login", response_model=dict)
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email}, {"_id": 0})
    if not db_user or not verify_password(user.password, db_user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(db_user["user_id"], db_user["role"])
    return {"token": token, "user": {k: v for k, v in db_user.items() if k != "password_hash"}}

@api_router.get("/auth/session")
async def process_session(session_id: str, response: Response):
    """Process Google OAuth session_id and return user data"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        data = resp.json()
        email = data.get("email")
        name = data.get("name")
        picture = data.get("picture")
        session_token = data.get("session_token")
        
        # Find or create user
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        if existing_user:
            user_id = existing_user["user_id"]
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"picture": picture, "name": name}}
            )
        else:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            username = email.split("@")[0] + "_" + uuid.uuid4().hex[:4]
            await db.users.insert_one({
                "user_id": user_id,
                "username": username,
                "email": email,
                "name": name,
                "picture": picture,
                "balance": 0.0,
                "role": "user",
                "password_hash": "",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Store session
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.user_sessions.update_one(
            {"user_id": user_id},
            {"$set": {
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7*24*60*60
        )
        
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
        return {"user": user, "token": session_token}

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {k: v for k, v in current_user.items() if k != "password_hash"}

@api_router.put("/auth/profile")
async def update_profile(update: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update user's own profile"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    # Check username uniqueness if changing
    if "username" in update_data:
        existing = await db.users.find_one({"username": update_data["username"], "user_id": {"$ne": current_user["user_id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Username deja utilizat")
    
    await db.users.update_one({"user_id": current_user["user_id"]}, {"$set": update_data})
    updated_user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0, "password_hash": 0})
    return updated_user

@api_router.post("/auth/logout")
async def logout(response: Response, current_user: dict = Depends(get_current_user)):
    await db.user_sessions.delete_one({"user_id": current_user["user_id"]})
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

# ==================== PASSWORD RESET ====================

@api_router.post("/auth/request-password-reset")
async def request_password_reset(request: PasswordResetRequest):
    """Request a password reset email"""
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "Dacă emailul există, vei primi un link de resetare"}
    
    # Generate reset token (valid for 1 hour)
    reset_token = f"reset_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token
    await db.password_resets.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "token": reset_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    # Send email
    await send_password_reset_email(user["email"], user.get("username", "Utilizator"), reset_token)
    
    return {"message": "Dacă emailul există, vei primi un link de resetare"}

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetConfirm):
    """Reset password using token"""
    # Find reset request
    reset_request = await db.password_resets.find_one({"token": request.token}, {"_id": 0})
    
    if not reset_request:
        raise HTTPException(status_code=400, detail="Link de resetare invalid sau expirat")
    
    # Check expiration
    expires_at = reset_request.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        await db.password_resets.delete_one({"token": request.token})
        raise HTTPException(status_code=400, detail="Link de resetare expirat. Te rugăm să ceri unul nou.")
    
    # Validate password
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Parola trebuie să aibă minim 6 caractere")
    
    # Update password
    await db.users.update_one(
        {"user_id": reset_request["user_id"]},
        {"$set": {"password_hash": hash_password(request.new_password)}}
    )
    
    # Delete reset token
    await db.password_resets.delete_one({"token": request.token})
    
    # Invalidate existing sessions
    await db.user_sessions.delete_many({"user_id": reset_request["user_id"]})
    
    return {"message": "Parola a fost resetată cu succes! Te poți autentifica acum."}

# ==================== COMPETITION ROUTES ====================

@api_router.get("/competitions")
async def get_competitions(status: Optional[str] = None, competition_type: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    if competition_type:
        query["competition_type"] = competition_type
    
    competitions = await db.competitions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    for c in competitions:
        c.setdefault("is_free", False)
    return competitions

@api_router.get("/competitions/{competition_id}")
async def get_competition(competition_id: str):
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    comp.setdefault("is_free", False)
    return comp

@api_router.get("/competitions/{competition_id}/tickets", response_model=List[TicketResponse])
async def get_competition_tickets(competition_id: str):
    tickets = await db.tickets.find({"competition_id": competition_id}, {"_id": 0}).to_list(10000)
    return tickets

# ==================== TICKET PURCHASE ====================

async def check_instant_prizes(competition_id: str, new_sold: int, max_tickets: int):
    """Check if any instant prize thresholds have been crossed and award them"""
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp or not comp.get("instant_prizes"):
        return
    
    current_percent = (new_sold / max_tickets) * 100
    updated = False
    awarded_user_ids = set()
    
    # Collect already awarded user IDs to avoid duplicates
    for prize in comp["instant_prizes"]:
        if prize.get("awarded") and prize.get("winner_user_id"):
            awarded_user_ids.add(prize["winner_user_id"])
    
    for i, prize in enumerate(comp["instant_prizes"]):
        if prize.get("awarded"):
            continue
        if current_percent >= prize.get("percentage", 100):
            all_tickets = await db.tickets.find({"competition_id": competition_id}, {"_id": 0}).to_list(new_sold)
            if not all_tickets:
                continue
            
            # Try to pick a user that hasn't won an instant prize yet
            eligible_tickets = [t for t in all_tickets if t["user_id"] not in awarded_user_ids]
            if not eligible_tickets:
                eligible_tickets = all_tickets
            
            winner_ticket = random.choice(eligible_tickets)
            winner_user = await db.users.find_one({"user_id": winner_ticket["user_id"]}, {"_id": 0})
            
            awarded_user_ids.add(winner_ticket["user_id"])
            
            comp["instant_prizes"][i]["awarded"] = True
            comp["instant_prizes"][i]["winner_user_id"] = winner_ticket["user_id"]
            comp["instant_prizes"][i]["winner_username"] = winner_user.get("username", "Unknown") if winner_user else "Unknown"
            comp["instant_prizes"][i]["winner_ticket_number"] = winner_ticket["ticket_number"]
            comp["instant_prizes"][i]["awarded_at"] = datetime.now(timezone.utc).isoformat()
            updated = True
            
            logger.info(f"Instant prize '{prize.get('prize_name')}' awarded to user {winner_ticket['user_id']} (ticket #{winner_ticket['ticket_number']}) at {current_percent:.1f}% in competition {competition_id}")
            
            await ws_manager.broadcast_all({
                "type": "instant_prize_awarded",
                "competition_id": competition_id,
                "prize_name": prize.get("prize_name"),
                "winner_username": winner_user.get("username", "Unknown") if winner_user else "Unknown",
                "ticket_number": winner_ticket["ticket_number"],
                "percentage": prize.get("percentage")
            })
            
            if winner_user and winner_user.get("email"):
                try:
                    await send_winner_notification(
                        winner_user["email"], 
                        winner_user.get("username", ""),
                        comp["title"],
                        f"Premiu Instant: {prize.get('prize_name', 'Premiu')}",
                        winner_ticket["ticket_number"]
                    )
                except Exception as e:
                    logger.error(f"Failed to send instant prize email: {e}")
    
    if updated:
        await db.competitions.update_one(
            {"competition_id": competition_id},
            {"$set": {"instant_prizes": comp["instant_prizes"]}}
        )

@api_router.post("/tickets/purchase", response_model=List[TicketResponse])
async def purchase_tickets(purchase: TicketPurchase, current_user: dict = Depends(get_current_user)):
    comp = await db.competitions.find_one({"competition_id": purchase.competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    if comp["status"] != "active":
        raise HTTPException(status_code=400, detail="Competition is not active")
    
    # Verify qualification answer
    qual_question = comp.get("qualification_question")
    if qual_question:
        if purchase.qualification_answer is None:
            raise HTTPException(status_code=400, detail="Qualification answer is required")
        if purchase.qualification_answer != qual_question.get("correct_answer"):
            raise HTTPException(status_code=400, detail="Incorrect qualification answer")
    
    available = comp["max_tickets"] - comp["sold_tickets"]
    if purchase.quantity > available:
        raise HTTPException(status_code=400, detail=f"Only {available} tickets available")
    
    total_cost = comp["ticket_price"] * purchase.quantity
    if current_user["balance"] < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Get sold ticket numbers
    sold_tickets = await db.tickets.find(
        {"competition_id": purchase.competition_id},
        {"ticket_number": 1, "_id": 0}
    ).to_list(10000)
    sold_numbers = {t["ticket_number"] for t in sold_tickets}
    
    # Generate available numbers
    all_numbers = set(range(1, comp["max_tickets"] + 1))
    available_numbers = list(all_numbers - sold_numbers)
    
    if len(available_numbers) < purchase.quantity:
        raise HTTPException(status_code=400, detail="Not enough tickets available")
    
    # Random selection
    selected_numbers = random.sample(available_numbers, purchase.quantity)
    
    # Create tickets
    purchased_tickets = []
    for num in selected_numbers:
        ticket_id = f"ticket_{uuid.uuid4().hex[:12]}"
        ticket_doc = {
            "ticket_id": ticket_id,
            "user_id": current_user["user_id"],
            "competition_id": purchase.competition_id,
            "ticket_number": num,
            "purchased_at": datetime.now(timezone.utc).isoformat(),
            "competition_title": comp["title"]
        }
        await db.tickets.insert_one(ticket_doc)
        purchased_tickets.append(ticket_doc)
    
    # Update user balance
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$inc": {"balance": -total_cost}}
    )
    
    # Update competition sold tickets
    new_sold = comp["sold_tickets"] + purchase.quantity
    update_data = {"sold_tickets": new_sold}
    
    # Check for instant win
    if comp["competition_type"] == "instant_win" and new_sold >= comp["max_tickets"]:
        # Auto-select winner
        all_tickets = await db.tickets.find({"competition_id": purchase.competition_id}, {"_id": 0}).to_list(10000)
        winner_ticket = random.choice(all_tickets)
        
        update_data["status"] = "completed"
        update_data["winner_id"] = winner_ticket["user_id"]
        update_data["winner_ticket"] = winner_ticket["ticket_number"]
        
        # Create winner record
        winner_user = await db.users.find_one({"user_id": winner_ticket["user_id"]}, {"_id": 0})
        winner_doc = {
            "winner_id": f"winner_{uuid.uuid4().hex[:12]}",
            "competition_id": purchase.competition_id,
            "competition_title": comp["title"],
            "user_id": winner_ticket["user_id"],
            "username": winner_user.get("username", "Unknown"),
            "ticket_number": winner_ticket["ticket_number"],
            "prize_description": comp.get("prize_description"),
            "announced_at": datetime.now(timezone.utc).isoformat(),
            "is_automatic": True
        }
        await db.winners.insert_one(winner_doc)
    
    await db.competitions.update_one(
        {"competition_id": purchase.competition_id},
        {"$set": update_data}
    )
    
    # Check and award instant prizes based on percentage thresholds
    await check_instant_prizes(purchase.competition_id, new_sold, comp["max_tickets"])
    
    # Record transaction
    await db.transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user["user_id"],
        "transaction_type": "ticket_purchase",
        "amount": -total_cost,
        "status": "completed",
        "description": f"Purchased {purchase.quantity} tickets for {comp['title']}",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Complete pending referral (first purchase bonus)
    pending_referral = await db.referrals.find_one({
        "referred_id": current_user["user_id"],
        "status": "pending"
    })
    if pending_referral:
        # Mark referral as completed
        await db.referrals.update_one(
            {"referral_id": pending_referral["referral_id"]},
            {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
        )
        # Give bonus to both users
        await db.users.update_one(
            {"user_id": pending_referral["referrer_id"]},
            {"$inc": {"balance": 5.0}}
        )
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$inc": {"balance": 5.0}}
        )
        # Record bonus transactions
        for uid, desc in [(pending_referral["referrer_id"], "Referral bonus - friend made first purchase"), 
                          (current_user["user_id"], "Welcome bonus - first purchase with referral")]:
            await db.transactions.insert_one({
                "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
                "user_id": uid,
                "transaction_type": "referral_bonus",
                "amount": 5.0,
                "status": "completed",
                "description": desc,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Broadcast ticket purchase via WebSocket
    await ws_manager.broadcast({
        "type": "ticket_purchased",
        "competition_id": purchase.competition_id,
        "sold_tickets": new_sold,
        "max_tickets": comp["max_tickets"]
    }, f"competition_{purchase.competition_id}")
    
    # Check and send alerts if competition is nearly sold out
    await check_and_send_competition_alerts(purchase.competition_id, new_sold, comp["max_tickets"])
    
    return purchased_tickets

# ==================== CART SYSTEM ====================

@api_router.post("/cart/purchase")
async def purchase_cart(cart: CartPurchase, current_user: dict = Depends(get_current_user)):
    """Purchase multiple competitions at once from cart"""
    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Validate all items first
    total_cost = 0
    validated_items = []
    
    for item in cart.items:
        comp = await db.competitions.find_one({"competition_id": item.competition_id}, {"_id": 0})
        if not comp:
            raise HTTPException(status_code=404, detail=f"Competition {item.competition_id} not found")
        
        if comp["status"] != "active":
            raise HTTPException(status_code=400, detail=f"Competition '{comp['title']}' is not active")
        
        available = comp["max_tickets"] - comp["sold_tickets"]
        if item.quantity > available:
            raise HTTPException(status_code=400, detail=f"Only {available} tickets available for '{comp['title']}'")
        
        # Verify qualification answer
        qual_question = comp.get("qualification_question")
        if qual_question:
            if item.qualification_answer is None:
                raise HTTPException(status_code=400, detail=f"Please answer the qualification question for '{comp['title']}'")
            if item.qualification_answer != qual_question.get("correct_answer"):
                raise HTTPException(status_code=400, detail=f"Incorrect answer for '{comp['title']}'")
        
        item_cost = comp["ticket_price"] * item.quantity
        total_cost += item_cost
        validated_items.append({
            "competition": comp,
            "quantity": item.quantity,
            "cost": item_cost,
            "qualification_answer": item.qualification_answer
        })
    
    if cart.payment_method == "wallet":
        # Check balance
        if current_user.get("balance", 0) < total_cost:
            raise HTTPException(status_code=400, detail=f"Insufficient balance. Need £{total_cost:.2f}")
        
        # Deduct balance
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$inc": {"balance": -total_cost}}
        )
        
        all_tickets = []
        
        # Process each item
        for validated in validated_items:
            comp = validated["competition"]
            quantity = validated["quantity"]
            
            # Generate tickets
            existing_tickets = await db.tickets.find(
                {"competition_id": comp["competition_id"]},
                {"ticket_number": 1}
            ).to_list(comp["max_tickets"])
            existing_numbers = {t["ticket_number"] for t in existing_tickets}
            available_numbers = [n for n in range(1, comp["max_tickets"] + 1) if n not in existing_numbers]
            selected_numbers = random.sample(available_numbers, quantity)
            
            tickets = []
            for num in selected_numbers:
                ticket_doc = {
                    "ticket_id": f"ticket_{uuid.uuid4().hex[:12]}",
                    "user_id": current_user["user_id"],
                    "competition_id": comp["competition_id"],
                    "ticket_number": num,
                    "purchased_at": datetime.now(timezone.utc).isoformat(),
                    "competition_title": comp["title"],
                    "qualification_answer": validated["qualification_answer"]
                }
                await db.tickets.insert_one(ticket_doc)
                tickets.append(ticket_doc)
            
            new_sold = comp["sold_tickets"] + quantity
            update_data = {"sold_tickets": new_sold}
            
            # Check for instant win
            if comp["competition_type"] == "instant_win" and new_sold >= comp["max_tickets"]:
                winner_ticket = random.choice(tickets)
                update_data["status"] = "completed"
                update_data["winner_id"] = winner_ticket["user_id"]
                update_data["winner_ticket"] = winner_ticket["ticket_number"]
            
            await db.competitions.update_one(
                {"competition_id": comp["competition_id"]},
                {"$set": update_data}
            )
            
            # Broadcast update
            await ws_manager.broadcast({
                "type": "ticket_purchased",
                "competition_id": comp["competition_id"],
                "sold_tickets": new_sold,
                "max_tickets": comp["max_tickets"]
            }, f"competition_{comp['competition_id']}")
            
            all_tickets.extend(tickets)
        
        # Record transaction
        await db.transactions.insert_one({
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "user_id": current_user["user_id"],
            "transaction_type": "cart_purchase",
            "amount": -total_cost,
            "status": "completed",
            "description": f"Cart purchase: {len(cart.items)} competitions, {sum(i.quantity for i in cart.items)} tickets",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": True,
            "total_paid": total_cost,
            "tickets_purchased": len(all_tickets),
            "tickets": all_tickets
        }
    
    else:  # Viva payment
        # Create Viva order for cart total
        access_token = await get_viva_access_token()
        if not access_token:
            raise HTTPException(status_code=500, detail="Payment service unavailable")
        
        # Store pending cart purchase
        pending_id = f"pending_cart_{uuid.uuid4().hex[:12]}"
        await db.pending_purchases.insert_one({
            "pending_id": pending_id,
            "user_id": current_user["user_id"],
            "items": [{"competition_id": i.competition_id, "quantity": i.quantity, "qualification_answer": i.qualification_answer} for i in cart.items],
            "total_amount": total_cost,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        })
        
        amount_in_cents = int(total_cost * 100)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        order_data = {
            "amount": amount_in_cents,
            "currencyCode": 826,
            "customerTrns": f"Cart: {len(cart.items)} competitions",
            "customer": {
                "email": current_user.get("email", ""),
                "fullName": current_user.get("username", ""),
                "requestLang": "en-GB"
            },
            "merchantTrns": pending_id,
            "sourceCode": "9806",
            "successUrl": "https://zektrix.uk/payment/success",
            "failureUrl": "https://zektrix.uk/payment/failed",
            "cancelUrl": "https://zektrix.uk/payment/cancel"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VIVA_API_URL}/checkout/v2/orders",
                headers=headers,
                json=order_data
            )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to create payment order")
        
        order_code = response.json().get("orderCode")
        
        await db.pending_purchases.update_one(
            {"pending_id": pending_id},
            {"$set": {"viva_order_code": order_code}}
        )
        
        checkout_url = f"{VIVA_CHECKOUT_URL}?ref={order_code}"
        
        return {
            "checkout_url": checkout_url,
            "order_code": order_code,
            "total_amount": total_cost
        }

@api_router.get("/tickets/my", response_model=List[TicketResponse])
async def get_my_tickets(current_user: dict = Depends(get_current_user)):
    tickets = await db.tickets.find({"user_id": current_user["user_id"]}, {"_id": 0}).sort("purchased_at", -1).to_list(1000)
    
    # Enrich tickets with competition titles
    enriched_tickets = []
    for ticket in tickets:
        comp = await db.competitions.find_one({"competition_id": ticket["competition_id"]}, {"_id": 0, "title": 1, "image_url": 1})
        ticket["competition_title"] = comp.get("title", "Unknown") if comp else "Unknown"
        ticket["competition_image"] = comp.get("image_url", "") if comp else ""
        enriched_tickets.append(ticket)
    
    return enriched_tickets

@api_router.get("/tickets/search", response_model=TicketSearchResult)
async def search_tickets_by_username(username: str = Query(..., min_length=1)):
    # Search by username, email, first_name, last_name (partial match)
    user_query = {
        "$or": [
            {"username": {"$regex": username, "$options": "i"}},
            {"email": {"$regex": username, "$options": "i"}},
            {"first_name": {"$regex": username, "$options": "i"}},
            {"last_name": {"$regex": username, "$options": "i"}}
        ]
    }
    user = await db.users.find_one(user_query, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tickets = await db.tickets.find({"user_id": user["user_id"]}, {"_id": 0}).sort("purchased_at", -1).to_list(1000)
    
    # Enrich tickets with competition titles
    enriched_tickets = []
    for ticket in tickets:
        comp = await db.competitions.find_one({"competition_id": ticket["competition_id"]}, {"_id": 0, "title": 1})
        ticket["competition_title"] = comp.get("title", "Unknown") if comp else "Unknown"
        enriched_tickets.append(ticket)
    
    return {"username": user["username"], "tickets": enriched_tickets}

class TicketPurchaseViva(BaseModel):
    competition_id: str
    quantity: int
    qualification_answer: Optional[int] = None  # Index of selected answer

@api_router.post("/tickets/purchase-viva")
async def purchase_tickets_with_viva(purchase: TicketPurchaseViva, current_user: dict = Depends(get_current_user)):
    """Purchase tickets directly with Viva Payments (without using wallet balance)"""
    comp = await db.competitions.find_one({"competition_id": purchase.competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    if comp["status"] != "active":
        raise HTTPException(status_code=400, detail="Competition is not active")
    
    # Verify qualification answer
    qual_question = comp.get("qualification_question")
    if qual_question:
        if purchase.qualification_answer is None:
            raise HTTPException(status_code=400, detail="Qualification answer is required")
        if purchase.qualification_answer != qual_question.get("correct_answer"):
            raise HTTPException(status_code=400, detail="Incorrect qualification answer")
    
    available = comp["max_tickets"] - comp["sold_tickets"]
    if purchase.quantity > available:
        raise HTTPException(status_code=400, detail=f"Only {available} tickets available")
    
    total_cost = comp["ticket_price"] * purchase.quantity
    amount_cents = int(total_cost * 100)
    
    try:
        token = await get_viva_access_token()
        
        # Store pending ticket purchase info
        pending_purchase_id = f"pending_{uuid.uuid4().hex[:12]}"
        await db.pending_purchases.insert_one({
            "pending_id": pending_purchase_id,
            "user_id": current_user["user_id"],
            "competition_id": purchase.competition_id,
            "quantity": purchase.quantity,
            "total_cost": total_cost,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        order_payload = {
            "amount": amount_cents,
            "currencyCode": 826,
            "customerTrns": f"Tickets for {comp['title']} - {purchase.quantity} tickets",
            "customer": {
                "email": current_user["email"],
                "fullName": current_user.get("username", "User"),
                "requestLang": "en-GB"
            },
            "merchantTrns": pending_purchase_id,
            "paymentTimeout": 1800,
            "sourceCode": "9806",
            "successUrl": "https://zektrix.uk/payment/success",
            "failureUrl": "https://zektrix.uk/payment/failed",
            "cancelUrl": "https://zektrix.uk/payment/cancel"
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VIVA_API_URL}/checkout/v2/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=order_payload,
                timeout=30.0
            )
            
            if resp.status_code != 200:
                logger.error(f"Viva order error: {resp.text}")
                raise HTTPException(status_code=500, detail="Failed to create payment order")
            
            data = resp.json()
            order_code = str(data.get("orderCode"))
            
            # Update pending purchase with order code
            await db.pending_purchases.update_one(
                {"pending_id": pending_purchase_id},
                {"$set": {"viva_order_code": order_code}}
            )
            
            # Store transaction
            transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
            await db.transactions.insert_one({
                "transaction_id": transaction_id,
                "user_id": current_user["user_id"],
                "transaction_type": "ticket_purchase_viva",
                "amount": -total_cost,
                "status": "pending",
                "viva_order_code": order_code,
                "pending_purchase_id": pending_purchase_id,
                "description": f"Purchase {purchase.quantity} tickets for {comp['title']}",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            checkout_url = f"{VIVA_CHECKOUT_URL}?ref={order_code}"
            return {"checkout_url": checkout_url, "order_code": order_code, "transaction_id": transaction_id}
    
    except httpx.HTTPError as e:
        logger.error(f"Payment error: {e}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")

# ==================== FREE ENTRY ====================

class FreeEntryRequest(BaseModel):
    competition_id: str
    qualification_answer: Optional[int] = None

@api_router.post("/tickets/enter-free")
async def enter_free_competition(entry: FreeEntryRequest, current_user: dict = Depends(get_current_user)):
    comp = await db.competitions.find_one({"competition_id": entry.competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    if not comp.get("is_free"):
        raise HTTPException(status_code=400, detail="This competition is not free")
    
    if comp["status"] != "active":
        raise HTTPException(status_code=400, detail="Competition is not active")
    
    # Check if user already entered this free competition
    existing = await db.tickets.find_one({
        "user_id": current_user["user_id"],
        "competition_id": entry.competition_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Ai participat deja la această competiție gratuită")
    
    # Verify qualification answer
    qual_question = comp.get("qualification_question")
    if qual_question:
        if entry.qualification_answer is None:
            raise HTTPException(status_code=400, detail="Qualification answer is required")
        if entry.qualification_answer != qual_question.get("correct_answer"):
            raise HTTPException(status_code=400, detail="Incorrect qualification answer")
    
    available = comp["max_tickets"] - comp["sold_tickets"]
    if available <= 0:
        raise HTTPException(status_code=400, detail="No spots available")
    
    # Generate random ticket number
    sold_tickets = await db.tickets.find(
        {"competition_id": entry.competition_id},
        {"ticket_number": 1, "_id": 0}
    ).to_list(10000)
    sold_numbers = {t["ticket_number"] for t in sold_tickets}
    all_numbers = set(range(1, comp["max_tickets"] + 1))
    available_numbers = list(all_numbers - sold_numbers)
    
    if not available_numbers:
        raise HTTPException(status_code=400, detail="No spots available")
    
    selected_number = random.choice(available_numbers)
    
    ticket_id = f"ticket_{uuid.uuid4().hex[:12]}"
    ticket_doc = {
        "ticket_id": ticket_id,
        "user_id": current_user["user_id"],
        "competition_id": entry.competition_id,
        "ticket_number": selected_number,
        "purchased_at": datetime.now(timezone.utc).isoformat(),
        "competition_title": comp["title"],
        "is_free_entry": True
    }
    await db.tickets.insert_one(ticket_doc)
    
    # Update sold tickets count
    new_sold = comp["sold_tickets"] + 1
    update_data = {"sold_tickets": new_sold}
    
    if comp["competition_type"] == "instant_win" and new_sold >= comp["max_tickets"]:
        # Auto-select winner when all spots are filled
        all_tickets = await db.tickets.find({"competition_id": entry.competition_id}, {"_id": 0}).to_list(new_sold)
        winner_ticket = random.choice(all_tickets)
        
        update_data["status"] = "completed"
        update_data["winner_id"] = winner_ticket["user_id"]
        update_data["winner_ticket"] = winner_ticket["ticket_number"]
        
        # Create winner record
        winner_user = await db.users.find_one({"user_id": winner_ticket["user_id"]}, {"_id": 0})
        winner_doc = {
            "winner_id": f"winner_{uuid.uuid4().hex[:12]}",
            "competition_id": entry.competition_id,
            "competition_title": comp["title"],
            "user_id": winner_ticket["user_id"],
            "username": winner_user.get("username", "Unknown") if winner_user else "Unknown",
            "ticket_number": winner_ticket["ticket_number"],
            "prize_description": comp.get("prize_description"),
            "announced_at": datetime.now(timezone.utc).isoformat(),
            "is_automatic": True
        }
        await db.winners.insert_one(winner_doc)
        
        # Send winner notification email
        if winner_user and winner_user.get("email"):
            try:
                await send_winner_notification(
                    winner_user["email"],
                    winner_user.get("username", ""),
                    comp["title"],
                    comp.get("prize_description", "Premiu principal"),
                    winner_ticket["ticket_number"]
                )
            except Exception as e:
                logger.error(f"Failed to send winner email: {e}")
    
    await db.competitions.update_one(
        {"competition_id": entry.competition_id},
        {"$set": update_data}
    )
    
    # Check instant prizes for free entry too
    await check_instant_prizes(entry.competition_id, new_sold, comp["max_tickets"])
    
    ticket_doc.pop("_id", None)
    
    return {
        "message": "Felicitări! Ai intrat cu succes în competiție!",
        "ticket": {
            "ticket_id": ticket_id,
            "ticket_number": selected_number,
            "competition_title": comp["title"]
        }
    }

@api_router.get("/wallet/balance")
async def get_wallet_balance(current_user: dict = Depends(get_current_user)):
    return {"balance": current_user["balance"]}

@api_router.get("/wallet/transactions")
async def get_wallet_transactions(current_user: dict = Depends(get_current_user)):
    try:
        transactions = await db.transactions.find({"user_id": current_user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
        # Ensure all required fields exist
        cleaned = []
        for t in transactions:
            cleaned.append({
                "transaction_id": t.get("transaction_id", "unknown"),
                "user_id": t.get("user_id", current_user["user_id"]),
                "transaction_type": t.get("transaction_type", "unknown"),
                "amount": float(t.get("amount", 0)),
                "status": t.get("status", "unknown"),
                "description": t.get("description", ""),
                "created_at": t.get("created_at", datetime.now(timezone.utc).isoformat())
            })
        return cleaned
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return []

# Viva Payments Token Cache
viva_token_cache = {"token": None, "expires_at": None}

async def get_viva_access_token():
    global viva_token_cache
    if viva_token_cache["token"] and viva_token_cache["expires_at"] and viva_token_cache["expires_at"] > datetime.now(timezone.utc):
        return viva_token_cache["token"]
    
    credentials = base64.b64encode(f"{VIVA_CLIENT_ID}:{VIVA_CLIENT_SECRET}".encode()).decode()
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://accounts.vivapayments.com/connect/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"grant_type": "client_credentials"},
            timeout=30.0
        )
        if resp.status_code != 200:
            logger.error(f"Viva token error: {resp.text}")
            raise HTTPException(status_code=500, detail="Failed to authenticate with payment provider")
        
        data = resp.json()
        viva_token_cache["token"] = data["access_token"]
        viva_token_cache["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600) - 60)
        return viva_token_cache["token"]

@api_router.post("/wallet/deposit")
async def wallet_deposit(deposit: WalletDeposit, current_user: dict = Depends(get_current_user)):
    """Create Viva Payments checkout for wallet deposit"""
    if deposit.amount < 5:
        raise HTTPException(status_code=400, detail="Minimum deposit is £5")
    if deposit.amount > 5000:
        raise HTTPException(status_code=400, detail="Maximum deposit is £5,000")
    
    # Get deposit bonus settings
    settings = await db.site_settings.find_one({"setting_id": "deposit_bonus"}, {"_id": 0})
    bonus_percent = settings.get("bonus_percent", 0) if settings else 0
    bonus_max = settings.get("bonus_max", 0) if settings else 0
    bonus_active = settings.get("active", False) if settings else False
    
    calculated_bonus = 0
    if bonus_active and bonus_percent > 0:
        calculated_bonus = min(deposit.amount * (bonus_percent / 100), bonus_max) if bonus_max > 0 else deposit.amount * (bonus_percent / 100)
    
    # Create Viva order
    access_token = await get_viva_access_token()
    if not access_token:
        raise HTTPException(status_code=500, detail="Payment service unavailable")
    
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    amount_cents = int(deposit.amount * 100)
    
    async with httpx.AsyncClient() as http_client:
        order_data = {
            "amount": amount_cents,
            "customerTrns": f"Wallet Deposit £{deposit.amount:.2f}",
            "merchantTrns": transaction_id,
            "sourceCode": VIVA_SOURCE_CODE,
            "paymentTimeout": 1800,
            "currencyCode": "826",
            "successUrl": "https://zektrix.uk/wallet?deposit=success",
            "failureUrl": "https://zektrix.uk/wallet?deposit=failed",
            "cancelUrl": "https://zektrix.uk/wallet?deposit=cancel"
        }
        
        resp = await http_client.post(
            f"{VIVA_API_URL}/checkout/v2/orders",
            json=order_data,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0
        )
        
        if resp.status_code != 200:
            logger.error(f"Viva deposit order error: {resp.text}")
            raise HTTPException(status_code=500, detail="Failed to create deposit order")
        
        order_code = str(resp.json().get("orderCode", ""))
    
    # Record pending transaction
    await db.transactions.insert_one({
        "transaction_id": transaction_id,
        "user_id": current_user["user_id"],
        "transaction_type": "deposit",
        "amount": deposit.amount,
        "bonus_preview": calculated_bonus,
        "status": "pending",
        "viva_order_code": order_code,
        "description": f"Wallet deposit £{deposit.amount:.2f}" + (f" (+£{calculated_bonus:.2f} bonus)" if calculated_bonus > 0 else ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    checkout_url = f"{VIVA_CHECKOUT_URL}?ref={order_code}"
    return {
        "checkout_url": checkout_url,
        "order_code": order_code,
        "transaction_id": transaction_id,
        "amount": deposit.amount,
        "bonus": calculated_bonus
    }

class WithdrawalRequest(BaseModel):
    amount: float
    method: str = "bank_transfer"
    bank_details: Optional[str] = None

@api_router.post("/wallet/withdraw")
async def request_withdrawal(req: WithdrawalRequest, current_user: dict = Depends(get_current_user)):
    """Request a withdrawal from wallet balance"""
    if req.amount < 10:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is £10")
    
    balance = current_user.get("balance", 0)
    if req.amount > balance:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. You have £{balance:.2f}")
    
    # Check for pending withdrawals
    pending = await db.withdrawal_requests.count_documents({
        "user_id": current_user["user_id"],
        "status": "pending"
    })
    if pending > 0:
        raise HTTPException(status_code=400, detail="You already have a pending withdrawal request")
    
    withdrawal_id = f"wd_{uuid.uuid4().hex[:12]}"
    
    # Freeze the amount (deduct from balance immediately)
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$inc": {"balance": -req.amount}}
    )
    
    withdrawal_doc = {
        "withdrawal_id": withdrawal_id,
        "user_id": current_user["user_id"],
        "username": current_user.get("username", ""),
        "email": current_user.get("email", ""),
        "amount": req.amount,
        "method": req.method,
        "bank_details": req.bank_details,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "processed_at": None,
        "admin_note": None
    }
    await db.withdrawal_requests.insert_one(withdrawal_doc)
    
    # Record transaction
    await db.transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user["user_id"],
        "transaction_type": "withdrawal_request",
        "amount": -req.amount,
        "status": "pending",
        "description": f"Withdrawal request £{req.amount:.2f} ({req.method})",
        "withdrawal_id": withdrawal_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Notify admins
    asyncio.create_task(notify_user_push(
        "admin_broadcast",
        "New Withdrawal Request",
        f"{current_user.get('username', 'User')} requested £{req.amount:.2f} withdrawal",
        "https://zektrix.uk/admin"
    ))
    
    return {"withdrawal_id": withdrawal_id, "amount": req.amount, "status": "pending"}

@api_router.get("/wallet/withdrawals")
async def get_my_withdrawals(current_user: dict = Depends(get_current_user)):
    """Get user's withdrawal requests"""
    withdrawals = await db.withdrawal_requests.find(
        {"user_id": current_user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return withdrawals

@api_router.get("/wallet/bonus-info")
async def get_deposit_bonus_info():
    """Public endpoint to show current deposit bonus"""
    settings = await db.site_settings.find_one({"setting_id": "deposit_bonus"}, {"_id": 0})
    if not settings or not settings.get("active"):
        return {"active": False, "bonus_percent": 0, "bonus_max": 0}
    return {
        "active": True,
        "bonus_percent": settings.get("bonus_percent", 0),
        "bonus_max": settings.get("bonus_max", 0)
    }

# ==================== ADMIN WALLET MANAGEMENT ====================

@api_router.get("/admin/wallet/withdrawals")
async def get_all_withdrawals(status: Optional[str] = None, admin: dict = Depends(get_admin_user)):
    """Get all withdrawal requests (admin)"""
    query = {}
    if status:
        query["status"] = status
    withdrawals = await db.withdrawal_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return withdrawals

@api_router.post("/admin/wallet/withdrawal/{withdrawal_id}/approve")
async def approve_withdrawal(withdrawal_id: str, admin: dict = Depends(get_admin_user)):
    """Approve a withdrawal request"""
    wd = await db.withdrawal_requests.find_one({"withdrawal_id": withdrawal_id}, {"_id": 0})
    if not wd:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    if wd["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Withdrawal is already {wd['status']}")
    
    await db.withdrawal_requests.update_one(
        {"withdrawal_id": withdrawal_id},
        {"$set": {"status": "approved", "processed_at": datetime.now(timezone.utc).isoformat(), "admin_note": "Approved"}}
    )
    
    # Update related transaction
    await db.transactions.update_one(
        {"withdrawal_id": withdrawal_id},
        {"$set": {"status": "completed", "description": f"Withdrawal £{wd['amount']:.2f} - Approved"}}
    )
    
    # Notify user
    asyncio.create_task(notify_user_push(
        wd["user_id"],
        "Withdrawal Approved!",
        f"Your withdrawal of £{wd['amount']:.2f} has been approved and is being processed.",
        "https://zektrix.uk/wallet"
    ))
    
    return {"success": True, "withdrawal_id": withdrawal_id, "status": "approved"}

@api_router.post("/admin/wallet/withdrawal/{withdrawal_id}/reject")
async def reject_withdrawal(withdrawal_id: str, reason: str = "Rejected by admin", admin: dict = Depends(get_admin_user)):
    """Reject a withdrawal and refund balance"""
    wd = await db.withdrawal_requests.find_one({"withdrawal_id": withdrawal_id}, {"_id": 0})
    if not wd:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    if wd["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Withdrawal is already {wd['status']}")
    
    # Refund balance
    await db.users.update_one(
        {"user_id": wd["user_id"]},
        {"$inc": {"balance": wd["amount"]}}
    )
    
    await db.withdrawal_requests.update_one(
        {"withdrawal_id": withdrawal_id},
        {"$set": {"status": "rejected", "processed_at": datetime.now(timezone.utc).isoformat(), "admin_note": reason}}
    )
    
    await db.transactions.update_one(
        {"withdrawal_id": withdrawal_id},
        {"$set": {"status": "refunded", "description": f"Withdrawal £{wd['amount']:.2f} - Rejected: {reason}"}}
    )
    
    # Notify user
    asyncio.create_task(notify_user_push(
        wd["user_id"],
        "Withdrawal Update",
        f"Your withdrawal of £{wd['amount']:.2f} was returned to your wallet.",
        "https://zektrix.uk/wallet"
    ))
    
    return {"success": True, "withdrawal_id": withdrawal_id, "status": "rejected"}

class AdminWalletAdjust(BaseModel):
    user_id: str
    amount: float
    reason: str = "Admin adjustment"

@api_router.post("/admin/wallet/adjust")
async def admin_adjust_wallet(adj: AdminWalletAdjust, admin: dict = Depends(get_admin_user)):
    """Admin manually add/subtract wallet funds"""
    user = await db.users.find_one({"user_id": adj.user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_balance = user.get("balance", 0) + adj.amount
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Would result in negative balance")
    
    await db.users.update_one(
        {"user_id": adj.user_id},
        {"$set": {"balance": new_balance}}
    )
    
    await db.transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": adj.user_id,
        "transaction_type": "admin_adjustment",
        "amount": adj.amount,
        "status": "completed",
        "description": f"{adj.reason} ({'+' if adj.amount > 0 else ''}£{adj.amount:.2f})",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "new_balance": new_balance}

class DepositBonusSettings(BaseModel):
    active: bool = False
    bonus_percent: float = 10
    bonus_max: float = 20

@api_router.get("/admin/wallet/bonus-settings")
async def get_bonus_settings(admin: dict = Depends(get_admin_user)):
    """Get deposit bonus configuration"""
    settings = await db.site_settings.find_one({"setting_id": "deposit_bonus"}, {"_id": 0})
    if not settings:
        return {"active": False, "bonus_percent": 10, "bonus_max": 20}
    return {"active": settings.get("active", False), "bonus_percent": settings.get("bonus_percent", 10), "bonus_max": settings.get("bonus_max", 20)}

@api_router.put("/admin/wallet/bonus-settings")
async def set_bonus_settings(settings: DepositBonusSettings, admin: dict = Depends(get_admin_user)):
    """Update deposit bonus configuration"""
    await db.site_settings.update_one(
        {"setting_id": "deposit_bonus"},
        {"$set": {
            "setting_id": "deposit_bonus",
            "active": settings.active,
            "bonus_percent": settings.bonus_percent,
            "bonus_max": settings.bonus_max,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    return {"success": True, **settings.model_dump()}

@api_router.get("/admin/wallet/stats")
async def get_wallet_stats(admin: dict = Depends(get_admin_user)):
    """Get wallet-related statistics"""
    total_deposits = await db.transactions.aggregate([
        {"$match": {"transaction_type": "deposit", "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    total_withdrawals = await db.withdrawal_requests.aggregate([
        {"$match": {"status": "approved"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    pending_withdrawals = await db.withdrawal_requests.count_documents({"status": "pending"})
    
    total_user_balances = await db.users.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$balance"}}}
    ]).to_list(1)
    
    return {
        "total_deposits": total_deposits[0]["total"] if total_deposits else 0,
        "total_withdrawals": total_withdrawals[0]["total"] if total_withdrawals else 0,
        "pending_withdrawals": pending_withdrawals,
        "total_user_balances": total_user_balances[0]["total"] if total_user_balances else 0
    }

@api_router.post("/wallet/webhook")
async def wallet_viva_webhook(request: Request):
    """Handle Viva payment webhooks for wallet deposits"""
    try:
        body = await request.json()
        order_code = str(body.get("OrderCode") or body.get("orderCode", ""))
        status_id = body.get("StatusId") or body.get("statusId", "")
        
        if not order_code:
            return {"status": "ok"}
        
        transaction = await db.transactions.find_one({"viva_order_code": order_code}, {"_id": 0})
        if not transaction:
            return {"status": "ok"}
        
        if status_id == "F":  # Success
            await db.transactions.update_one(
                {"transaction_id": transaction["transaction_id"]},
                {"$set": {"status": "completed"}}
            )
            
            # Handle wallet deposit
            if transaction["transaction_type"] == "deposit":
                user = await db.users.find_one({"user_id": transaction["user_id"]})
                deposit_amount = transaction["amount"]
                bonus_amount = 0
                
                # Check site-wide deposit bonus settings
                bonus_settings = await db.site_settings.find_one({"setting_id": "deposit_bonus"}, {"_id": 0})
                if bonus_settings and bonus_settings.get("active"):
                    bp = bonus_settings.get("bonus_percent", 0)
                    bm = bonus_settings.get("bonus_max", 0)
                    calculated = deposit_amount * (bp / 100)
                    bonus_amount = min(calculated, bm) if bm > 0 else calculated
                
                # Also check user-specific bonus (from Lucky Wheel etc.)
                if user and user.get("next_deposit_bonus"):
                    user_bp = user.get("next_deposit_bonus", 0)
                    user_bm = user.get("next_deposit_bonus_max", 50)
                    user_bonus = min(deposit_amount * (user_bp / 100), user_bm)
                    bonus_amount = max(bonus_amount, user_bonus)
                    await db.users.update_one(
                        {"user_id": transaction["user_id"]},
                        {"$unset": {"next_deposit_bonus": "", "next_deposit_bonus_max": "", "milestone_bonus": ""}}
                    )
                
                # Add deposit + bonus to balance
                total_credit = deposit_amount + bonus_amount
                await db.users.update_one(
                    {"user_id": transaction["user_id"]},
                    {"$inc": {"balance": total_credit}}
                )
                
                # Update transaction with bonus info
                if bonus_amount > 0:
                    await db.transactions.update_one(
                        {"transaction_id": transaction["transaction_id"]},
                        {"$set": {"bonus_applied": bonus_amount, "total_credited": total_credit}}
                    )
            # Handle direct ticket purchase
            elif transaction["transaction_type"] == "ticket_purchase_viva":
                pending_id = transaction.get("pending_purchase_id")
                if pending_id:
                    await process_pending_ticket_purchase(pending_id)
                    
        elif status_id in ["E", "X"]:  # Failed/Cancelled
            await db.transactions.update_one(
                {"transaction_id": transaction["transaction_id"]},
                {"$set": {"status": "failed"}}
            )
            # Mark pending purchase as failed
            if transaction.get("pending_purchase_id"):
                await db.pending_purchases.update_one(
                    {"pending_id": transaction["pending_purchase_id"]},
                    {"$set": {"status": "failed"}}
                )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "ok"}

async def process_pending_ticket_purchase(pending_id: str):
    """Process a pending ticket purchase after successful payment"""
    pending = await db.pending_purchases.find_one({"pending_id": pending_id}, {"_id": 0})
    if not pending or pending["status"] != "pending":
        return
    
    comp = await db.competitions.find_one({"competition_id": pending["competition_id"]}, {"_id": 0})
    if not comp or comp["status"] != "active":
        return
    
    # Get sold ticket numbers
    sold_tickets = await db.tickets.find(
        {"competition_id": pending["competition_id"]},
        {"ticket_number": 1, "_id": 0}
    ).to_list(10000)
    sold_numbers = {t["ticket_number"] for t in sold_tickets}
    
    # Generate available numbers
    all_numbers = set(range(1, comp["max_tickets"] + 1))
    available_numbers = list(all_numbers - sold_numbers)
    
    quantity = min(pending["quantity"], len(available_numbers))
    if quantity <= 0:
        await db.pending_purchases.update_one({"pending_id": pending_id}, {"$set": {"status": "failed"}})
        return
    
    # Random selection
    selected_numbers = random.sample(available_numbers, quantity)
    
    # Create tickets
    for num in selected_numbers:
        ticket_id = f"ticket_{uuid.uuid4().hex[:12]}"
        await db.tickets.insert_one({
            "ticket_id": ticket_id,
            "user_id": pending["user_id"],
            "competition_id": pending["competition_id"],
            "ticket_number": num,
            "purchased_at": datetime.now(timezone.utc).isoformat(),
            "competition_title": comp["title"]
        })
    
    # Update competition sold tickets
    new_sold = comp["sold_tickets"] + quantity
    update_data = {"sold_tickets": new_sold}
    
    # Check for instant win
    if comp["competition_type"] == "instant_win" and new_sold >= comp["max_tickets"]:
        all_tickets = await db.tickets.find({"competition_id": pending["competition_id"]}, {"_id": 0}).to_list(10000)
        winner_ticket = random.choice(all_tickets)
        
        update_data["status"] = "completed"
        update_data["winner_id"] = winner_ticket["user_id"]
        update_data["winner_ticket"] = winner_ticket["ticket_number"]
        
        winner_user = await db.users.find_one({"user_id": winner_ticket["user_id"]}, {"_id": 0})
        await db.winners.insert_one({
            "winner_id": f"winner_{uuid.uuid4().hex[:12]}",
            "competition_id": pending["competition_id"],
            "competition_title": comp["title"],
            "user_id": winner_ticket["user_id"],
            "username": winner_user.get("username", "Unknown") if winner_user else "Unknown",
            "ticket_number": winner_ticket["ticket_number"],
            "prize_description": comp.get("prize_description"),
            "announced_at": datetime.now(timezone.utc).isoformat(),
            "is_automatic": True
        })
    
    await db.competitions.update_one(
        {"competition_id": pending["competition_id"]},
        {"$set": update_data}
    )
    
    # Check instant prizes after Viva payment
    await check_instant_prizes(pending["competition_id"], new_sold, comp["max_tickets"])
    
    # Mark pending purchase as completed
    await db.pending_purchases.update_one(
        {"pending_id": pending_id},
        {"$set": {"status": "completed"}}
    )

@api_router.get("/wallet/payment-status/{order_code}")
async def check_payment_status(order_code: str, current_user: dict = Depends(get_current_user)):
    transaction = await db.transactions.find_one(
        {"viva_order_code": order_code, "user_id": current_user["user_id"]},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

# ==================== WINNERS ====================

@api_router.get("/winners", response_model=List[WinnerResponse])
async def get_winners():
    winners = await db.winners.find({}, {"_id": 0}).sort("announced_at", -1).to_list(100)
    return winners

# Default qualification questions pool (2 options: 1 correct, 1 wrong)
QUALIFICATION_QUESTIONS = [
    {
        "question": "SPF-ul te protejează de razele UV?",
        "options": ["Da, corect", "Nu, te protejează de ploaie"],
        "correct_answer": 0
    },
    {
        "question": "Londra este capitala Marii Britanii?",
        "options": ["Da, este capitala", "Nu, este Manchester"],
        "correct_answer": 0
    },
    {
        "question": "Un an bisect are 366 de zile?",
        "options": ["Da, corect", "Nu, are 365 zile"],
        "correct_answer": 0
    },
    {
        "question": "Pacificul este cel mai mare ocean?",
        "options": ["Da, este cel mai mare", "Nu, Atlanticul este mai mare"],
        "correct_answer": 0
    },
    {
        "question": "15 + 27 = 42?",
        "options": ["Da, corect", "Nu, rezultatul este 41"],
        "correct_answer": 0
    },
    {
        "question": "Mercur este planeta cea mai apropiată de Soare?",
        "options": ["Da, corect", "Nu, este Venus"],
        "correct_answer": 0
    },
    {
        "question": "O oră are 60 de minute?",
        "options": ["Da, 60 minute", "Nu, are 100 minute"],
        "correct_answer": 0
    },
    {
        "question": "H2O este simbolul chimic pentru apă?",
        "options": ["Da, corect", "Nu, este O2"],
        "correct_answer": 0
    },
    {
        "question": "Telefonul a fost inventat în 1876?",
        "options": ["Da, de Alexander Graham Bell", "Nu, a fost inventat în 1776"],
        "correct_answer": 0
    },
    {
        "question": "Verde se obține din galben + albastru?",
        "options": ["Da, corect", "Nu, se obține roșu"],
        "correct_answer": 0
    }
]

# AI function to generate description and question
async def generate_ai_content(title: str, category: str = "other"):
    """Generate competition description and qualification question using AI"""
    if not EMERGENT_LLM_KEY:
        return None, None
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"gen_{uuid.uuid4().hex[:8]}",
            system_message="Ești un asistent pentru o platformă de competiții cu premii. Răspunde doar în română."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Pentru competiția "{title}" în categoria "{category}":

1. Scrie o descriere atractivă de maxim 100 cuvinte în română.
2. Generează o întrebare de calificare cu exact 2 răspunsuri (unul corect, unul greșit).

Răspunde EXACT în acest format JSON:
{{
  "description": "descrierea aici",
  "question": "întrebarea aici?",
  "correct_answer": "răspunsul corect",
  "wrong_answer": "răspunsul greșit"
}}"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse JSON from response
        import json
        # Find JSON in response
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end > start:
            data = json.loads(response[start:end])
            question_data = {
                "question": data.get("question", "Aceasta este o întrebare de calificare?"),
                "options": [data.get("correct_answer", "Da, corect"), data.get("wrong_answer", "Nu, incorect")],
                "correct_answer": 0
            }
            return data.get("description"), question_data
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
    
    return None, None

async def generate_seo_content(title: str, description: str, category: str = "other"):
    """Generate SEO meta tags for a competition using AI"""
    if not EMERGENT_LLM_KEY:
        return None
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"seo_{uuid.uuid4().hex[:8]}",
            system_message="Ești un expert SEO. Generează conținut optimizat pentru motoare de căutare."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Generează meta tags SEO pentru această competiție:
Titlu: {title}
Descriere: {description}
Categorie: {category}

Cerințe:
- Meta title: max 60 caractere, include cuvinte cheie
- Meta description: max 155 caractere, call-to-action
- Keywords: 8-10 cuvinte cheie relevante separate prin virgulă
- og_title: titlu pentru social media
- og_description: descriere pentru share pe social media

Răspunde EXACT în format JSON:
{{
  "meta_title": "...",
  "meta_description": "...",
  "keywords": "keyword1, keyword2, ...",
  "og_title": "...",
  "og_description": "..."
}}"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        import json
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
    except Exception as e:
        logger.error(f"SEO generation failed: {e}")
    
    return None

# Default postal entry info
DEFAULT_POSTAL_ENTRY = {
    "company_name": "Zektrix UK Ltd",
    "address_line1": "c/o Bartle House",
    "address_line2": "Oxford Court, Manchester",
    "postcode": "M23 WQ",
    "country": "United Kingdom",
    "instructions": [
        "Nume complet",
        "Adresă poștală",
        "Email + Telefon",
        "Numele competiției"
    ]
}

# ==================== ADMIN ROUTES ====================

class AIGenerateRequest(BaseModel):
    title: str
    category: Optional[str] = "other"

@api_router.post("/admin/generate-ai-content")
async def generate_ai_competition_content(request: AIGenerateRequest, admin: dict = Depends(get_admin_user)):
    """Generate competition description and qualification question using AI"""
    description, question = await generate_ai_content(request.title, request.category)
    
    if not description:
        # Fallback description if AI fails
        fallback_descriptions = {
            "tech": f"Participă la competiția noastră și ai șansa să câștigi {request.title}! Un premiu de excepție pentru pasionații de tehnologie. Nu rata această oportunitate unică!",
            "cars": f"Visul tău de a conduce un {request.title} poate deveni realitate! Intră în competiție și fii unul dintre norocoșii participanți.",
            "cash": f"Câștigă {request.title} și schimbă-ți viața! O sumă care îți poate îndeplini multe dorințe te așteaptă.",
            "other": f"Premiu incredibil: {request.title}! Participă acum la competiția noastră și ai șansa de a câștiga acest premiu fantastic."
        }
        category = request.category or "other"
        fallback_desc = fallback_descriptions.get(category, fallback_descriptions["other"])
        
        return {
            "description": fallback_desc,
            "qualification_question": question if question else random.choice(QUALIFICATION_QUESTIONS),
            "ai_generated": False
        }
    
    return {
        "description": description,
        "qualification_question": question,
        "ai_generated": True
    }

@api_router.post("/admin/competitions", response_model=CompetitionResponse)
async def create_competition(comp: CompetitionCreate, admin: dict = Depends(get_admin_user)):
    competition_id = f"comp_{uuid.uuid4().hex[:12]}"
    
    # Auto-generate qualification question if not provided
    if comp.qualification_question:
        qual_question = comp.qualification_question.model_dump()
    else:
        qual_question = random.choice(QUALIFICATION_QUESTIONS)
    
    comp_doc = {
        "competition_id": competition_id,
        "title": comp.title,
        "description": comp.description,
        "ticket_price": 0 if comp.is_free else comp.ticket_price,
        "max_tickets": comp.max_tickets,
        "sold_tickets": 0,
        "competition_type": comp.competition_type,
        "category": comp.category or "other",
        "status": "active",
        "image_url": comp.image_url,
        "images": comp.images or [],
        "prize_description": comp.prize_description,
        "draw_date": comp.draw_date,
        "qualification_question": qual_question,
        "postal_entry": DEFAULT_POSTAL_ENTRY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "winner_id": None,
        "winner_ticket": None,
        "is_free": bool(comp.is_free),
        "instant_prizes": [
            {**p, "awarded": False, "winner_user_id": None, "winner_ticket_number": None, "awarded_at": None}
            for p in (comp.instant_prizes or [])
        ] if comp.instant_prizes else [],
        "seo": None  # Will be generated automatically
    }
    logger.info(f"Creating competition: {comp.title}, is_free={comp.is_free}")
    await db.competitions.insert_one(comp_doc)
    
    # Generate SEO content asynchronously (don't wait)
    asyncio.create_task(auto_generate_seo(competition_id, comp.title, comp.description, comp.category or "other"))
    
    return comp_doc

async def auto_generate_seo(comp_id: str, title: str, description: str, category: str):
    """Auto-generate SEO for a competition"""
    try:
        seo = await generate_seo_content(title, description, category)
        if seo:
            await db.competitions.update_one(
                {"competition_id": comp_id},
                {"$set": {"seo": seo}}
            )
            logger.info(f"SEO generated for competition {comp_id}")
    except Exception as e:
        logger.error(f"Failed to auto-generate SEO for {comp_id}: {e}")

@api_router.put("/admin/competitions/{competition_id}", response_model=CompetitionResponse)
async def update_competition(competition_id: str, update: CompetitionUpdate, admin: dict = Depends(get_admin_user)):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await db.competitions.update_one(
        {"competition_id": competition_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    return await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})

@api_router.delete("/admin/competitions/{competition_id}")
async def delete_competition(competition_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.competitions.delete_one({"competition_id": competition_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Competition not found")
    return {"message": "Competition deleted"}

@api_router.post("/admin/competitions/{competition_id}/generate-seo")
async def regenerate_seo(competition_id: str, admin: dict = Depends(get_admin_user)):
    """Manually regenerate SEO for a competition"""
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    seo = await generate_seo_content(comp["title"], comp["description"], comp.get("category", "other"))
    if seo:
        await db.competitions.update_one(
            {"competition_id": competition_id},
            {"$set": {"seo": seo}}
        )
        return {"message": "SEO regenerat cu succes!", "seo": seo}
    else:
        raise HTTPException(status_code=500, detail="Nu s-a putut genera SEO. Verifică cheia AI.")

@api_router.post("/admin/competitions/{competition_id}/end")
async def end_competition(competition_id: str, admin: dict = Depends(get_admin_user)):
    """End a classic competition (admin can end at any time)"""
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    if comp["status"] != "active":
        raise HTTPException(status_code=400, detail="Competition is not active")
    
    await db.competitions.update_one(
        {"competition_id": competition_id},
        {"$set": {"status": "completed"}}
    )
    return {"message": "Competition ended successfully"}

@api_router.post("/admin/competitions/{competition_id}/draw-winner")
async def draw_winner(competition_id: str, admin: dict = Depends(get_admin_user)):
    """Manually draw a winner for classic competition"""
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    if comp.get("winner_id"):
        raise HTTPException(status_code=400, detail="Winner already selected")
    
    tickets = await db.tickets.find({"competition_id": competition_id}, {"_id": 0}).to_list(10000)
    if not tickets:
        raise HTTPException(status_code=400, detail="No tickets sold")
    
    winner_ticket = random.choice(tickets)
    winner_user = await db.users.find_one({"user_id": winner_ticket["user_id"]}, {"_id": 0})
    
    await db.competitions.update_one(
        {"competition_id": competition_id},
        {"$set": {
            "status": "completed",
            "winner_id": winner_ticket["user_id"],
            "winner_ticket": winner_ticket["ticket_number"]
        }}
    )
    
    winner_doc = {
        "winner_id": f"winner_{uuid.uuid4().hex[:12]}",
        "competition_id": competition_id,
        "competition_title": comp["title"],
        "user_id": winner_ticket["user_id"],
        "username": winner_user.get("username", "Unknown"),
        "ticket_number": winner_ticket["ticket_number"],
        "prize_description": comp.get("prize_description"),
        "announced_at": datetime.now(timezone.utc).isoformat(),
        "is_automatic": False
    }
    await db.winners.insert_one(winner_doc)
    
    # Send winner notification email
    if winner_user and winner_user.get("email"):
        asyncio.create_task(send_winner_notification_email(
            winner_user["email"],
            winner_user.get("username", "Câștigător"),
            comp["title"],
            comp.get("prize_description"),
            winner_ticket["ticket_number"]
        ))
    
    # Broadcast winner announcement via WebSocket
    await ws_manager.broadcast_all({
        "type": "winner_announced",
        "competition_id": competition_id,
        "competition_title": comp["title"],
        "winner_username": winner_user.get("username", "Unknown"),
        "ticket_number": winner_ticket["ticket_number"]
    })
    
    # Push notification to winner
    await notify_user_push(
        winner_ticket["user_id"],
        "Felicitări! Ai câștigat!",
        f"Ai câștigat la {comp['title']}! Locul #{winner_ticket['ticket_number']} este câștigător!",
        f"https://zektrix.uk/competitions/{competition_id}"
    )
    
    # Push notification to all participants
    await notify_competition_participants_push(
        competition_id,
        f"{comp['title']} - Câștigător extras!",
        f"Câștigătorul a fost extras! Verifică rezultatele.",
        "https://zektrix.uk/winners"
    )
    
    return winner_doc

@api_router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(admin: dict = Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.put("/admin/users/{user_id}")
async def update_user(user_id: str, update: AdminUserUpdate, admin: dict = Depends(get_admin_user)):
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    
    # Update basic fields
    if update.first_name is not None:
        update_data["first_name"] = update.first_name
    if update.last_name is not None:
        update_data["last_name"] = update.last_name
    if update.phone is not None:
        update_data["phone"] = update.phone
    if update.email is not None:
        # Check if email is already taken by another user
        existing = await db.users.find_one({"email": update.email, "user_id": {"$ne": user_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = update.email
    
    # Update balance (add or subtract)
    if update.balance is not None:
        balance_change = update.balance - user.get("balance", 0)
        update_data["balance"] = update.balance
        # Record transaction for audit
        await db.transactions.insert_one({
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "transaction_type": "admin_adjustment",
            "amount": balance_change,
            "status": "completed",
            "description": f"Admin balance set to {update.balance} (change: {'+' if balance_change > 0 else ''}{balance_change})",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Block/Unblock user
    if update.is_blocked is not None:
        update_data["is_blocked"] = update.is_blocked
        if update.is_blocked:
            # Invalidate all sessions when blocked
            await db.user_sessions.delete_many({"user_id": user_id})
    
    # Update password
    if update.new_password:
        if len(update.new_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        update_data["password_hash"] = hash_password(update.new_password)
        # Invalidate sessions after password change
        await db.user_sessions.delete_many({"user_id": user_id})
    
    if update_data:
        await db.users.update_one({"user_id": user_id}, {"$set": update_data})
    
    return await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Delete a user (admin only)"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting admin
    if user.get("role") == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin users")
    
    # Delete user and related data
    await db.users.delete_one({"user_id": user_id})
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.password_resets.delete_many({"user_id": user_id})
    
    # Note: We keep tickets and transactions for audit purposes
    
    return {"message": f"Utilizatorul {user.get('username', user_id)} a fost șters cu succes"}

@api_router.get("/admin/tickets", response_model=List[TicketResponse])
async def get_all_tickets(
    admin: dict = Depends(get_admin_user),
    competition_id: Optional[str] = None,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 200,
    skip: int = 0
):
    query = {}
    if competition_id:
        query["competition_id"] = competition_id
    if user_id:
        query["user_id"] = user_id
    
    # Search by username, email, first_name, last_name OR ticket_number
    if search or username:
        search_term = search or username
        
        # Check if search term is a ticket number (numeric)
        if search_term.isdigit():
            ticket_number = int(search_term)
            query["ticket_number"] = ticket_number
        else:
            # Find users matching the search term
            user_query = {
                "$or": [
                    {"username": {"$regex": search_term, "$options": "i"}},
                    {"email": {"$regex": search_term, "$options": "i"}},
                    {"first_name": {"$regex": search_term, "$options": "i"}},
                    {"last_name": {"$regex": search_term, "$options": "i"}},
                    {"phone": {"$regex": search_term, "$options": "i"}}
                ]
            }
            matching_users = await db.users.find(user_query, {"_id": 0, "user_id": 1}).to_list(1000)
            if matching_users:
                query["user_id"] = {"$in": [u["user_id"] for u in matching_users]}
            else:
                return []  # No matching users found
    
    tickets = await db.tickets.find(query, {"_id": 0}).sort("purchased_at", -1).skip(skip).limit(limit).to_list(limit)
    
    if not tickets:
        return tickets
    
    # Batch fetch all users and competitions at once (instead of N+1 queries)
    user_ids = list(set(t["user_id"] for t in tickets))
    comp_ids = list(set(t["competition_id"] for t in tickets))
    
    users_list = await db.users.find({"user_id": {"$in": user_ids}}, {"_id": 0}).to_list(len(user_ids))
    comps_list = await db.competitions.find({"competition_id": {"$in": comp_ids}}, {"_id": 0, "competition_id": 1, "title": 1}).to_list(len(comp_ids))
    
    users_map = {u["user_id"]: u for u in users_list}
    comps_map = {c["competition_id"]: c.get("title", "Unknown") for c in comps_list}
    
    for ticket in tickets:
        user = users_map.get(ticket["user_id"])
        if user:
            ticket["username"] = user.get("username", "Unknown")
            ticket["first_name"] = user.get("first_name", "")
            ticket["last_name"] = user.get("last_name", "")
            ticket["phone"] = user.get("phone", "")
            ticket["email"] = user.get("email", "")
            ticket["full_name"] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get("username", "Unknown")
        else:
            ticket["username"] = "Unknown"
            ticket["full_name"] = "Unknown"
            ticket["phone"] = ""
            ticket["email"] = ""
        
        ticket["competition_title"] = comps_map.get(ticket["competition_id"], "Unknown")
    
    return tickets

@api_router.post("/admin/winners", response_model=WinnerResponse)
async def add_winner_manually(winner: WinnerCreate, admin: dict = Depends(get_admin_user)):
    """Manually add a winner for classic competitions"""
    comp = await db.competitions.find_one({"competition_id": winner.competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    user = await db.users.find_one({"user_id": winner.user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    winner_doc = {
        "winner_id": f"winner_{uuid.uuid4().hex[:12]}",
        "competition_id": winner.competition_id,
        "competition_title": comp["title"],
        "user_id": winner.user_id,
        "username": user.get("username", "Unknown"),
        "ticket_number": winner.ticket_number,
        "prize_description": winner.prize_description or comp.get("prize_description"),
        "announced_at": datetime.now(timezone.utc).isoformat(),
        "is_automatic": False
    }
    await db.winners.insert_one(winner_doc)
    
    await db.competitions.update_one(
        {"competition_id": winner.competition_id},
        {"$set": {"winner_id": winner.user_id, "winner_ticket": winner.ticket_number, "status": "completed"}}
    )
    
    return winner_doc

@api_router.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    total_users = await db.users.count_documents({})
    total_competitions = await db.competitions.count_documents({})
    active_competitions = await db.competitions.count_documents({"status": "active"})
    total_tickets = await db.tickets.count_documents({})
    
    return {
        "total_users": total_users,
        "total_competitions": total_competitions,
        "active_competitions": active_competitions,
        "total_tickets": total_tickets
    }

# ==================== ANALYTICS ====================

@api_router.get("/stats")
async def get_public_stats():
    """Get public statistics for homepage"""
    winners_count = await db.winners.count_documents({})
    users_count = await db.users.count_documents({})
    tickets_count = await db.tickets.count_documents({})
    
    return {
        "winners": winners_count,
        "users": users_count,
        "tickets": tickets_count
    }

@api_router.get("/activity/recent")
async def get_recent_activity():
    """Get recent activity for live ticker (purchases, winners)"""
    activities = []
    
    # Get recent ticket purchases (last 10)
    recent_tickets = await db.tickets.find(
        {}, 
        {"_id": 0, "user_id": 1, "competition_id": 1, "purchased_at": 1}
    ).sort("purchased_at", -1).limit(10).to_list(10)
    
    for ticket in recent_tickets:
        user = await db.users.find_one({"user_id": ticket["user_id"]}, {"_id": 0, "username": 1})
        comp = await db.competitions.find_one({"competition_id": ticket["competition_id"]}, {"_id": 0, "title": 1})
        if user and comp:
            activities.append({
                "type": "purchase",
                "username": user.get("username", "Anonim")[:15],
                "message": f"a rezervat loc la {comp.get('title', 'competiție')[:25]}",
                "time": ticket.get("purchased_at", "")
            })
    
    # Get recent winners (last 5)
    recent_winners = await db.winners.find(
        {},
        {"_id": 0, "user_id": 1, "competition_id": 1, "created_at": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    for winner in recent_winners:
        user = await db.users.find_one({"user_id": winner["user_id"]}, {"_id": 0, "username": 1})
        comp = await db.competitions.find_one({"competition_id": winner["competition_id"]}, {"_id": 0, "title": 1, "prize_description": 1})
        if user and comp:
            activities.append({
                "type": "winner",
                "username": user.get("username", "Câștigător")[:15],
                "message": f"a câștigat {comp.get('prize_description', comp.get('title', '')[:25])}!",
                "time": winner.get("created_at", "")
            })
    
    # Sort by time and return
    activities.sort(key=lambda x: x.get("time", ""), reverse=True)
    return activities[:15]

# ==================== SITE SETTINGS (TikTok LIVE, etc.) ====================

@api_router.get("/settings/tiktok-live")
async def get_tiktok_live_status():
    """Get TikTok LIVE status (public endpoint)"""
    settings = await db.site_settings.find_one({"setting_id": "tiktok_live"})
    if not settings:
        return {"is_live": False, "tiktok_url": "https://www.tiktok.com/@zektrix.uk"}
    return {
        "is_live": settings.get("is_live", False),
        "tiktok_url": settings.get("tiktok_url", "https://www.tiktok.com/@zektrix.uk")
    }

@api_router.post("/admin/settings/tiktok-live")
async def set_tiktok_live_status(is_live: bool, tiktok_url: Optional[str] = None, admin: dict = Depends(get_admin_user)):
    """Toggle TikTok LIVE status (admin only)"""
    update_data = {"is_live": is_live, "updated_at": datetime.now(timezone.utc).isoformat()}
    if tiktok_url:
        update_data["tiktok_url"] = tiktok_url
    
    await db.site_settings.update_one(
        {"setting_id": "tiktok_live"},
        {"$set": update_data},
        upsert=True
    )
    
    return {"success": True, "is_live": is_live, "message": f"TikTok LIVE {'activat' if is_live else 'dezactivat'}"}

@api_router.get("/settings/featured-competition")
async def get_featured_competition():
    """Get the featured/recommended competition for homepage"""
    setting = await db.site_settings.find_one({"setting_id": "featured_competition"})
    comp_id = setting.get("competition_id") if setting else None
    if comp_id:
        comp = await db.competitions.find_one({"competition_id": comp_id, "status": "active"}, {"_id": 0})
        if comp:
            return {"competition": comp}
    return {"competition": None}

@api_router.post("/admin/settings/featured-competition")
async def set_featured_competition(competition_id: str, admin: dict = Depends(get_admin_user)):
    """Set the featured/recommended competition (admin only)"""
    comp = await db.competitions.find_one({"competition_id": competition_id})
    if not comp:
        raise HTTPException(404, "Competition not found")
    await db.site_settings.update_one(
        {"setting_id": "featured_competition"},
        {"$set": {"competition_id": competition_id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"success": True, "competition_id": competition_id, "title": comp.get("title")}


@api_router.get("/admin/analytics")
async def get_analytics(admin: dict = Depends(get_admin_user)):
    """Get comprehensive analytics for admin dashboard - optimized"""
    import asyncio
    
    # Run all independent queries in parallel
    counts_task = asyncio.gather(
        db.users.count_documents({}),
        db.tickets.count_documents({}),
        db.competitions.count_documents({}),
        db.competitions.count_documents({"status": "active"}),
        db.competitions.count_documents({"status": "completed"}),
        db.winners.count_documents({}),
        db.referrals.count_documents({"status": "completed"})
    )
    
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    # Revenue aggregation pipeline (much faster than loading all docs)
    revenue_pipeline = [
        {"$match": {"status": "completed", "amount": {"$gt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_task = db.transactions.aggregate(revenue_pipeline).to_list(1)
    
    # Revenue by day pipeline
    revenue_day_pipeline = [
        {"$match": {"status": "completed", "amount": {"$gt": 0}, "created_at": {"$gte": thirty_days_ago}}},
        {"$addFields": {"day": {"$substr": ["$created_at", 0, 10]}}},
        {"$group": {"_id": "$day", "revenue": {"$sum": "$amount"}}},
        {"$sort": {"_id": 1}}
    ]
    revenue_day_task = db.transactions.aggregate(revenue_day_pipeline).to_list(30)
    
    # Top competitions
    top_comps_task = db.competitions.find({}, {"_id": 0, "title": 1, "sold_tickets": 1, "max_tickets": 1, "ticket_price": 1}).sort("sold_tickets", -1).limit(10).to_list(10)
    
    # User growth
    user_growth_pipeline = [
        {"$match": {"created_at": {"$gte": thirty_days_ago}}},
        {"$addFields": {"day": {"$substr": ["$created_at", 0, 10]}}},
        {"$group": {"_id": "$day", "users": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    user_growth_task = db.users.aggregate(user_growth_pipeline).to_list(30)
    
    # Await all in parallel
    counts, revenue_result, revenue_by_day_result, competitions, user_growth_result = await asyncio.gather(
        counts_task, revenue_task, revenue_day_task, top_comps_task, user_growth_task
    )
    
    total_users, total_tickets, total_competitions, active_competitions, completed_competitions, total_winners, total_referrals = counts
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    avg_tickets = total_tickets / total_users if total_users > 0 else 0
    
    revenue_by_day_list = [{"date": r["_id"], "revenue": r["revenue"]} for r in revenue_by_day_result]
    top_competitions = [
        {"title": c["title"], "sold": c["sold_tickets"], "max": c["max_tickets"], "revenue": c["sold_tickets"] * c["ticket_price"]}
        for c in competitions
    ]
    user_growth_list = [{"date": u["_id"], "users": u["users"]} for u in user_growth_result]
    
    return {
        "total_revenue": round(total_revenue, 2),
        "total_users": total_users,
        "total_tickets": total_tickets,
        "total_competitions": total_competitions,
        "active_competitions": active_competitions,
        "completed_competitions": completed_competitions,
        "total_winners": total_winners,
        "avg_tickets_per_user": round(avg_tickets, 2),
        "revenue_by_day": revenue_by_day_list,
        "top_competitions": top_competitions,
        "user_growth": user_growth_list,
        "total_referrals": total_referrals,
        "referral_bonus_paid": total_referrals * 5
    }

# ==================== REFERRAL SYSTEM ====================

def generate_referral_code(user_id: str) -> str:
    """Generate unique referral code"""
    return f"ZEK{user_id[-6:].upper()}"

@api_router.get("/referral/my-code")
async def get_my_referral_code(current_user: dict = Depends(get_current_user)):
    """Get user's referral code"""
    referral_code = current_user.get("referral_code")
    if not referral_code:
        referral_code = generate_referral_code(current_user["user_id"])
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": {"referral_code": referral_code}}
        )
    
    # Get referral stats
    referrals = await db.referrals.find(
        {"referrer_id": current_user["user_id"]},
        {"_id": 0}
    ).to_list(100)
    
    completed = len([r for r in referrals if r["status"] == "completed"])
    pending = len([r for r in referrals if r["status"] == "pending"])
    total_earned = completed * 5  # £5 per successful referral
    
    return {
        "referral_code": referral_code,
        "referral_link": f"https://zektrix.uk/register?ref={referral_code}",
        "total_referrals": len(referrals),
        "completed_referrals": completed,
        "pending_referrals": pending,
        "total_earned": total_earned,
        "bonus_per_referral": 5
    }

@api_router.get("/referral/my-referrals")
async def get_my_referrals(current_user: dict = Depends(get_current_user)):
    """Get list of user's referrals"""
    referrals = await db.referrals.find(
        {"referrer_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get referred user names
    for ref in referrals:
        referred_user = await db.users.find_one({"user_id": ref["referred_id"]}, {"_id": 0, "username": 1})
        ref["referred_username"] = referred_user.get("username", "Unknown") if referred_user else "Unknown"
    
    return referrals

@api_router.post("/referral/apply")
async def apply_referral_code(referral: ReferralCreate, current_user: dict = Depends(get_current_user)):
    """Apply a referral code (for new users)"""
    # Check if user already used a referral
    existing = await db.referrals.find_one({"referred_id": current_user["user_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Already used a referral code")
    
    # Check if user has any purchases (must be new user)
    purchases = await db.transactions.count_documents({"user_id": current_user["user_id"]})
    if purchases > 0:
        raise HTTPException(status_code=400, detail="Referral code can only be used by new users")
    
    # Find referrer by code
    referrer = await db.users.find_one({"referral_code": referral.referrer_code.upper()}, {"_id": 0})
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    if referrer["user_id"] == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot use your own referral code")
    
    # Create pending referral
    referral_doc = {
        "referral_id": f"ref_{uuid.uuid4().hex[:12]}",
        "referrer_id": referrer["user_id"],
        "referred_id": current_user["user_id"],
        "status": "pending",  # Will become 'completed' after first purchase
        "bonus_amount": 5.0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.referrals.insert_one(referral_doc)
    
    return {"message": "Referral code applied! You'll both receive £5 bonus after your first purchase."}

@api_router.get("/referral/validate/{code}")
async def validate_referral_code(code: str):
    """Validate a referral code (public endpoint for registration)"""
    referrer = await db.users.find_one({"referral_code": code.upper()}, {"_id": 0, "username": 1})
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    return {"valid": True, "referrer_username": referrer.get("username", "Unknown")}

# ==================== SOCIAL SHARING ====================

@api_router.get("/share/competition/{competition_id}")
async def get_share_data(competition_id: str):
    """Get shareable data for a competition"""
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    share_url = f"https://zektrix.uk/competitions/{competition_id}"
    share_text = f"Participa la competitia '{comp['title']}' si castiga {comp.get('prize_description', 'premii incredibile')}! Bilete de la doar £{comp['ticket_price']}"
    
    return {
        "title": comp["title"],
        "description": comp.get("prize_description", comp["description"]),
        "image_url": comp.get("image_url"),
        "share_url": share_url,
        "share_text": share_text,
        "twitter_url": f"https://twitter.com/intent/tweet?text={share_text}&url={share_url}",
        "facebook_url": f"https://www.facebook.com/sharer/sharer.php?u={share_url}",
        "whatsapp_url": f"https://wa.me/?text={share_text} {share_url}"
    }

@api_router.get("/share/winner/{winner_id}")
async def get_winner_share_data(winner_id: str):
    """Get shareable data for a winner announcement"""
    winner = await db.winners.find_one({"winner_id": winner_id}, {"_id": 0})
    if not winner:
        raise HTTPException(status_code=404, detail="Winner not found")
    
    share_url = "https://zektrix.uk/winners"
    share_text = f"[CASTIGATOR] {winner['username']} a castigat '{winner['competition_title']}'! Tu poti fi urmatorul castigator la Zektrix UK!"
    
    return {
        "winner_username": winner["username"],
        "competition_title": winner["competition_title"],
        "prize": winner.get("prize_description"),
        "share_url": share_url,
        "share_text": share_text,
        "twitter_url": f"https://twitter.com/intent/tweet?text={share_text}&url={share_url}",
        "facebook_url": f"https://www.facebook.com/sharer/sharer.php?u={share_url}",
        "whatsapp_url": f"https://wa.me/?text={share_text} {share_url}"
    }

# ==================== PUSH NOTIFICATIONS ====================

@api_router.post("/notifications/subscribe")
async def subscribe_push_notifications(
    subscription: PushSubscription,
    current_user: dict = Depends(get_current_user)
):
    """Subscribe user to push notifications"""
    user_id = current_user["user_id"]
    
    # Store subscription in database
    await db.push_subscriptions.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "endpoint": subscription.endpoint,
                "keys": subscription.keys,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Update user preferences
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"push_notifications_enabled": True}}
    )
    
    return {"success": True, "message": "Subscribed to push notifications"}

@api_router.delete("/notifications/unsubscribe")
async def unsubscribe_push_notifications(current_user: dict = Depends(get_current_user)):
    """Unsubscribe user from push notifications"""
    user_id = current_user["user_id"]
    
    await db.push_subscriptions.delete_one({"user_id": user_id})
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"push_notifications_enabled": False}}
    )
    
    return {"success": True, "message": "Unsubscribed from push notifications"}

@api_router.get("/notifications/status")
async def get_notification_status(current_user: dict = Depends(get_current_user)):
    """Get user's notification subscription status"""
    user_id = current_user["user_id"]
    
    subscription = await db.push_subscriptions.find_one({"user_id": user_id})
    user = await db.users.find_one({"user_id": user_id})
    
    return {
        "subscribed": subscription is not None,
        "push_enabled": user.get("push_notifications_enabled", False) if user else False
    }

# Helper function to send notifications when competition reaches threshold
async def check_and_send_competition_alerts(competition_id: str, sold_tickets: int, max_tickets: int):
    """Send push + email notifications when competition reaches milestones"""
    percentage = (sold_tickets / max_tickets) * 100 if max_tickets > 0 else 0
    
    milestones = [
        (70, 75, "70"),
        (80, 85, "80"),
        (90, 95, "90"),
    ]
    
    for low, high, label in milestones:
        if low <= percentage < high:
            comp = await db.competitions.find_one({"competition_id": competition_id})
            if not comp:
                return
            
            alert_key = f"alert_{label}_{competition_id}"
            if await db.settings.find_one({"key": alert_key}):
                return
            
            await db.settings.update_one(
                {"key": alert_key},
                {"$set": {"sent_at": datetime.now(timezone.utc).isoformat()}},
                upsert=True
            )
            
            remaining = max_tickets - sold_tickets
            title = comp.get("title", "Competiție")
            
            # Push notifications to participants
            await notify_competition_participants_push(
                competition_id,
                f"{title} - {int(percentage)}% ocupat!",
                f"Doar {remaining} locuri rămase! Grăbește-te!",
                f"https://zektrix.uk/competitions/{competition_id}"
            )
            
            # Personalized emails to participants
            tickets = await db.tickets.find(
                {"competition_id": competition_id},
                {"_id": 0, "user_id": 1}
            ).to_list(10000)
            user_ids = list(set(t["user_id"] for t in tickets))
            
            if user_ids:
                users = await db.users.find(
                    {"user_id": {"$in": user_ids}, "email_unsubscribed": {"$ne": True}},
                    {"_id": 0, "user_id": 1, "email": 1, "first_name": 1, "username": 1}
                ).to_list(10000)
                
                for user in users:
                    try:
                        name = user.get("first_name") or user.get("username", "Utilizator")
                        comp_link = f"https://zektrix.uk/competitions/{competition_id}"
                        image_url = comp.get("image_url", "")
                        prize = comp.get("prize_description") or title
                        
                        img_html = f'<img src="{image_url}" alt="{title}" style="width:100%;height:180px;object-fit:cover;display:block;border-radius:12px 12px 0 0;" />' if image_url else ""
                        
                        email_html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#030014;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
<table cellpadding="0" cellspacing="0" style="width:100%;background:#030014;"><tr><td style="padding:30px 16px;">
<table cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;width:100%;">
<tr><td style="text-align:center;padding-bottom:20px;">
    <h1 style="margin:0;font-size:28px;font-weight:900;"><span style="color:#8b5cf6;">ZEKTRIX</span><span style="color:#fff;">.UK</span></h1>
</td></tr>
<tr><td style="padding-bottom:16px;">
    <table cellpadding="0" cellspacing="0" style="width:100%;background:#0d0b1a;border:1px solid #ef444440;border-radius:12px;overflow:hidden;">
        <tr><td style="background:linear-gradient(135deg,#ef4444,#dc2626);padding:14px 20px;text-align:center;">
            <p style="color:#fff;margin:0;font-size:14px;font-weight:700;">&#128293; COMPETITIA TA SE APROPIE DE EXTRAGERE!</p>
        </td></tr>
        <tr><td style="padding:20px;">
            <p style="color:#9ca3af;margin:0 0 8px 0;font-size:14px;">Salut <strong style="color:#fff;">{name}</strong>,</p>
            <p style="color:#9ca3af;margin:0;font-size:13px;line-height:1.5;">Competitia la care participi este <strong style="color:#ef4444;">{int(percentage)}% ocupata</strong>! Mai sunt doar <strong style="color:#fbbf24;">{remaining} locuri</strong> ramase.</p>
        </td></tr>
    </table>
</td></tr>
<tr><td style="padding-bottom:16px;">
    <a href="{comp_link}" style="text-decoration:none;display:block;">
    <table cellpadding="0" cellspacing="0" style="width:100%;background:#0d0b1a;border:1px solid #1e1b3a;border-radius:12px;overflow:hidden;">
        <tr><td>{img_html}</td></tr>
        <tr><td style="padding:16px;">
            <p style="color:#fff;margin:0 0 6px 0;font-size:17px;font-weight:700;">{title}</p>
            <p style="color:#fbbf24;margin:0;font-size:13px;">Premiu: {prize}</p>
            <table cellpadding="0" cellspacing="0" style="width:100%;margin-top:12px;"><tr>
                <td style="background:#1a1730;border-radius:6px;height:8px;overflow:hidden;">
                    <div style="background:linear-gradient(90deg,#ef4444,#f97316);height:8px;width:{int(percentage)}%;border-radius:6px;"></div>
                </td>
            </tr></table>
            <p style="color:#6b7280;margin:8px 0 0 0;font-size:11px;"><span style="color:#ef4444;font-weight:700;">{int(percentage)}%</span> ocupat &bull; <span style="color:#10b981;">{remaining} locuri ramase</span></p>
        </td></tr>
    </table>
    </a>
</td></tr>
<tr><td style="text-align:center;padding:10px 0 20px 0;">
    <a href="{comp_link}" style="display:inline-block;background:linear-gradient(135deg,#8b5cf6,#7c3aed);color:#fff;text-decoration:none;padding:14px 40px;border-radius:50px;font-weight:700;font-size:14px;">VEZI COMPETITIA &#8594;</a>
</td></tr>
<tr><td style="text-align:center;padding-top:20px;border-top:1px solid #1e1b3a;">
    <p style="color:#4b5563;font-size:9px;margin:0;">&#169; 2026 Zektrix UK Ltd &bull; <a href="https://zektrix.uk/unsubscribe/{user.get('user_id','')}" style="color:#6b7280;">Dezabonare</a></p>
</td></tr>
</table></td></tr></table></body></html>'''
                        
                        resend.Emails.send({
                            "from": SENDER_EMAIL,
                            "to": [user["email"]],
                            "subject": f"[ZEKTRIX] {title} - Doar {remaining} locuri ramase! &#128293;",
                            "html": email_html
                        })
                        await asyncio.sleep(0.2)
                    except Exception as e:
                        logger.error(f"Failed to send milestone email to {user.get('email')}: {e}")
            
            logger.info(f"Competition {competition_id} reached {label}% - alerts sent")

# Lucky Wheel removed

# ==================== FLASH SALES ====================

@api_router.get("/competitions/flash-sales")
async def get_flash_sales():
    """Get active flash sale competitions"""
    now = datetime.now(timezone.utc)
    
    flash_sales = await db.competitions.find({
        "flash_sale.active": True,
        "flash_sale.end_time": {"$gt": now.isoformat()},
        "status": "active"
    }, {"_id": 0}).to_list(100)
    
    return flash_sales

@api_router.post("/admin/flash-sale")
async def create_flash_sale(data: FlashSaleCreate, admin: dict = Depends(get_admin_user)):
    """Create a flash sale for a competition"""
    comp = await db.competitions.find_one({"competition_id": data.competition_id})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    end_time = datetime.now(timezone.utc) + timedelta(hours=data.duration_hours)
    original_price = comp.get("ticket_price", 0)
    flash_price = round(original_price * (1 - data.discount_percent / 100), 2)
    
    await db.competitions.update_one(
        {"competition_id": data.competition_id},
        {"$set": {
            "flash_sale": {
                "active": True,
                "discount_percent": data.discount_percent,
                "original_price": original_price,
                "flash_price": flash_price,
                "end_time": end_time.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }}
    )
    
    return {"success": True, "flash_sale_ends": end_time.isoformat(), "flash_price": flash_price}

@api_router.delete("/admin/flash-sale/{competition_id}")
async def end_flash_sale(competition_id: str, admin: dict = Depends(get_admin_user)):
    """End a flash sale early"""
    await db.competitions.update_one(
        {"competition_id": competition_id},
        {"$unset": {"flash_sale": ""}}
    )
    return {"success": True}

# ==================== LIVE CHAT / FAQ BOT ====================

FAQ_RESPONSES = {
    "cum functioneaza": "Inregistrezi un cont, adaugi fonduri in portofel, apoi cumperi bilete la competitiile dorite. Fiecare bilet iti ofera o sansa de a primi premiul!",
    "cum cumpar bilete": "1) Alege o competitie 2) Raspunde la intrebarea de calificare 3) Selecteaza cate bilete vrei 4) Plateste cu portofelul sau cardul",
    "cand sunt extragerile": "Extragerile au loc cand toate biletele sunt vandute (Premiu Instant) sau la data specificata pe pagina competitiei.",
    "cum primesc premiul": "Te contactam prin email in 24-48 ore de la extragere cu instructiunile de revendicare a premiului.",
    "este gratuit": "Inregistrarea este gratuita! Poti participa si prin intrare postala gratuita - vezi detaliile pe fiecare competitie.",
    "contact": "Email: contact@x67digital.com | TikTok: @zektrix.uk",
    "cum depun bani": "Mergi in Panou -> Portofel -> Adauga Fonduri. Acceptam Visa, Mastercard, Apple Pay si Google Pay prin Viva Payments.",
    "castig": "Preminatii sunt selectati aleatoriu din toate biletele valide. Verifica rezultatele pe pagina Premianti!",
    "roata norocului": "Invarte roata zilnic pentru sansa de a castiga bani, bilete gratuite sau bonusuri! O singura invartire pe zi.",
}

# Chat WebSocket Manager
class ChatManager:
    def __init__(self):
        self.user_connections: Dict[str, WebSocket] = {}
        self.admin_connections: List[WebSocket] = []

    async def connect_user(self, ws: WebSocket, user_id: str):
        await ws.accept()
        self.user_connections[user_id] = ws

    def disconnect_user(self, user_id: str):
        self.user_connections.pop(user_id, None)

    async def connect_admin(self, ws: WebSocket):
        await ws.accept()
        self.admin_connections.append(ws)

    def disconnect_admin(self, ws: WebSocket):
        if ws in self.admin_connections:
            self.admin_connections.remove(ws)

    async def send_to_user(self, user_id: str, message: dict):
        ws = self.user_connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect_user(user_id)

    async def send_to_admins(self, message: dict):
        dead = []
        for ws in self.admin_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_admin(ws)

chat_manager = ChatManager()

async def verify_ws_token(token: str):
    """Verify JWT or session token for WebSocket connections"""
    # Try JWT first
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
        if user:
            return user
    except Exception:
        pass
    
    # Try session token (Google Auth)
    try:
        session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
        if session:
            user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
            return user
    except Exception:
        pass
    
    return None

@app.websocket("/ws/chat/user")
async def ws_chat_user(websocket: WebSocket, token: str = Query(...)):
    user = await verify_ws_token(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    user_id = user["user_id"]
    await chat_manager.connect_user(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                msg_text = data.get("message", "").strip()
                if not msg_text:
                    continue
                # Check FAQ first
                faq_response = None
                for keyword, response in FAQ_RESPONSES.items():
                    if keyword in msg_text.lower():
                        faq_response = response
                        break
                if faq_response:
                    await chat_manager.send_to_user(user_id, {
                        "type": "faq_response",
                        "message": faq_response,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                else:
                    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
                    msg_doc = {
                        "message_id": msg_id,
                        "user_id": user_id,
                        "username": user.get("username", user.get("first_name", "User")),
                        "user_email": user.get("email", ""),
                        "message": msg_text,
                        "status": "pending",
                        "admin_reply": None,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.chat_messages.insert_one({**msg_doc})
                    await chat_manager.send_to_user(user_id, {
                        "type": "message_sent",
                        "message_id": msg_id,
                        "message": msg_text,
                        "timestamp": msg_doc["created_at"]
                    })
                    await chat_manager.send_to_admins({
                        "type": "new_message",
                        "message_id": msg_id,
                        "user_id": user_id,
                        "username": msg_doc["username"],
                        "user_email": msg_doc["user_email"],
                        "message": msg_text,
                        "status": "pending",
                        "created_at": msg_doc["created_at"]
                    })
    except WebSocketDisconnect:
        chat_manager.disconnect_user(user_id)

@app.websocket("/ws/chat/admin")
async def ws_chat_admin(websocket: WebSocket, token: str = Query(...)):
    admin = await verify_ws_token(token)
    if not admin or admin.get("role") != "admin":
        await websocket.close(code=4001, reason="Unauthorized")
        return
    await chat_manager.connect_admin(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "reply":
                msg_id = data.get("message_id")
                reply_text = data.get("reply", "").strip()
                if not msg_id or not reply_text:
                    continue
                original = await db.chat_messages.find_one({"message_id": msg_id}, {"_id": 0})
                if not original:
                    continue
                await db.chat_messages.update_one(
                    {"message_id": msg_id},
                    {"$set": {
                        "status": "replied",
                        "admin_reply": reply_text,
                        "replied_at": datetime.now(timezone.utc).isoformat(),
                        "replied_by": admin.get("username", "Admin")
                    }}
                )
                await chat_manager.send_to_user(original["user_id"], {
                    "type": "admin_reply",
                    "message_id": msg_id,
                    "reply": reply_text,
                    "replied_by": admin.get("username", "Admin"),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                await chat_manager.send_to_admins({
                    "type": "reply_sent",
                    "message_id": msg_id,
                    "reply": reply_text,
                    "replied_by": admin.get("username", "Admin")
                })
    except WebSocketDisconnect:
        chat_manager.disconnect_admin(websocket)

# =============================================
# AI CHATBOT + PUSH NOTIFICATIONS
# =============================================

ZEKTRIX_SYSTEM_PROMPT = """Ești asistentul AI al platformei Zektrix.UK - o platformă de competiții online cu premii din Marea Britanie.

INFORMAȚII DESPRE ZEKTRIX.UK:
- Platformă de competiții online unde utilizatorii cumpără locuri (bilete) pentru a câștiga premii valoroase
- Premii: mașini (Tesla Model 3, AMG GLE 63S), cash (£500-£10,000), vacanțe, tech (iPhone, Apple Watch, PS5)
- Moneda: GBP (£ - lire sterline)
- Plăți securizate prin Viva Payments (card bancar)
- Există și competiții GRATUITE (un loc per utilizator)

CUM FUNCȚIONEAZĂ:
1. Utilizatorul creează un cont gratuit pe zektrix.uk
2. Alege o competiție care îi place
3. Selectează numărul de locuri dorite
4. Răspunde la o întrebare de calificare (obligatorie legal)
5. Plătește cu cardul prin Viva Payments
6. Când toate locurile sunt vândute sau la data extragerii, se alege câștigătorul

TIPURI DE COMPETIȚII:
- AUTODRAW (instant_win): Câștigătorul este ales automat când se vând toate locurile
- DRAW: Extragere manuală la o dată specificată de admin

CONT ȘI DASHBOARD:
- "Locurile Mele" - vezi toate biletele cumpărate
- "Istoric" - istoricul tranzacțiilor
- "Contul Meu" - editează profilul (nume, email, telefon, adresă)

PREȚURI:
- Biletele variază de la £0.49 la £2.98 per loc
- Competițiile gratuite nu necesită plată
- Poți cumpăra mai multe locuri pentru șanse mai mari

REGULI IMPORTANTE:
- Vârsta minimă: 18 ani
- Un singur loc per utilizator la competițiile gratuite
- Intrare poștală gratuită disponibilă (conform legii UK)
- Trebuie să răspunzi corect la întrebarea de calificare

CONTACT:
- Email: support@zektrix.uk
- WhatsApp: +40 730 268 067
- Chat live pe site

REGULI PENTRU TINE:
1. Răspunde DOAR în limba română
2. Fii prietenos, concis și util
3. Dacă nu știi răspunsul exact, spune sincer și sugerează contactarea suportului live
4. Când utilizatorul are o problemă complexă (plată eșuată, cont blocat, premiu neclamat), sugerează să vorbească cu un operator live
5. NU inventa informații pe care nu le ai
6. Răspunsurile să fie scurte (max 2-3 propoziții) dacă nu e nevoie de mai mult"""

class AIChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@api_router.post("/chat/ai")
async def ai_chat(req: AIChatRequest, current_user: dict = Depends(get_current_user)):
    """AI chatbot endpoint - answers questions about Zektrix"""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="AI service unavailable")
    
    session_id = req.session_id or f"ai_{current_user['user_id']}_{uuid.uuid4().hex[:8]}"
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=ZEKTRIX_SYSTEM_PROMPT
        ).with_model("gemini", "gemini-2.5-flash")
        
        response = await chat.send_message(UserMessage(text=req.message))
        
        needs_escalation = any(kw in response.lower() for kw in [
            "operator live", "asistență live", "contactează suportul", 
            "vorbește cu un operator", "echipa noastră"
        ])
        
        return {
            "response": response,
            "session_id": session_id,
            "needs_escalation": needs_escalation
        }
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return {
            "response": "Îmi pare rău, am o problemă tehnică momentan. Te rog să folosești chat-ul live pentru asistență.",
            "session_id": session_id,
            "needs_escalation": True
        }

@api_router.get("/push/vapid-key")
async def get_vapid_key():
    """Return VAPID public key for push notification subscription"""
    return {"public_key": VAPID_PUBLIC_KEY}

@api_router.post("/push/subscribe")
async def push_subscribe(subscription: PushSubscription, current_user: dict = Depends(get_current_user)):
    """Subscribe any user to push notifications"""
    await db.push_subscriptions.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "user_id": current_user["user_id"],
            "role": current_user.get("role", "user"),
            "endpoint": subscription.endpoint,
            "keys": subscription.keys,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    return {"message": "Subscribed to push notifications"}

@api_router.get("/push/status")
async def push_status(current_user: dict = Depends(get_current_user)):
    """Check if user has an active push subscription"""
    sub = await db.push_subscriptions.find_one({"user_id": current_user["user_id"]}, {"_id": 0, "endpoint": 1})
    return {"subscribed": bool(sub)}

@api_router.post("/push/unsubscribe")
async def push_unsubscribe(current_user: dict = Depends(get_current_user)):
    """Unsubscribe from push notifications"""
    await db.push_subscriptions.delete_one({"user_id": current_user["user_id"]})
    return {"message": "Unsubscribed"}

@api_router.post("/push/test")
async def test_push_notification(current_user: dict = Depends(get_admin_user)):
    """Send a test push notification to verify setup works"""
    
    subs = await db.push_subscriptions.find({"user_id": current_user["user_id"]}, {"_id": 0}).to_list(5)
    if not subs:
        raise HTTPException(status_code=404, detail="Nu ai nicio subscriptie push activa. Activeaza mai intai notificarile.")
    
    sent = 0
    errors = []
    for sub in subs:
        try:
            result = await send_web_push(
                sub,
                {"title": "Test Zektrix", "body": "Notificarile push functioneaza!", "url": "https://zektrix.uk/admin"}
            )
            if result:
                sent += 1
            else:
                errors.append("Push failed silently")
        except Exception as e:
            err_str = str(e)
            errors.append(err_str[:100])
            if "410" in err_str or "404" in err_str:
                await db.push_subscriptions.delete_one({"endpoint": sub["endpoint"]})
    
    if sent > 0:
        return {"success": True, "message": f"Notificare de test trimisa!"}
    else:
        raise HTTPException(status_code=400, detail=f"Nu s-a putut trimite: {'; '.join(errors)}")


async def notify_admins_live_chat(user_name: str, user_email: str, message: str):
    """Send push notification + email to all admins when user requests live chat"""
    # 1. Push notifications to admins
    await _notify_admins_push(db, "Asistenta Live Solicitata", f"{user_name}: {message[:100]}", "https://zektrix.uk/admin")
    
    # 2. Email notification
    if RESEND_API_KEY:
        try:
            admins = await db.users.find({"role": "admin"}, {"_id": 0, "email": 1}).to_list(10)
            admin_emails = [a["email"] for a in admins if a.get("email")]
            if admin_emails:
                resend.Emails.send({
                    "from": SENDER_EMAIL,
                    "to": admin_emails,
                    "subject": f"🔔 Asistență Live - {user_name}",
                    "html": f"""
                    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;background:#1a1a2e;color:white;border-radius:12px;">
                        <h2 style="color:#8b5cf6;">Cerere Asistență Live</h2>
                        <p><strong>Utilizator:</strong> {user_name}</p>
                        <p><strong>Email:</strong> {user_email}</p>
                        <p><strong>Mesaj:</strong> {message[:200]}</p>
                        <a href="https://zektrix.uk/admin" style="display:inline-block;margin-top:15px;padding:12px 24px;background:#8b5cf6;color:white;text-decoration:none;border-radius:8px;font-weight:bold;">Deschide Admin Panel</a>
                    </div>
                    """
                })
        except Exception as e:
            logger.error(f"Email notification failed: {e}")

@api_router.post("/chat/escalate")
async def escalate_to_live(req: AIChatRequest, current_user: dict = Depends(get_current_user)):
    """Escalate from AI chat to live chat - notifies admins"""
    user_name = current_user.get("username", current_user.get("first_name", "Utilizator"))
    user_email = current_user.get("email", "")
    
    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    msg_doc = {
        "message_id": msg_id,
        "user_id": current_user["user_id"],
        "username": user_name,
        "user_email": user_email,
        "message": f"[ESCALAT DIN AI] {req.message}",
        "status": "pending",
        "admin_reply": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one({**msg_doc})
    
    await chat_manager.send_to_admins({
        "type": "new_message",
        "message_id": msg_id,
        "user_id": current_user["user_id"],
        "username": user_name,
        "user_email": user_email,
        "message": f"[ESCALAT DIN AI] {req.message}",
        "status": "pending",
        "created_at": msg_doc["created_at"]
    })
    
    await notify_admins_live_chat(user_name, user_email, req.message)
    
    return {"message": "Escalated to live chat", "message_id": msg_id}

@api_router.get("/chat/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    """Get user's chat history"""
    messages = await db.chat_messages.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("created_at", 1).to_list(50)
    return messages

@api_router.post("/chat/message")
async def chat_message(msg: ChatMessage, current_user: dict = Depends(get_current_user)):
    """Process chat message - returns FAQ response or forwards to support"""
    user_message = msg.message.lower().strip()
    
    # Check for FAQ matches
    for keyword, response in FAQ_RESPONSES.items():
        if keyword in user_message:
            return {
                "type": "faq",
                "response": response,
                "matched_keyword": keyword
            }
    
    # No FAQ match - save for support review
    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    msg_doc = {
        "message_id": msg_id,
        "user_id": current_user["user_id"],
        "username": current_user.get("username", "Unknown"),
        "user_email": current_user.get("email", ""),
        "message": msg.message,
        "status": "pending",
        "admin_reply": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_messages.insert_one({**msg_doc})
    
    # Notify admin via WebSocket
    await chat_manager.send_to_admins({
        "type": "new_message",
        "message_id": msg_id,
        "user_id": current_user["user_id"],
        "username": msg_doc["username"],
        "user_email": msg_doc["user_email"],
        "message": msg.message,
        "status": "pending",
        "created_at": msg_doc["created_at"]
    })
    
    return {
        "type": "support",
        "response": "Mesajul tau a fost trimis echipei de suport. Vei primi un raspuns in curand!",
        "ticket_created": True
    }

@api_router.get("/chat/faq")
async def get_faq_list():
    """Get list of FAQ topics"""
    return [
        {"question": "Cum funcționează Zektrix?", "keyword": "cum funcționează"},
        {"question": "Cum cumpăr bilete?", "keyword": "cum cumpăr bilete"},
        {"question": "Când sunt extragerile?", "keyword": "când sunt extragerile"},
        {"question": "Cum primesc premiul?", "keyword": "cum primesc premiul"},
        {"question": "Este gratuit să particip?", "keyword": "este gratuit"},
        {"question": "Cum depun bani?", "keyword": "cum depun bani"},
        {"question": "Contact & Suport", "keyword": "contact"},
        {"question": "Roata Norocului", "keyword": "roata norocului"},
    ]

@api_router.get("/admin/chat/messages")
async def get_pending_messages(admin: dict = Depends(get_admin_user), status: Optional[str] = None):
    """Get all chat messages with user info - optimized"""
    query = {}
    if status:
        query["status"] = status
    
    messages = await db.chat_messages.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    
    if messages:
        # Batch fetch all users at once
        user_ids = list(set(m.get("user_id") for m in messages if m.get("user_id")))
        users_list = await db.users.find({"user_id": {"$in": user_ids}}, {"_id": 0, "user_id": 1, "email": 1, "first_name": 1, "last_name": 1}).to_list(len(user_ids))
        users_map = {u["user_id"]: u for u in users_list}
        
        for msg in messages:
            user = users_map.get(msg.get("user_id"))
            if user:
                msg["user_email"] = user.get("email")
                msg["user_first_name"] = user.get("first_name")
                msg["user_last_name"] = user.get("last_name")
    
    return messages

@api_router.put("/admin/chat/{message_id}/status")
async def update_chat_status(message_id: str, request: Request, admin: dict = Depends(get_admin_user)):
    """Update chat message status (pending/replied/resolved)"""
    body = await request.json()
    new_status = body.get("status", "resolved")
    
    result = await db.chat_messages.update_one(
        {"message_id": message_id},
        {"$set": {"status": new_status, "resolved_at": datetime.now(timezone.utc).isoformat(), "resolved_by": admin.get("username", "Admin")}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Status updated", "status": new_status}

@api_router.delete("/admin/chat/{message_id}")
async def delete_chat_message(message_id: str, admin: dict = Depends(get_admin_user)):
    """Delete a chat message/conversation"""
    result = await db.chat_messages.delete_one({"message_id": message_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Conversation deleted"}

class AdminEmailReply(BaseModel):
    message_id: str
    reply: str
    user_email: str

@api_router.post("/admin/chat/reply-email")
async def admin_reply_email(data: AdminEmailReply, admin: dict = Depends(get_admin_user)):
    """Reply to user via email and update chat status"""
    # Update message in DB
    await db.chat_messages.update_one(
        {"message_id": data.message_id},
        {"$set": {
            "status": "replied",
            "admin_reply": data.reply,
            "replied_at": datetime.now(timezone.utc).isoformat(),
            "replied_by": admin.get("username", "Admin"),
            "replied_via": "email"
        }}
    )
    
    # Send email
    try:
        email_html = f"""
        <div style="font-family: Arial; padding: 20px; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); padding: 20px; border-radius: 12px 12px 0 0;">
                <h2 style="color: white; margin: 0;">Zektrix UK - Suport</h2>
            </div>
            <div style="background: #f9fafb; padding: 20px; border-radius: 0 0 12px 12px;">
                <p style="color: #374151;">Răspunsul echipei noastre de suport:</p>
                <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #8b5cf6; margin: 15px 0;">
                    <p style="color: #1f2937; margin: 0;">{data.reply}</p>
                </div>
                <p style="color: #6b7280; font-size: 12px;">Dacă ai nevoie de ajutor suplimentar, nu ezita să ne contactezi.</p>
                <p style="color: #6b7280; font-size: 12px;">Echipa Zektrix UK</p>
            </div>
        </div>
        """
        resend_api_key = os.environ.get("RESEND_API_KEY")
        sender = os.environ.get("SENDER_EMAIL", "Zektrix <noreply@x67digital.com>")
        if resend_api_key:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {resend_api_key}"},
                    json={
                        "from": sender,
                        "to": data.user_email,
                        "subject": "Răspuns de la Suport - Zektrix UK",
                        "html": email_html
                    }
                )
        email_sent = True
    except Exception as e:
        logger.error(f"Failed to send reply email: {e}")
        email_sent = False
    
    # Also notify user via WebSocket if online
    original = await db.chat_messages.find_one({"message_id": data.message_id}, {"_id": 0})
    if original:
        await chat_manager.send_to_user(original["user_id"], {
            "type": "admin_reply",
            "message_id": data.message_id,
            "reply": data.reply,
            "replied_by": admin.get("username", "Admin"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    return {"message": "Reply sent", "email_sent": email_sent}

class AdminChatReply(BaseModel):
    message_id: str
    reply: str

@api_router.post("/admin/chat/reply")
async def admin_reply_to_chat(reply: AdminChatReply, admin: dict = Depends(get_admin_user)):
    """Admin replies to a user chat message"""
    # Find the original message
    original = await db.chat_messages.find_one({"message_id": reply.message_id}, {"_id": 0})
    if not original:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Update message status
    await db.chat_messages.update_one(
        {"message_id": reply.message_id},
        {"$set": {
            "status": "replied",
            "admin_reply": reply.reply,
            "replied_at": datetime.now(timezone.utc).isoformat(),
            "replied_by": admin.get("username", "Admin")
        }}
    )
    
    # Get user to send email
    user = await db.users.find_one({"user_id": original["user_id"]}, {"_id": 0})
    if user and user.get("email"):
        try:
            # Send email notification
            email_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0a0614; padding: 30px; border-radius: 15px;">
                <h1 style="color: #8b5cf6; text-align: center;">Răspuns de la Suport</h1>
                <p style="color: #ffffff;">Salut {user.get('first_name', user.get('username', 'Utilizator'))},</p>
                <p style="color: #9ca3af;">Ai primit un răspuns la mesajul tău:</p>
                <div style="background: #1a1a2e; padding: 15px; border-radius: 10px; margin: 20px 0;">
                    <p style="color: #6b7280; font-size: 12px;">Mesajul tău:</p>
                    <p style="color: #ffffff;">{original['message']}</p>
                </div>
                <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(249, 115, 22, 0.1)); padding: 15px; border-radius: 10px; border: 1px solid #8b5cf6;">
                    <p style="color: #8b5cf6; font-size: 12px;">Răspuns:</p>
                    <p style="color: #ffffff;">{reply.reply}</p>
                </div>
                <p style="color: #9ca3af; margin-top: 30px; text-align: center;">Cu drag,<br><strong style="color: #8b5cf6;">Echipa Zektrix</strong></p>
            </div>
            """
            
            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": [user["email"]],
                "subject": "Răspuns de la Suport - Zektrix",
                "html": email_html
            })
            logger.info(f"Chat reply email sent to {user['email']}")
        except Exception as e:
            logger.error(f"Failed to send chat reply email: {e}")
    
    # Broadcast to user via WebSocket chat
    await chat_manager.send_to_user(original["user_id"], {
        "type": "admin_reply",
        "message_id": reply.message_id,
        "reply": reply.reply,
        "replied_by": admin.get("username", "Admin"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Push notification to user
    await notify_user_push(
        original["user_id"],
        "Răspuns de la Suport",
        f"{reply.reply[:100]}",
        "https://zektrix.uk"
    )
    
    return {"message": "Reply sent successfully", "email_sent": bool(user and user.get("email"))}

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket, "general")
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "general")

@app.websocket("/ws/competition/{competition_id}")
async def competition_websocket(websocket: WebSocket, competition_id: str):
    """WebSocket endpoint for competition-specific updates"""
    channel = f"competition_{competition_id}"
    await ws_manager.connect(websocket, channel)
    try:
        # Send initial data
        comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
        if comp:
            await websocket.send_json({
                "type": "competition_update",
                "sold_tickets": comp["sold_tickets"],
                "max_tickets": comp["max_tickets"],
                "status": comp["status"]
            })
        
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)

# ==================== PUBLIC ROUTES ====================


@api_router.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    modules = {}
    for mod_name in ["pywebpush", "py_vapid", "emergentintegrations"]:
        try:
            __import__(mod_name)
            modules[mod_name] = "installed"
        except ImportError:
            modules[mod_name] = "MISSING"
    return {"status": "healthy", "service": "zektrix-backend", "modules": modules}

@api_router.get("/")
async def root():
    return {"message": "Zektrix UK Competition Platform API", "version": "2.0.0"}

# ==================== LIVE STATUS ====================

class LiveStatusUpdate(BaseModel):
    isLive: bool
    message: Optional[str] = ""

@api_router.get("/settings/live-status")
async def get_live_status():
    """Get current live streaming status"""
    settings = await db.settings.find_one({"key": "live_status"})
    if settings:
        return {"isLive": settings.get("isLive", False), "message": settings.get("message", "")}
    return {"isLive": False, "message": ""}

@api_router.put("/admin/live-status")
async def update_live_status(status: LiveStatusUpdate, current_user: dict = Depends(get_current_user)):
    """Admin: Update live streaming status"""
    if current_user.get("role") != "admin" and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.settings.update_one(
        {"key": "live_status"},
        {"$set": {"isLive": status.isLive, "message": status.message, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    # Broadcast to WebSocket clients
    await ws_manager.broadcast({"type": "live_status", "isLive": status.isLive, "message": status.message})
    
    return {"success": True, "isLive": status.isLive, "message": status.message}

# ==================== VIVA WEBHOOK ====================

@api_router.get("/webhooks/viva")
async def viva_webhook_verification():
    """Handle Viva Webhook URL verification - must return Key in JSON format"""
    return {"Key": "475FFE73819D67134BBB2D6690A9023714C14E2E"}

@api_router.post("/webhooks/viva")
async def viva_webhook(request: Request):
    """Handle Viva Payment webhook callbacks"""
    try:
        payload = await request.json()
        logger.info(f"Viva webhook received: {payload}")
        
        event_type = payload.get("EventTypeId")
        event_data = payload.get("EventData", {})
        
        # Transaction Paid event
        if event_type == 1796:  # Transaction Payment Created
            transaction_id = event_data.get("TransactionId")
            order_code = event_data.get("OrderCode")
            amount = event_data.get("Amount", 0) / 100  # Convert from cents
            
            # Find pending purchase by order code
            pending = await db.pending_purchases.find_one({"viva_order_code": str(order_code)})
            
            if pending:
                # Generate tickets now that payment is confirmed
                tickets_to_create = []
                competition = await db.competitions.find_one({"competition_id": pending["competition_id"]})
                
                if competition:
                    for i in range(pending["quantity"]):
                        # Generate RANDOM ticket number
                        ticket_number = await generate_random_ticket_number(
                            pending["competition_id"], 
                            competition["max_tickets"]
                        )
                        ticket = {
                            "ticket_id": f"tkt_{uuid.uuid4().hex[:12]}",
                            "ticket_code": f"ZEK{random.randint(100000, 999999)}",
                            "competition_id": pending["competition_id"],
                            "user_id": pending["user_id"],
                            "ticket_number": ticket_number,
                            "status": "active",
                            "purchased_at": datetime.now(timezone.utc).isoformat(),
                            "payment_method": "viva",
                            "viva_transaction_id": transaction_id
                        }
                        tickets_to_create.append(ticket)
                    
                    # Insert tickets
                    if tickets_to_create:
                        await db.tickets.insert_many(tickets_to_create)
                    
                    # Update competition sold count
                    await db.competitions.update_one(
                        {"competition_id": pending["competition_id"]},
                        {"$inc": {"sold_tickets": pending["quantity"]}}
                    )
                    
                    # Update pending purchase status
                    await db.pending_purchases.update_one(
                        {"_id": pending["_id"]},
                        {"$set": {"status": "completed", "transaction_id": transaction_id, "completed_at": datetime.now(timezone.utc).isoformat()}}
                    )
                    
                    # Record transaction
                    await db.transactions.insert_one({
                        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
                        "user_id": pending["user_id"],
                        "type": "ticket_purchase",
                        "amount": -amount,
                        "description": f"Purchase {pending['quantity']} spots - {competition.get('title', 'Competition')}",
                        "viva_order_code": str(order_code),
                        "viva_transaction_id": transaction_id,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    
                    logger.info(f"Viva webhook: Created {len(tickets_to_create)} tickets for order {order_code}")
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Viva webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}

@api_router.post("/admin/process-pending-payment/{order_code}")
async def admin_process_pending_payment(order_code: str, admin: dict = Depends(get_admin_user)):
    """Manually process a pending payment and create tickets"""
    # Find pending purchase
    pending = await db.pending_purchases.find_one({"viva_order_code": order_code})
    if not pending:
        # Try with string conversion
        pending = await db.pending_purchases.find_one({"viva_order_code": str(order_code)})
    
    if not pending:
        raise HTTPException(status_code=404, detail=f"Pending purchase not found for order {order_code}")
    
    if pending.get("status") == "completed":
        return {"message": "Payment already processed", "pending": {k:v for k,v in pending.items() if k != "_id"}}
    
    # Get competition
    competition = await db.competitions.find_one({"competition_id": pending["competition_id"]})
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # Create tickets with RANDOM numbers
    tickets_created = []
    for i in range(pending["quantity"]):
        # Generate RANDOM ticket number
        ticket_number = await generate_random_ticket_number(
            pending["competition_id"],
            competition["max_tickets"]
        )
        ticket = {
            "ticket_id": f"tkt_{uuid.uuid4().hex[:12]}",
            "ticket_code": f"ZEK{random.randint(100000, 999999)}",
            "competition_id": pending["competition_id"],
            "user_id": pending["user_id"],
            "ticket_number": ticket_number,
            "status": "active",
            "purchased_at": datetime.now(timezone.utc).isoformat(),
            "payment_method": "viva_manual",
            "viva_order_code": order_code
        }
        tickets_created.append(ticket)
    
    if tickets_created:
        await db.tickets.insert_many(tickets_created)
    
    # Update competition sold count
    await db.competitions.update_one(
        {"competition_id": pending["competition_id"]},
        {"$inc": {"sold_tickets": pending["quantity"]}}
    )
    
    # Update pending status
    await db.pending_purchases.update_one(
        {"_id": pending["_id"]},
        {"$set": {"status": "completed", "processed_manually": True, "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "success": True,
        "message": f"Created {len(tickets_created)} tickets for user",
        "tickets": len(tickets_created),
        "user_id": pending["user_id"],
        "competition": competition.get("title")
    }

@api_router.get("/admin/pending-payments")
async def admin_get_pending_payments(admin: dict = Depends(get_admin_user)):
    """Get all pending payments that haven't been processed"""
    pending = await db.pending_purchases.find(
        {"status": {"$ne": "completed"}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return pending

@api_router.post("/admin/sync-sold-tickets")
async def admin_sync_sold_tickets(admin: dict = Depends(get_admin_user)):
    """Sync sold_tickets count with actual tickets in database"""
    competitions = await db.competitions.find({}, {"_id": 0, "competition_id": 1, "title": 1, "sold_tickets": 1}).to_list(1000)
    
    updates = []
    for comp in competitions:
        actual_count = await db.tickets.count_documents({"competition_id": comp["competition_id"]})
        if actual_count != comp.get("sold_tickets", 0):
            await db.competitions.update_one(
                {"competition_id": comp["competition_id"]},
                {"$set": {"sold_tickets": actual_count}}
            )
            updates.append({
                "competition_id": comp["competition_id"],
                "title": comp.get("title"),
                "old_count": comp.get("sold_tickets", 0),
                "new_count": actual_count
            })
    
    return {
        "success": True,
        "message": f"Synced {len(updates)} competitions",
        "updates": updates
    }

@api_router.get("/payments/verify")
async def verify_payment(
    orderId: Optional[str] = None,
    transactionId: Optional[str] = None,
    t: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Verify payment and return ticket details"""
    trans_id = transactionId or t
    
    if not orderId and not trans_id:
        raise HTTPException(status_code=400, detail="Order ID or Transaction ID required")
    
    # Find tickets by transaction
    query = {"user_id": current_user["user_id"]}
    if trans_id:
        query["viva_transaction_id"] = trans_id
    
    tickets = await db.tickets.find(query).sort("purchased_at", -1).limit(20).to_list(20)
    
    # Get pending purchase details
    pending_query = {"user_id": current_user["user_id"]}
    if orderId:
        pending_query["viva_order_code"] = orderId
    
    pending = await db.pending_purchases.find_one(pending_query)
    
    return {
        "success": True,
        "tickets": [{k: v for k, v in t.items() if k != "_id"} for t in tickets],
        "amount": pending.get("total_amount") if pending else None,
        "status": pending.get("status") if pending else "completed"
    }

# ==================== EMAIL BOT ENDPOINTS ====================

@api_router.post("/admin/send-daily-digest")
async def send_daily_digest(admin: dict = Depends(get_admin_user)):
    """Manually trigger daily digest emails to all users"""
    # Get new competitions (created in last 24 hours)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    new_competitions = await db.competitions.find({
        "created_at": {"$gte": yesterday.isoformat()},
        "status": "active"
    }, {"_id": 0}).to_list(20)
    
    # Get competitions that are 70%+ sold (ending soon)
    all_active = await db.competitions.find({"status": "active"}, {"_id": 0}).to_list(100)
    ending_soon = [c for c in all_active if c.get("sold_tickets", 0) / max(c.get("max_tickets", 1), 1) >= 0.7]
    
    if not new_competitions and not ending_soon:
        return {"message": "Nu sunt competiții noi sau aproape de final", "emails_sent": 0}
    
    # Get all users who have email
    users = await db.users.find({
        "email": {"$exists": True, "$ne": ""},
        "is_blocked": {"$ne": True}
    }, {"_id": 0, "email": 1, "username": 1}).to_list(10000)
    
    sent_count = 0
    for user in users:
        try:
            await send_daily_digest_email(
                user["email"], 
                user.get("username", "Utilizator"),
                new_competitions,
                ending_soon
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send digest to {user.get('email')}: {e}")
    
    return {"message": f"Digest trimis la {sent_count} utilizatori", "emails_sent": sent_count}

@api_router.post("/admin/notify-75-percent/{competition_id}")
async def notify_competition_75_percent(competition_id: str, admin: dict = Depends(get_admin_user)):
    """Send notification to all users when competition reaches 75%"""
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    sold_percent = int((comp.get("sold_tickets", 0) / max(comp.get("max_tickets", 1), 1)) * 100)
    
    if sold_percent < 75:
        return {"message": f"Competiția este doar {sold_percent}% vândută. Notificările se trimit la 75%+"}
    
    # Get all users
    users = await db.users.find({
        "email": {"$exists": True, "$ne": ""},
        "is_blocked": {"$ne": True}
    }, {"_id": 0, "email": 1, "username": 1}).to_list(10000)
    
    sent_count = 0
    for user in users:
        try:
            await send_competition_75_percent_email(
                user["email"],
                user.get("username", "Utilizator"),
                comp["title"],
                sold_percent
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send 75% notification to {user.get('email')}: {e}")
    
    return {"message": f"Notificare trimisă la {sent_count} utilizatori pentru '{comp['title']}' ({sold_percent}% vândut)", "emails_sent": sent_count}

# ==================== COMPETITION AUTO-BOT ====================
# Automatically maintains 3 cash prize competitions and auto-draws winners

AUTO_COMPETITION_TEMPLATES = [
    {
        "prize_amount": 500,
        "max_tickets": 100,
        "ticket_price": 7.99,
        "title_template": "Castiga {amount} RON Cash!",
        "description": "Participa acum pentru sansa de a castiga 500 RON in numerar! Extragere automata cand toate biletele sunt vandute.",
        "category": "cash"
    },
    {
        "prize_amount": 2500,
        "max_tickets": 200,
        "ticket_price": 15.99,
        "title_template": "Castiga {amount} RON Cash!",
        "description": "Premiu mare de 2500 RON in numerar! Extragere automata la completarea tuturor biletelor.",
        "category": "cash"
    },
    {
        "prize_amount": 5000,
        "max_tickets": 500,
        "ticket_price": 14.99,
        "title_template": "JACKPOT {amount} RON Cash!",
        "description": "Mega premiu de 5000 RON in numerar! Sansa ta de a castiga mare. Extragere automata.",
        "category": "cash"
    }
]

# Special competitions (not auto-recreated, admin controlled)
SPECIAL_COMPETITION_CONFIGS = [
    {
        "id": "tesla_model_3",
        "prize_name": "Tesla Model 3",
        "prize_value": 200000,  # ~200k RON value
        "max_tickets": 61000,
        "ticket_price": 5.5,
        "duration_days": 90,
        "title": "MEGA PREMIU: Tesla Model 3!",
        "description": "Castiga o Tesla Model 3 NOUA! Competitie speciala cu 61.000 de locuri. Extragere la finalul celor 90 de zile sau cand adminul decide. Nu rata aceasta sansa unica!",
        "category": "cars",
        "image_url": "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=800&q=80"
    }
]

# Permanent auto-recreating competition config
PERMANENT_COMPETITION_CONFIG = {
    "id": "permanent_special",
    "title": "Competiție Specială - 10.000 RON",
    "description": "Competiția Specială cu premiu de 10.000 RON Cash! Se extrage automat când se vând toate biletele și se creează instant una nouă. Șanse mari de câștig la doar 1.99 RON!",
    "ticket_price": 1.99,
    "max_tickets": 8900,
    "category": "cash",
    "prize_description": "10.000 RON Cash",
    "prize_value": 10000,
    "image_url": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=800&q=80"
}

async def create_permanent_competition() -> dict:
    """Create the permanent auto-recreating competition"""
    config = PERMANENT_COMPETITION_CONFIG
    competition_id = f"comp_special_{uuid.uuid4().hex[:8]}"
    
    comp_doc = {
        "competition_id": competition_id,
        "title": config["title"],
        "description": config["description"],
        "ticket_price": config["ticket_price"],
        "max_tickets": config["max_tickets"],
        "sold_tickets": 0,
        "competition_type": "instant_win",
        "category": config["category"],
        "status": "active",
        "image_url": config["image_url"],
        "prize_description": config["prize_description"],
        "prize_value": config.get("prize_value", 10000),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_permanent": True,
        "qualification_question": {
            "question": "Care este premiul acestei competiții?",
            "options": ["10.000 RON", "5.000 RON", "1.000 RON"],
            "correct_answer": 0
        }
    }
    
    await db.competitions.insert_one(comp_doc)
    logger.info(f"[PERMANENT-BOT] Created permanent competition: {comp_doc['title']} (ID: {competition_id})")
    
    comp_doc.pop("_id", None)
    return comp_doc

async def check_and_recreate_permanent_competition():
    """Check if permanent competition needs to be recreated after winner draw"""
    # Find active permanent competition
    active_perm = await db.competitions.find_one({
        "is_permanent": True,
        "status": "active"
    })
    
    if not active_perm:
        # No active permanent competition - create one
        await create_permanent_competition()
        return
    
    # Check if it's full and needs winner draw
    if active_perm["sold_tickets"] >= active_perm["max_tickets"]:
        # Draw winner and create new one
        await draw_competition_winner(active_perm["competition_id"])
        await create_permanent_competition()
        logger.info("[PERMANENT-BOT] Drew winner and created new permanent competition")

async def create_auto_competition(template: dict) -> dict:
    """Create a new auto-managed competition from template"""
    competition_id = f"comp_{uuid.uuid4().hex[:12]}"
    
    comp_doc = {
        "competition_id": competition_id,
        "title": template["title_template"].format(amount=template["prize_amount"]),
        "description": template["description"],
        "ticket_price": template["ticket_price"],
        "max_tickets": template["max_tickets"],
        "sold_tickets": 0,
        "competition_type": "instant_win",
        "category": template["category"],
        "status": "active",
        "image_url": f"https://images.unsplash.com/photo-1621981386829-9b458a2cddde?w=800&q=80",  # Cash/money image
        "prize_description": f"{template['prize_amount']} RON în numerar",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_auto_managed": True,
        "auto_prize_amount": template["prize_amount"],
        "qualification_question": {
            "question": f"Cât de mult este premiul acestei competiții?",
            "options": [f"{template['prize_amount']} RON", f"{template['prize_amount'] + 500} RON"],
            "correct_answer": 0
        }
    }
    
    await db.competitions.insert_one(comp_doc)
    logger.info(f"[AUTO-BOT] Created new competition: {comp_doc['title']} (ID: {competition_id})")
    
    # Return without _id (MongoDB adds it)
    comp_doc.pop("_id", None)
    return comp_doc

async def create_special_competition(config_id: str) -> dict:
    """Create a special competition (Tesla, etc.) - not auto-recreated"""
    # Find config
    config = None
    for c in SPECIAL_COMPETITION_CONFIGS:
        if c["id"] == config_id:
            config = c
            break
    
    if not config:
        return None
    
    # Check if already exists and active
    existing = await db.competitions.find_one({
        "special_config_id": config_id,
        "status": "active"
    })
    if existing:
        return None  # Already exists
    
    competition_id = f"comp_{uuid.uuid4().hex[:12]}"
    end_date = datetime.now(timezone.utc) + timedelta(days=config["duration_days"])
    
    comp_doc = {
        "competition_id": competition_id,
        "title": config["title"],
        "description": config["description"],
        "ticket_price": config["ticket_price"],
        "max_tickets": config["max_tickets"],
        "sold_tickets": 0,
        "competition_type": "classic",  # Not instant win - has end date
        "category": config["category"],
        "status": "active",
        "image_url": config["image_url"],
        "prize_description": config["prize_name"],
        "prize_value": config["prize_value"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "draw_date": end_date.isoformat(),
        "is_auto_managed": False,  # Admin controlled
        "special_config_id": config_id,
        "qualification_question": {
            "question": "Care este premiul acestei competitii?",
            "options": [config["prize_name"], "iPhone 15 Pro", "5000 RON"],
            "correct_answer": 0
        }
    }
    
    await db.competitions.insert_one(comp_doc)
    logger.info(f"[SPECIAL] Created special competition: {comp_doc['title']} (ID: {competition_id})")
    
    comp_doc.pop("_id", None)
    return comp_doc

# Admin endpoint to create special competitions
@api_router.post("/admin/create-special-competition/{config_id}")
async def admin_create_special_competition(config_id: str, admin: dict = Depends(get_admin_user)):
    """Create a special competition (Tesla, etc.)"""
    result = await create_special_competition(config_id)
    if result:
        return {"success": True, "competition": result}
    else:
        raise HTTPException(status_code=400, detail="Competitia exista deja sau config invalid")

# Admin endpoint to list available special configs
@api_router.get("/admin/special-competition-configs")
async def get_special_configs(admin: dict = Depends(get_admin_user)):
    """Get available special competition configurations"""
    configs_with_status = []
    for config in SPECIAL_COMPETITION_CONFIGS:
        existing = await db.competitions.find_one({
            "special_config_id": config["id"],
            "status": "active"
        })
        configs_with_status.append({
            **config,
            "already_active": existing is not None
        })
    return configs_with_status

async def auto_draw_winner(competition_id: str) -> dict:
    """Automatically draw winner for a completed competition"""
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp:
        logger.error(f"[AUTO-BOT] Competition not found: {competition_id}")
        return None
    
    if comp.get("winner_id"):
        logger.info(f"[AUTO-BOT] Winner already drawn for: {comp['title']}")
        return None
    
    # Get all tickets
    tickets = await db.tickets.find({"competition_id": competition_id}, {"_id": 0}).to_list(10000)
    if not tickets:
        logger.error(f"[AUTO-BOT] No tickets for competition: {competition_id}")
        return None
    
    # Random selection
    winner_ticket = random.choice(tickets)
    winner_user = await db.users.find_one({"user_id": winner_ticket["user_id"]}, {"_id": 0})
    
    if not winner_user:
        logger.error(f"[AUTO-BOT] Winner user not found: {winner_ticket['user_id']}")
        return None
    
    # Update competition
    await db.competitions.update_one(
        {"competition_id": competition_id},
        {"$set": {
            "status": "completed",
            "winner_id": winner_ticket["user_id"],
            "winner_ticket": winner_ticket["ticket_number"],
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Create winner record
    winner_doc = {
        "winner_id": f"winner_{uuid.uuid4().hex[:12]}",
        "competition_id": competition_id,
        "competition_title": comp["title"],
        "user_id": winner_ticket["user_id"],
        "username": winner_user.get("username", "Unknown"),
        "first_name": winner_user.get("first_name", ""),
        "last_name": winner_user.get("last_name", ""),
        "ticket_number": winner_ticket["ticket_number"],
        "prize_description": comp.get("prize_description"),
        "prize_amount": comp.get("auto_prize_amount", 0),
        "announced_at": datetime.now(timezone.utc).isoformat(),
        "is_automatic": True
    }
    await db.winners.insert_one(winner_doc)
    
    logger.info(f"[AUTO-BOT] Winner drawn! {winner_user.get('username')} won {comp['title']} with ticket #{winner_ticket['ticket_number']}")
    
    # Send winner email
    if winner_user.get("email"):
        try:
            await send_winner_notification_email(
                winner_user["email"],
                winner_user.get("first_name") or winner_user.get("username", "Câștigător"),
                comp["title"],
                comp.get("prize_description"),
                winner_ticket["ticket_number"]
            )
            logger.info(f"[AUTO-BOT] Winner email sent to: {winner_user['email']}")
        except Exception as e:
            logger.error(f"[AUTO-BOT] Failed to send winner email: {e}")
    
    # Broadcast winner announcement
    await ws_manager.broadcast_all({
        "type": "winner_announced",
        "competition_id": competition_id,
        "competition_title": comp["title"],
        "winner_username": winner_user.get("username", "Unknown"),
        "ticket_number": winner_ticket["ticket_number"],
        "is_automatic": True
    })
    
    # Push notification to winner
    await notify_user_push(
        winner_ticket["user_id"],
        "Felicitări! Ai câștigat!",
        f"Ai câștigat la {comp['title']}! Locul #{winner_ticket['ticket_number']} este câștigător!",
        f"https://zektrix.uk/competitions/{competition_id}"
    )
    
    # Push notification to all other participants
    await notify_competition_participants_push(
        competition_id,
        f"{comp['title']} - Câștigător extras!",
        f"Câștigătorul a fost extras! Verifică rezultatele.",
        "https://zektrix.uk/winners"
    )
    
    return winner_doc

async def competition_auto_bot():
    """Background task that manages automatic competitions"""
    logger.info("[AUTO-BOT] Starting Competition Auto-Bot...")
    
    # Initial delay to let server start
    await asyncio.sleep(10)
    
    while True:
        try:
            # Check for each prize tier
            for template in AUTO_COMPETITION_TEMPLATES:
                prize_amount = template["prize_amount"]
                
                # Count active competitions for this prize tier
                active_count = await db.competitions.count_documents({
                    "is_auto_managed": True,
                    "auto_prize_amount": prize_amount,
                    "status": "active"
                })
                
                # If no active competition for this tier, create one
                if active_count == 0:
                    logger.info(f"[AUTO-BOT] No active {prize_amount} RON competition, creating one...")
                    await create_auto_competition(template)
            
            # Check for completed competitions (100% sold) that need auto-draw
            full_competitions = await db.competitions.find({
                "is_auto_managed": True,
                "status": "active",
                "$expr": {"$gte": ["$sold_tickets", "$max_tickets"]}
            }, {"_id": 0}).to_list(100)
            
            for comp in full_competitions:
                logger.info(f"[AUTO-BOT] Competition full! Drawing winner for: {comp['title']}")
                await auto_draw_winner(comp["competition_id"])
                
                # Create a replacement competition
                for template in AUTO_COMPETITION_TEMPLATES:
                    if template["prize_amount"] == comp.get("auto_prize_amount"):
                        await create_auto_competition(template)
                        break
            
            # ===== PERMANENT COMPETITION CHECK =====
            # Check if permanent competition exists and is active
            active_perm = await db.competitions.find_one({
                "is_permanent": True,
                "status": "active"
            })
            
            if not active_perm:
                # No active permanent competition - create one
                logger.info("[PERMANENT-BOT] No permanent competition found, creating one...")
                await create_permanent_competition()
            elif active_perm["sold_tickets"] >= active_perm["max_tickets"]:
                # Permanent competition is full - draw winner and create new one
                logger.info(f"[PERMANENT-BOT] Permanent competition full! Drawing winner...")
                await auto_draw_winner(active_perm["competition_id"])
                await create_permanent_competition()
            
            # Log status every 30 seconds
            active_comps = await db.competitions.find({"status": "active"}, {"_id": 0, "title": 1, "sold_tickets": 1, "max_tickets": 1, "is_permanent": 1}).to_list(20)
            if active_comps:
                status_msg = ", ".join([f"{'[PERM]' if c.get('is_permanent') else ''}{c['title']}: {c['sold_tickets']}/{c['max_tickets']}" for c in active_comps])
                logger.info(f"[AUTO-BOT] Active competitions: {status_msg}")
            
        except Exception as e:
            logger.error(f"[AUTO-BOT] Error: {e}")
        
        # Check every 30 seconds
        await asyncio.sleep(30)

# ==================== DAILY EMAIL BOT ====================
# Sends daily email to all users with competition updates

async def generate_daily_email_html(competitions: list, user_name: str, user_id: str = "") -> str:
    """Generate modern premium email HTML for daily digest"""
    
    sorted_comps = sorted(competitions, key=lambda x: (x.get("sold_tickets", 0) / max(x.get("max_tickets", 1), 1)), reverse=True)
    
    # Calculate total prizes as ticket_price × max_tickets (realistic prize pool)
    total_prize_pool = 0
    for comp in sorted_comps:
        price = comp.get("ticket_price", 0) or 0
        max_t = comp.get("max_tickets", 0) or 0
        if price > 0:
            total_prize_pool += price * max_t
        elif comp.get("auto_prize_amount"):
            total_prize_pool += comp["auto_prize_amount"]
    
    total_tickets_available = sum(comp.get("max_tickets", 0) - comp.get("sold_tickets", 0) for comp in sorted_comps)
    hot_comps = [c for c in sorted_comps if (c.get("sold_tickets", 0) / max(c.get("max_tickets", 1), 1)) > 0.6]
    
    # Build competition cards with images
    comp_cards = ""
    for comp in sorted_comps[:6]:
        progress = int((comp.get("sold_tickets", 0) / max(comp.get("max_tickets", 1), 1)) * 100)
        remaining = comp.get("max_tickets", 0) - comp.get("sold_tickets", 0)
        prize = comp.get("prize_description") or comp.get("title", "Premiu")
        image_url = comp.get("image_url", "")
        comp_link = f"https://zektrix.uk/competitions/{comp.get('competition_id', '')}"
        price = comp.get("ticket_price", 0) or 0
        max_t = comp.get("max_tickets", 0) or 0
        comp_prize_pool = price * max_t if price > 0 else (comp.get("auto_prize_amount") or 0)
        is_free = price == 0
        
        if progress >= 80:
            urgency_color = "#ef4444"
            urgency_text = "APROAPE SOLD OUT!"
            badge_bg = "linear-gradient(135deg, #ef4444, #dc2626)"
        elif progress >= 60:
            urgency_color = "#f97316"
            urgency_text = "SE VINDE RAPID!"
            badge_bg = "linear-gradient(135deg, #f97316, #ea580c)"
        elif is_free:
            urgency_color = "#10b981"
            urgency_text = "GRATUIT!"
            badge_bg = "linear-gradient(135deg, #10b981, #059669)"
        else:
            urgency_color = "#8b5cf6"
            urgency_text = ""
            badge_bg = ""
        
        price_display = "GRATUIT" if is_free else f"£{price:.2f}"
        
        image_section = ""
        if image_url:
            image_section = f'''
                                                <a href="{comp_link}" style="text-decoration: none; display: block;">
                                                    <img src="{image_url}" alt="{comp.get('title', '')}" style="width: 100%; height: 200px; object-fit: cover; display: block; border-radius: 12px 12px 0 0;" />
                                                </a>'''
        
        urgency_badge = ""
        if urgency_text:
            urgency_badge = f'<span style="display: inline-block; background: {badge_bg}; color: white; padding: 3px 10px; border-radius: 20px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;">{urgency_text}</span>'
        
        comp_cards += f'''
                    <tr>
                        <td style="padding: 0 0 16px 0;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0d0b1a; border: 1px solid #1e1b3a; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 0;">
                                        {image_section}
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="padding: 16px 18px;">
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                                        <tr>
                                                            <td>
                                                                <a href="{comp_link}" style="text-decoration: none; color: #ffffff; font-size: 17px; font-weight: 700; display: block; margin-bottom: 6px;">{comp.get("title", "")}</a>
                                                                {urgency_badge}
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%; margin-top: 12px;">
                                                        <tr>
                                                            <td style="width: 50%;">
                                                                <p style="color: #6b7280; margin: 0; font-size: 11px;">Premiu</p>
                                                                <p style="color: #fbbf24; margin: 2px 0 0 0; font-size: 14px; font-weight: 700;">{prize[:40]}</p>
                                                            </td>
                                                            <td style="width: 50%; text-align: right;">
                                                                <p style="color: #6b7280; margin: 0; font-size: 11px;">Pret loc</p>
                                                                <p style="color: #10b981; margin: 2px 0 0 0; font-size: 14px; font-weight: 700;">{price_display}</p>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%; margin-top: 12px;">
                                                        <tr>
                                                            <td style="background: #1a1730; border-radius: 6px; height: 8px; overflow: hidden;">
                                                                <div style="background: linear-gradient(90deg, {urgency_color}, #a855f7); height: 8px; width: {max(progress, 2)}%; border-radius: 6px;"></div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%; margin-top: 8px;">
                                                        <tr>
                                                            <td>
                                                                <span style="color: #6b7280; font-size: 11px;"><span style="color: {urgency_color}; font-weight: 700;">{progress}%</span> ocupat</span>
                                                                <span style="color: #6b7280; font-size: 11px; margin-left: 8px;"><span style="color: #10b981; font-weight: 600;">{remaining:,}</span> locuri</span>
                                                            </td>
                                                            <td style="text-align: right;">
                                                                <a href="{comp_link}" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; text-decoration: none; padding: 7px 18px; border-radius: 20px; font-size: 12px; font-weight: 600;">Participa</a>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''
    
    # Hot alert
    hot_alert_html = ""
    if hot_comps:
        hot_alert_html = f'''<tr>
                        <td style="padding-bottom: 20px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #451a03 0%, #7c2d12 100%); border: 1px solid #f9731640; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 14px 20px; text-align: center;">
                                        <p style="color: #fed7aa; margin: 0; font-size: 13px; font-weight: 600;">
                                            &#128293; <strong style="color: #ffffff;">{len(hot_comps)} competitii</strong> se vand rapid! Nu rata sansa!
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''
    
    # Recent winners
    recent_winners = await db.winners.find({}, {"_id": 0}).sort("announced_at", -1).limit(3).to_list(3)
    winners_html = ""
    if recent_winners:
        winner_items = ""
        for w in recent_winners:
            winner_items += f'''
                                <tr>
                                    <td style="padding: 10px 16px; border-bottom: 1px solid #1e1b3a;">
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="width: 36px; vertical-align: middle;">
                                                    <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #fbbf24, #f59e0b); border-radius: 50%; text-align: center; line-height: 32px; font-size: 14px;">&#127942;</div>
                                                </td>
                                                <td style="vertical-align: middle;">
                                                    <p style="color: #ffffff; margin: 0; font-size: 13px; font-weight: 600;">{w.get("username", "Castigator")}</p>
                                                    <p style="color: #6b7280; margin: 0; font-size: 11px;">Loc #{w.get("ticket_number", "?")}</p>
                                                </td>
                                                <td style="text-align: right; vertical-align: middle;">
                                                    <p style="color: #fbbf24; margin: 0; font-size: 11px; font-weight: 600;">{w.get("competition_title", "")[:25]}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>'''
        winners_html = f'''
                    <tr>
                        <td style="padding: 25px 0 15px 0;">
                            <p style="color: #fbbf24; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin: 0; font-weight: 700;">&#127942; CASTIGATORI RECENTI</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding-bottom: 25px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0d0b1a; border: 1px solid #1e1b3a; border-radius: 12px; overflow: hidden;">
                                {winner_items}
                            </table>
                        </td>
                    </tr>'''
    
    # Format prize pool display
    if total_prize_pool >= 1000:
        prize_display = f"£{total_prize_pool:,.0f}"
    else:
        prize_display = f"£{total_prize_pool:.0f}"
    
    email_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zektrix - Competitii Active</title>
</head>
<body style="margin: 0; padding: 0; background-color: #030014; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table cellpadding="0" cellspacing="0" style="width: 100%; background-color: #030014;">
        <tr>
            <td style="padding: 30px 16px;">
                <table cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; width: 100%;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="text-align: center; padding-bottom: 24px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #0d0b1a 0%, #1a0a2e 50%, #0d0b1a 100%); border: 1px solid #8b5cf630; border-radius: 16px;">
                                <tr>
                                    <td style="padding: 28px 20px;">
                                        <h1 style="margin: 0 0 4px 0; font-size: 32px; font-weight: 900; letter-spacing: -1px; text-align: center;">
                                            <span style="color: #8b5cf6;">ZEKTRIX</span><span style="color: #ffffff;">.UK</span>
                                        </h1>
                                        <p style="color: #6b7280; margin: 0; font-size: 12px; text-align: center; letter-spacing: 1px;">PREMII REALE &bull; SANSE REALE &bull; CASTIGATORI REALI</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Greeting + Stats -->
                    <tr>
                        <td style="padding-bottom: 20px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #0d0b1a 0%, #130d24 100%); border: 1px solid #1e1b3a; border-radius: 16px;">
                                <tr>
                                    <td style="padding: 24px;">
                                        <p style="color: #9ca3af; margin: 0 0 4px 0; font-size: 14px;">Salut, <strong style="color: #ffffff;">{user_name}</strong>!</p>
                                        <p style="color: #6b7280; margin: 0 0 20px 0; font-size: 13px; line-height: 1.5;">
                                            Avem <strong style="color: #8b5cf6;">{len(sorted_comps)} competitii active</strong> cu premii in valoare totala de
                                        </p>
                                        <p style="text-align: center; margin: 0 0 20px 0;">
                                            <span style="font-size: 36px; font-weight: 900; color: #fbbf24; letter-spacing: -1px;">{prize_display}</span>
                                        </p>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="width: 33%; text-align: center; padding: 12px 4px; background: #0a0818; border-radius: 10px;">
                                                    <p style="color: #8b5cf6; margin: 0; font-size: 20px; font-weight: 800;">{len(sorted_comps)}</p>
                                                    <p style="color: #6b7280; margin: 2px 0 0 0; font-size: 10px;">Competitii</p>
                                                </td>
                                                <td style="width: 1%;"></td>
                                                <td style="width: 33%; text-align: center; padding: 12px 4px; background: #0a0818; border-radius: 10px;">
                                                    <p style="color: #f97316; margin: 0; font-size: 20px; font-weight: 800;">{total_tickets_available:,}</p>
                                                    <p style="color: #6b7280; margin: 2px 0 0 0; font-size: 10px;">Locuri Libere</p>
                                                </td>
                                                <td style="width: 1%;"></td>
                                                <td style="width: 33%; text-align: center; padding: 12px 4px; background: #0a0818; border-radius: 10px;">
                                                    <p style="color: #10b981; margin: 0; font-size: 20px; font-weight: 800;">{prize_display}</p>
                                                    <p style="color: #6b7280; margin: 2px 0 0 0; font-size: 10px;">Premii Totale</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    {hot_alert_html}
                    
                    <!-- Section Title -->
                    <tr>
                        <td style="padding-bottom: 12px;">
                            <p style="color: #a78bfa; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin: 0; font-weight: 700;">COMPETITII DISPONIBILE</p>
                        </td>
                    </tr>
                    
                    {comp_cards}
                    
                    <!-- CTA -->
                    <tr>
                        <td style="text-align: center; padding: 20px 0 30px 0;">
                            <a href="https://zektrix.uk/competitions" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; text-decoration: none; padding: 16px 48px; border-radius: 50px; font-weight: 700; font-size: 15px; letter-spacing: 0.5px;">
                                VEZI TOATE COMPETITIILE &#8594;
                            </a>
                        </td>
                    </tr>
                    
                    {winners_html}
                    
                    <!-- Why Zektrix -->
                    <tr>
                        <td style="padding-bottom: 25px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0d0b1a; border: 1px solid #1e1b3a; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #ffffff; margin: 0 0 14px 0; font-size: 14px; font-weight: 700; text-align: center;">De ce Zektrix?</p>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="padding: 6px 8px; width: 50%;"><p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Extrageri transparente</p></td>
                                                <td style="padding: 6px 8px; width: 50%;"><p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Premii platite instant</p></td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 8px;"><p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Locuri de la £0.99</p></td>
                                                <td style="padding: 6px 8px;"><p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Suport 24/7 WhatsApp</p></td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding-top: 10px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0d0b1a; border: 1px solid #1e1b3a; border-radius: 16px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 28px 24px;">
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 20px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <h3 style="margin: 0; font-size: 22px; font-weight: 900;">
                                                        <span style="color: #8b5cf6;">ZEKTRIX</span><span style="color: #ffffff;">.UK</span>
                                                    </h3>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 20px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <a href="https://zektrix.uk" style="display: inline-block; background: #1a1730; color: #8b5cf6; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-size: 11px; font-weight: 600; margin: 0 3px;">&#127760; Website</a>
                                                    <a href="https://wa.me/40730268067" style="display: inline-block; background: #1a1730; color: #22c55e; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-size: 11px; font-weight: 600; margin: 0 3px;">&#128172; WhatsApp</a>
                                                    <a href="https://tiktok.com/@zektrix.uk" style="display: inline-block; background: #1a1730; color: #ffffff; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-size: 11px; font-weight: 600; margin: 0 3px;">&#9835; TikTok</a>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 16px;">
                                            <tr><td style="height: 1px; background: linear-gradient(90deg, transparent, #1e1b3a, transparent);"></td></tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 16px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <p style="color: #6b7280; font-size: 10px; margin: 0 0 8px 0; line-height: 1.5;">
                                                        Ai primit acest email pentru ca esti inregistrat pe <strong style="color: #8b5cf6;">Zektrix.uk</strong>.<br/>
                                                        Conform GDPR, datele tale sunt in siguranta si nu sunt partajate cu terti.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 16px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <a href="https://zektrix.uk/faq" style="color: #6b7280; text-decoration: none; font-size: 10px; margin: 0 8px;">FAQ</a>
                                                    <span style="color: #374151;">|</span>
                                                    <a href="https://zektrix.uk/privacy" style="color: #6b7280; text-decoration: none; font-size: 10px; margin: 0 8px;">Confidentialitate</a>
                                                    <span style="color: #374151;">|</span>
                                                    <a href="https://zektrix.uk/terms" style="color: #6b7280; text-decoration: none; font-size: 10px; margin: 0 8px;">Termeni</a>
                                                    <span style="color: #374151;">|</span>
                                                    <a href="https://zektrix.uk/dashboard" style="color: #6b7280; text-decoration: none; font-size: 10px; margin: 0 8px;">Contul Meu</a>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0a0818; border-radius: 10px; margin-bottom: 16px;">
                                            <tr>
                                                <td style="padding: 14px; text-align: center;">
                                                    <p style="color: #4b5563; font-size: 10px; margin: 0 0 8px 0;">Nu mai vrei aceste email-uri?</p>
                                                    <a href="https://zektrix.uk/unsubscribe/{user_id}" style="color: #ef4444; text-decoration: none; font-size: 11px; font-weight: 600;">Dezabonare</a>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <p style="color: #374151; font-size: 9px; margin: 0;">&#169; 2026 Zektrix UK Ltd. Toate drepturile rezervate.</p>
                                                    <p style="color: #2d3748; font-size: 8px; margin: 4px 0 0 0;">Zektrix UK Ltd &bull; c/o Bartle House, Oxford Court &bull; Manchester, M23 WQ &bull; United Kingdom</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
    
    return email_html

async def send_daily_digest_to_user(user: dict, competitions: list) -> bool:
    """Send daily digest email to a single user"""
    try:
        # Check if user is unsubscribed from marketing emails
        if user.get("email_unsubscribed", False):
            return True  # Skip but count as success
        
        user_name = user.get("first_name") or user.get("username", "Utilizator")
        user_id = user.get("user_id", "")
        email_html = await generate_daily_email_html(competitions, user_name, user_id)
        
        # Calculate total prize pool for subject line
        total_pool = 0
        for c in competitions:
            p = c.get("ticket_price", 0) or 0
            m = c.get("max_tickets", 0) or 0
            total_pool += p * m if p > 0 else (c.get("auto_prize_amount") or 0)
        
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": [user["email"]],
            "subject": f"[ZEKTRIX] {len(competitions)} Competitii Active - Premii de £{total_pool:,.0f}!",
            "html": email_html
        })
        return True
    except Exception as e:
        logger.error(f"[EMAIL-BOT] Failed to send to {user.get('email')}: {e}")
        return False

async def daily_email_bot():
    """Background task that sends emails twice a day: 9:00 and 18:00 Romania time (UTC+2/+3)"""
    logger.info("[EMAIL-BOT] Starting Daily Email Bot (9:00 & 18:00 Romania)...")
    
    # Initial delay to let server stabilize
    await asyncio.sleep(60)
    
    # Track sent times to avoid duplicates
    sent_morning_date = None
    sent_evening_date = None
    
    while True:
        try:
            # Romania is UTC+2 (winter) or UTC+3 (summer/DST)
            # Using UTC+2 as baseline: 9:00 RO = 7:00 UTC, 18:00 RO = 16:00 UTC
            now = datetime.now(timezone.utc)
            today = now.date()
            current_hour = now.hour
            
            # Morning send: 7:00-8:00 UTC (9:00-10:00 Romania)
            should_send_morning = (
                sent_morning_date != today and 
                7 <= current_hour < 9
            )
            
            # Evening send: 16:00-17:00 UTC (18:00-19:00 Romania)
            should_send_evening = (
                sent_evening_date != today and 
                16 <= current_hour < 18
            )
            
            if should_send_morning or should_send_evening:
                time_label = "DIMINEAȚĂ 9:00" if should_send_morning else "SEARĂ 18:00"
                logger.info(f"[EMAIL-BOT] Starting {time_label} email digest...")
                
                # Get active competitions
                competitions = await db.competitions.find(
                    {"status": "active"},
                    {"_id": 0}
                ).to_list(100)
                
                if not competitions:
                    logger.info(f"[EMAIL-BOT] No active competitions, skipping {time_label} emails")
                    if should_send_morning:
                        sent_morning_date = today
                    else:
                        sent_evening_date = today
                    await asyncio.sleep(1800)  # Check again in 30 min
                    continue
                
                # Get all users with valid email
                users = await db.users.find(
                    {"email": {"$exists": True, "$ne": None}},
                    {"_id": 0, "user_id": 1, "email": 1, "first_name": 1, "username": 1}
                ).to_list(10000)
                
                sent_count = 0
                failed_count = 0
                
                for user in users:
                    success = await send_daily_digest_to_user(user, competitions)
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                    
                    # Rate limiting - small delay between emails
                    await asyncio.sleep(0.5)
                
                logger.info(f"[EMAIL-BOT] {time_label} digest complete! Sent: {sent_count}, Failed: {failed_count}")
                
                # Mark as sent
                if should_send_morning:
                    sent_morning_date = today
                else:
                    sent_evening_date = today
            
        except Exception as e:
            logger.error(f"[EMAIL-BOT] Error: {e}")
        
        # Check every 30 minutes
        await asyncio.sleep(1800)

# Endpoint to manually trigger daily digest (admin only)
@api_router.post("/admin/trigger-daily-digest")
async def trigger_daily_digest(admin: dict = Depends(get_admin_user)):
    """Manually trigger daily digest email to all users"""
    competitions = await db.competitions.find({"status": "active"}, {"_id": 0}).to_list(100)
    users = await db.users.find(
        {"email": {"$exists": True, "$ne": None}},
        {"_id": 0, "user_id": 1, "email": 1, "first_name": 1, "username": 1}
    ).to_list(10000)
    
    sent_count = 0
    for user in users:
        success = await send_daily_digest_to_user(user, competitions)
        if success:
            sent_count += 1
        await asyncio.sleep(0.3)
    
    return {"message": f"Daily digest sent to {sent_count} users", "total_users": len(users)}

# Endpoint to send test email (admin only)
@api_router.post("/admin/test-daily-email")
async def test_daily_email(email: str = "d.madalin29@gmail.com", admin: dict = Depends(get_admin_user)):
    """Send test daily digest email to specific address"""
    competitions = await db.competitions.find({"status": "active"}, {"_id": 0}).to_list(100)
    
    test_user = {"email": email, "first_name": "Test User", "username": "testuser"}
    success = await send_daily_digest_to_user(test_user, competitions)
    
    if success:
        return {"message": f"Test email sent to {email}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email")

# Email Unsubscribe endpoint (no auth required - uses user_id from link)
@api_router.post("/email/unsubscribe/{user_id}")
async def unsubscribe_from_emails(user_id: str):
    """Unsubscribe user from marketing emails"""
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negasit")
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"email_unsubscribed": True, "unsubscribed_at": datetime.now(timezone.utc)}}
    )
    
    return {
        "success": True,
        "message": "Te-ai dezabonat cu succes de la email-urile promotionale.",
        "email": user.get("email", "")[:3] + "***"  # Partial email for confirmation
    }

# Email Resubscribe endpoint
@api_router.post("/email/resubscribe/{user_id}")
async def resubscribe_to_emails(user_id: str):
    """Resubscribe user to marketing emails"""
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negasit")
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"email_unsubscribed": False}, "$unset": {"unsubscribed_at": ""}}
    )
    
    return {
        "success": True,
        "message": "Te-ai reabonat cu succes la email-urile promotionale!",
        "email": user.get("email", "")[:3] + "***"
    }

# Check subscription status
@api_router.get("/email/status/{user_id}")
async def get_email_subscription_status(user_id: str):
    """Get user's email subscription status"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email_unsubscribed": 1, "email": 1})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negasit")
    
    return {
        "subscribed": not user.get("email_unsubscribed", False),
        "email": user.get("email", "")[:3] + "***"
    }

@api_router.post("/upload/image")
async def upload_image(file: UploadFile = File(...), current_user: dict = Depends(get_admin_user)):
    """Upload image for competitions (admin only)"""
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Only JPEG, PNG, WebP and GIF images allowed")
    
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 10MB)")
    
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
        ext = "jpg"
    
    import uuid
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Return the public URL
    backend_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    if backend_url:
        image_url = f"https://{backend_url}/api/uploads/{filename}"
    else:
        image_url = f"/api/uploads/{filename}"
    
    return {"url": image_url, "filename": filename}

app.include_router(api_router)

# Serve uploaded files
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db():
    # Create indexes
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.users.create_index("referral_code", unique=True, sparse=True)
    await db.competitions.create_index("competition_id", unique=True)
    await db.tickets.create_index("ticket_id", unique=True)
    await db.tickets.create_index([("competition_id", 1), ("ticket_number", 1)], unique=True)
    await db.transactions.create_index("transaction_id", unique=True)
    await db.transactions.create_index("viva_order_code")
    await db.winners.create_index("winner_id", unique=True)
    await db.user_sessions.create_index("user_id", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.referrals.create_index("referral_id", unique=True)
    await db.referrals.create_index("referrer_id")
    await db.referrals.create_index("referred_id", unique=True, sparse=True)
    await db.password_resets.create_index("token", unique=True)
    await db.password_resets.create_index("user_id")
    logger.info("Database indexes created")
    
    # Start Competition Auto-Bot
    asyncio.create_task(competition_auto_bot())
    logger.info("Competition Auto-Bot started")
    
    # Start Daily Email Bot (9:00 & 18:00 Romania time)
    asyncio.create_task(daily_email_bot())
    logger.info("Daily Email Bot started (sends at 9:00 & 18:00 Romania time)")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
# Force deploy Mon Mar  2 10:59:20 UTC 2026
