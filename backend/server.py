# -*- coding: utf-8 -*-
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, Query, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
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

# Health endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "ok", "service": "zektrix-backend"}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    balance: float
    role: str
    picture: Optional[str] = None
    created_at: datetime

class QualificationQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int  # Index of correct answer (0, 1, or 2)

class PostalEntry(BaseModel):
    company_name: str = "Zektrix UK Ltd"
    address_line1: str = "c/o Bartle House"
    address_line2: str = "Oxford Court, Manchester"
    postcode: str = "M23 WQ"
    country: str = "United Kingdom"
    instructions: List[str] = [
        "Nume complet",
        "Adresă poștală",
        "Email + Telefon",
        "Numele competiției"
    ]

class CompetitionCreate(BaseModel):
    title: str
    description: str
    ticket_price: float
    max_tickets: int
    competition_type: str  # "instant_win" or "classic"
    category: Optional[str] = "other"  # "instant_wins", "tech", "cash", "cars", "other"
    image_url: Optional[str] = None
    prize_description: Optional[str] = None
    draw_date: Optional[str] = None  # ISO date string for countdown
    qualification_question: Optional[QualificationQuestion] = None

class CompetitionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    ticket_price: Optional[float] = None
    max_tickets: Optional[int] = None
    competition_type: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None
    prize_description: Optional[str] = None
    draw_date: Optional[str] = None
    qualification_question: Optional[QualificationQuestion] = None
    postal_entry: Optional[PostalEntry] = None

class CompetitionResponse(BaseModel):
    competition_id: str
    title: str
    description: str
    ticket_price: float
    max_tickets: int
    sold_tickets: int
    competition_type: str
    category: Optional[str] = "other"
    status: str
    image_url: Optional[str] = None
    prize_description: Optional[str] = None
    draw_date: Optional[str] = None
    created_at: datetime
    winner_id: Optional[str] = None
    winner_ticket: Optional[int] = None
    qualification_question: Optional[QualificationQuestion] = None
    postal_entry: Optional[PostalEntry] = None

class TicketPurchase(BaseModel):
    competition_id: str
    quantity: int
    qualification_answer: Optional[int] = None  # Index of selected answer

# Cart models
class CartItem(BaseModel):
    competition_id: str
    quantity: int
    qualification_answer: Optional[int] = None

class CartPurchase(BaseModel):
    items: List[CartItem]
    payment_method: str = "wallet"  # "wallet" or "viva"

class TicketResponse(BaseModel):
    ticket_id: str
    user_id: str
    competition_id: str
    ticket_number: int
    purchased_at: datetime
    competition_title: Optional[str] = None
    competition_image: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        extra = "allow"

class WalletDeposit(BaseModel):
    amount: float

class TransactionResponse(BaseModel):
    transaction_id: str
    user_id: str
    transaction_type: str
    amount: float
    status: str
    description: Optional[str] = None
    created_at: datetime

class WinnerCreate(BaseModel):
    competition_id: str
    user_id: str
    ticket_number: int
    prize_description: Optional[str] = None

class WinnerResponse(BaseModel):
    winner_id: str
    competition_id: str
    competition_title: str
    user_id: str
    username: str
    ticket_number: int
    prize_description: Optional[str] = None
    announced_at: datetime
    is_automatic: bool

class TicketSearchResult(BaseModel):
    username: str
    tickets: List[TicketResponse]

# Referral models
class ReferralCreate(BaseModel):
    referrer_code: str

class ReferralResponse(BaseModel):
    referral_id: str
    referrer_id: str
    referred_id: str
    status: str
    bonus_amount: float
    created_at: datetime

# Analytics models
class AnalyticsResponse(BaseModel):
    total_revenue: float
    total_users: int
    total_tickets: int
    total_competitions: int
    active_competitions: int
    completed_competitions: int
    total_winners: int
    avg_tickets_per_user: float
    revenue_by_day: List[dict]
    top_competitions: List[dict]

# Push Notification models
class PushSubscription(BaseModel):
    endpoint: str
    keys: dict  # Contains p256dh and auth keys

class NotificationPreferences(BaseModel):
    push_enabled: bool = True
    competition_alerts: bool = True  # Alert when competition reaches 80%
    winner_alerts: bool = True  # Alert when you win

# Lucky Wheel Models
class SpinResult(BaseModel):
    prize_type: str  # 'cash', 'ticket', 'nothing', 'bonus_percent'
    prize_value: float
    message: str

# Flash Sale Competition
class FlashSaleCreate(BaseModel):
    competition_id: str
    discount_percent: int = 20
    duration_hours: int = 2

# Chat Message
class ChatMessage(BaseModel):
    message: str
    is_faq: bool = False

# Password Reset
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# Admin User Management
class AdminUserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    balance: Optional[float] = None
    is_blocked: Optional[bool] = None
    new_password: Optional[str] = None

# Email helper functions
async def send_winner_notification_email(winner_email: str, winner_name: str, competition_title: str, prize_description: str, ticket_number: int):
    """Send email notification to winner"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping email")
        return None
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #1a1a2e; color: white; padding: 40px; border-radius: 16px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d946ef; margin: 0;">FELICITARI!</h1>
            <h2 style="color: white; margin-top: 10px;">Ai câștigat!</h2>
        </div>
        
        <div style="background: linear-gradient(135deg, #d946ef33, #8b5cf633); padding: 30px; border-radius: 12px; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 18px;">Dragă <strong>{winner_name}</strong>,</p>
            <p style="margin-top: 15px;">Suntem încântați să te anunțăm că ești câștigătorul competiției:</p>
            <h3 style="color: #d946ef; font-size: 24px; margin: 20px 0;">{competition_title}</h3>
            <p><strong>Premiu:</strong> {prize_description or 'Vezi detalii pe site'}</p>
            <p><strong>Număr loc câștigător:</strong> #{ticket_number}</p>
        </div>
        
        <div style="background: #2a2a4e; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
            <h4 style="color: #8b5cf6; margin-top: 0;">Următorii pași:</h4>
            <ol style="padding-left: 20px;">
                <li style="margin-bottom: 10px;">Te vom contacta în 24-48 ore cu instrucțiuni detaliate</li>
                <li style="margin-bottom: 10px;">Pregătește-ți documentele de identitate pentru verificare</li>
                <li>Verifică folderul spam pentru a nu rata comunicările noastre</li>
            </ol>
        </div>
        
        <p style="text-align: center; color: #888; font-size: 14px;">
            Cu drag,<br/>
            <strong style="color: white;">Echipa Zektrix UK</strong>
        </p>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #333;">
            <a href="https://zektrix.uk" style="color: #d946ef; text-decoration: none;">zektrix.uk</a>
        </div>
    </div>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [winner_email],
            "subject": f"[CASTIGATOR] Felicitari! Ai castigat la {competition_title}!",
            "html": html_content
        }
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Winner notification email sent to {winner_email}")
        return email.get("id")
    except Exception as e:
        logger.error(f"Failed to send winner email: {str(e)}")
        return None

async def send_welcome_email(user_email: str, username: str, referral_code: str):
    """Send welcome email to new user"""
    if not RESEND_API_KEY:
        return None
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #1a1a2e; color: white; padding: 40px; border-radius: 16px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d946ef; margin: 0;">Bine ai venit!</h1>
            <h2 style="color: white; margin-top: 10px;">la Zektrix UK</h2>
        </div>
        
        <p>Salut <strong>{username}</strong>,</p>
        <p>Îți mulțumim că te-ai alăturat platformei noastre de competiții!</p>
        
        <div style="background: linear-gradient(135deg, #d946ef33, #8b5cf633); padding: 20px; border-radius: 12px; margin: 20px 0;">
            <h4 style="color: #d946ef; margin-top: 0;">Codul tău de referral:</h4>
            <p style="font-size: 24px; text-align: center; background: #2a2a4e; padding: 15px; border-radius: 8px; font-family: monospace; letter-spacing: 2px;">
                {referral_code}
            </p>
            <p style="font-size: 14px; text-align: center; margin-bottom: 0;">Invită prieteni și câștigi £5 pentru fiecare!</p>
        </div>
        
        <p style="text-align: center;">
            <a href="https://zektrix.uk/competitions" style="display: inline-block; background: linear-gradient(135deg, #d946ef, #8b5cf6); color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                Vezi Competițiile
            </a>
        </p>
        
        <p style="text-align: center; color: #888; font-size: 14px; margin-top: 30px;">
            Cu drag,<br/>
            <strong style="color: white;">Echipa Zektrix UK</strong>
        </p>
    </div>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [user_email],
            "subject": "[ZEKTRIX] Bine ai venit la Zektrix UK!",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Welcome email sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")

async def send_password_reset_email(user_email: str, username: str, reset_token: str):
    """Send password reset email"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping email")
        return None
    
    reset_link = f"https://zektrix.uk/reset-password?token={reset_token}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #1a1a2e; color: white; padding: 40px; border-radius: 16px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d946ef; margin: 0;">Resetare Parolă</h1>
        </div>
        
        <p>Salut <strong>{username}</strong>,</p>
        <p>Am primit o cerere de resetare a parolei pentru contul tău Zektrix UK.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #d946ef, #8b5cf6); color: white; padding: 15px 40px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 16px;">
                Resetează Parola
            </a>
        </div>
        
        <p style="color: #888; font-size: 14px;">Acest link este valid pentru 1 oră.</p>
        <p style="color: #888; font-size: 14px;">Dacă nu ai cerut această resetare, ignoră acest email.</p>
        
        <div style="border-top: 1px solid #333; margin-top: 30px; padding-top: 20px; text-align: center;">
            <p style="color: #888; font-size: 12px;">Cu drag, Echipa Zektrix UK</p>
        </div>
    </div>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [user_email],
            "subject": "[ZEKTRIX] Resetare Parola - Zektrix UK",
            "html": html_content
        }
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Password reset email sent to {user_email}")
        return email.get("id")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return None

async def send_competition_75_percent_email(user_email: str, username: str, competition_title: str, sold_percent: int):
    """Send email when competition reaches 75%+ sold"""
    if not RESEND_API_KEY:
        return None
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #1a1a2e; color: white; padding: 40px; border-radius: 16px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #f97316; margin: 0;">Aproape Sold Out!</h1>
        </div>
        
        <p>Salut <strong>{username}</strong>,</p>
        <p>Competiția <strong style="color: #d946ef;">{competition_title}</strong> este aproape terminată!</p>
        
        <div style="background: linear-gradient(135deg, #f9731633, #d946ef33); padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center;">
            <p style="font-size: 48px; margin: 0; font-weight: bold; color: #f97316;">{sold_percent}%</p>
            <p style="margin: 10px 0 0 0; color: #888;">din locuri vândute</p>
        </div>
        
        <p style="text-align: center;">
            <a href="https://zektrix.uk/competitions" style="display: inline-block; background: linear-gradient(135deg, #f97316, #d946ef); color: white; padding: 15px 40px; border-radius: 12px; text-decoration: none; font-weight: bold;">
                Rezervă-ți Locul Acum!
            </a>
        </p>
        
        <div style="border-top: 1px solid #333; margin-top: 30px; padding-top: 20px; text-align: center;">
            <p style="color: #888; font-size: 12px;">Cu drag, Echipa Zektrix UK</p>
        </div>
    </div>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [user_email],
            "subject": f"[HOT] {sold_percent}% Vandut! {competition_title} - Zektrix UK",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"75% alert email sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send 75% alert email: {str(e)}")

async def send_daily_digest_email(user_email: str, username: str, new_competitions: list, ending_soon: list):
    """Send daily digest email with new competitions and ending soon"""
    if not RESEND_API_KEY or (not new_competitions and not ending_soon):
        return None
    
    new_comps_html = ""
    if new_competitions:
        new_comps_html = """
        <div style="margin-bottom: 30px;">
            <h3 style="color: #d946ef; margin-bottom: 15px;">🆕 Competiții Noi</h3>
        """
        for comp in new_competitions[:5]:
            new_comps_html += f"""
            <div style="background: #2a2a4e; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                <p style="margin: 0; font-weight: bold;">{comp.get('title', 'N/A')}</p>
                <p style="margin: 5px 0 0 0; color: #888; font-size: 14px;">Preț loc: RON {comp.get('ticket_price', 0):.2f}</p>
            </div>
            """
        new_comps_html += "</div>"
    
    ending_html = ""
    if ending_soon:
        ending_html = """
        <div style="margin-bottom: 30px;">
            <h3 style="color: #f97316; margin-bottom: 15px;">⏰ Se Termină Curând</h3>
        """
        for comp in ending_soon[:5]:
            sold_percent = int((comp.get('sold_tickets', 0) / max(comp.get('max_tickets', 1), 1)) * 100)
            ending_html += f"""
            <div style="background: linear-gradient(135deg, #f9731620, #d946ef20); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #f9731640;">
                <p style="margin: 0; font-weight: bold;">{comp.get('title', 'N/A')}</p>
                <p style="margin: 5px 0 0 0; color: #f97316; font-size: 14px;">{sold_percent}% vândut - Grăbește-te!</p>
            </div>
            """
        ending_html += "</div>"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #1a1a2e; color: white; padding: 40px; border-radius: 16px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d946ef; margin: 0;">Update Zilnic Zektrix</h1>
            <p style="color: #888; margin-top: 10px;">Salut {username}, iată ce e nou!</p>
        </div>
        
        {new_comps_html}
        {ending_html}
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="https://zektrix.uk/competitions" style="display: inline-block; background: linear-gradient(135deg, #d946ef, #8b5cf6); color: white; padding: 15px 40px; border-radius: 12px; text-decoration: none; font-weight: bold;">
                Vezi Toate Competițiile
            </a>
        </div>
        
        <div style="border-top: 1px solid #333; margin-top: 30px; padding-top: 20px; text-align: center;">
            <p style="color: #888; font-size: 12px;">Cu drag, Echipa Zektrix UK</p>
            <p style="color: #666; font-size: 11px;">Pentru a dezactiva emailurile zilnice, accesează setările contului tău.</p>
        </div>
    </div>
    """
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [user_email],
            "subject": "[ZEKTRIX] Update Zilnic - Competitii Noi si Aproape Terminate | Zektrix UK",
            "html": html_content
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Daily digest sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send daily digest: {str(e)}")

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

class ProfileUpdate(BaseModel):
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

@api_router.put("/auth/profile")
async def update_profile(profile: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update user profile (phone, name, etc.)"""
    update_data = {}
    if profile.phone:
        update_data["phone"] = profile.phone
    if profile.first_name:
        update_data["first_name"] = profile.first_name
    if profile.last_name:
        update_data["last_name"] = profile.last_name
    
    if update_data:
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data}
        )
    
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

@api_router.get("/competitions", response_model=List[CompetitionResponse])
async def get_competitions(status: Optional[str] = None, competition_type: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    if competition_type:
        query["competition_type"] = competition_type
    
    competitions = await db.competitions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return competitions

@api_router.get("/competitions/{competition_id}", response_model=CompetitionResponse)
async def get_competition(competition_id: str):
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return comp

@api_router.get("/competitions/{competition_id}/tickets", response_model=List[TicketResponse])
async def get_competition_tickets(competition_id: str):
    tickets = await db.tickets.find({"competition_id": competition_id}, {"_id": 0}).to_list(10000)
    return tickets

# ==================== TICKET PURCHASE ====================

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
    
    # Record transaction
    await db.transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user["user_id"],
        "transaction_type": "ticket_purchase",
        "amount": -total_cost,
        "status": "completed",
        "description": f"Achiziție {purchase.quantity} {'loc' if purchase.quantity == 1 else 'locuri'} pentru {comp['title']}",
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
            "customerTrns": f"Cart: {len(cart.items)} competitions",
            "customer": {
                "email": current_user.get("email", ""),
                "fullName": current_user.get("username", "")
            },
            "merchantTrns": pending_id,
            "sourceCode": "9806",
            "successUrl": "https://zektrix.uk/payment/success",
            "failureUrl": "https://zektrix.uk/payment/failed"
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
            "customerTrns": f"{'Loc' if purchase.quantity == 1 else 'Locuri'} pentru {comp['title']} - {purchase.quantity} {'loc' if purchase.quantity == 1 else 'locuri'}",
            "customer": {
                "email": current_user["email"],
                "fullName": current_user.get("username", "User"),
                "requestLang": "en-GB"
            },
            "merchantTrns": pending_purchase_id,
            "paymentTimeout": 1800,
            "sourceCode": "9806",
            "successUrl": "https://zektrix.uk/payment/success",
            "failureUrl": "https://zektrix.uk/payment/failed"
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
                "description": f"Achiziție {purchase.quantity} {'loc' if purchase.quantity == 1 else 'locuri'} pentru {comp['title']}",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            checkout_url = f"{VIVA_CHECKOUT_URL}?ref={order_code}"
            return {"checkout_url": checkout_url, "order_code": order_code, "transaction_id": transaction_id}
    
    except httpx.HTTPError as e:
        logger.error(f"Payment error: {e}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")

# ==================== WALLET & PAYMENTS ====================

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

# Wallet deposit removed - direct payments only

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
                
                # Check if user has deposit bonus from Lucky Wheel
                if user and user.get("next_deposit_bonus"):
                    bonus_percent = user.get("next_deposit_bonus", 0)
                    bonus_max = user.get("next_deposit_bonus_max", 50)  # Default max 50 RON
                    
                    # Calculate bonus (percentage of deposit, capped at max)
                    calculated_bonus = deposit_amount * (bonus_percent / 100)
                    bonus_amount = min(calculated_bonus, bonus_max)
                    
                    # Clear the bonus after applying
                    await db.users.update_one(
                        {"user_id": transaction["user_id"]},
                        {
                            "$unset": {"next_deposit_bonus": "", "next_deposit_bonus_max": "", "milestone_bonus": ""}
                        }
                    )
                    
                    logger.info(f"Applied {bonus_percent}% bonus: {bonus_amount} RON for user {transaction['user_id']}")
                
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
        "ticket_price": comp.ticket_price,
        "max_tickets": comp.max_tickets,
        "sold_tickets": 0,
        "competition_type": comp.competition_type,
        "category": comp.category or "other",
        "status": "active",
        "image_url": comp.image_url,
        "prize_description": comp.prize_description,
        "draw_date": comp.draw_date,
        "qualification_question": qual_question,
        "postal_entry": DEFAULT_POSTAL_ENTRY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "winner_id": None,
        "winner_ticket": None,
        "seo": None  # Will be generated automatically
    }
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
    search: Optional[str] = None
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
    
    tickets = await db.tickets.find(query, {"_id": 0}).sort("purchased_at", -1).to_list(10000)
    
    # Add user details and competition title to tickets
    for ticket in tickets:
        user = await db.users.find_one({"user_id": ticket["user_id"]}, {"_id": 0})
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
        
        # Add competition title
        comp = await db.competitions.find_one({"competition_id": ticket["competition_id"]}, {"_id": 0})
        ticket["competition_title"] = comp.get("title", "Unknown") if comp else "Unknown"
    
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

@api_router.get("/admin/analytics")
async def get_analytics(admin: dict = Depends(get_admin_user)):
    """Get comprehensive analytics for admin dashboard"""
    # Basic counts
    total_users = await db.users.count_documents({})
    total_tickets = await db.tickets.count_documents({})
    total_competitions = await db.competitions.count_documents({})
    active_competitions = await db.competitions.count_documents({"status": "active"})
    completed_competitions = await db.competitions.count_documents({"status": "completed"})
    total_winners = await db.winners.count_documents({})
    
    # Revenue calculation from completed transactions
    transactions = await db.transactions.find(
        {"status": "completed", "transaction_type": {"$in": ["deposit", "ticket_purchase", "ticket_purchase_viva"]}},
        {"_id": 0}
    ).to_list(10000)
    
    total_revenue = sum(abs(t.get("amount", 0)) for t in transactions if t.get("amount", 0) > 0)
    
    # Average tickets per user
    avg_tickets = total_tickets / total_users if total_users > 0 else 0
    
    # Revenue by day (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    recent_transactions = await db.transactions.find(
        {"status": "completed", "created_at": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).to_list(10000)
    
    revenue_by_day = {}
    for t in recent_transactions:
        if t.get("amount", 0) > 0:
            day = t.get("created_at", "")[:10]
            revenue_by_day[day] = revenue_by_day.get(day, 0) + t["amount"]
    
    revenue_by_day_list = [{"date": k, "revenue": v} for k, v in sorted(revenue_by_day.items())]
    
    # Top competitions by tickets sold
    competitions = await db.competitions.find({}, {"_id": 0}).sort("sold_tickets", -1).to_list(10)
    top_competitions = [
        {"title": c["title"], "sold": c["sold_tickets"], "max": c["max_tickets"], "revenue": c["sold_tickets"] * c["ticket_price"]}
        for c in competitions
    ]
    
    # User growth by day (last 30 days)
    users = await db.users.find({"created_at": {"$gte": thirty_days_ago}}, {"_id": 0, "created_at": 1}).to_list(10000)
    user_growth = {}
    for u in users:
        day = u.get("created_at", "")[:10]
        user_growth[day] = user_growth.get(day, 0) + 1
    
    user_growth_list = [{"date": k, "users": v} for k, v in sorted(user_growth.items())]
    
    # Referral stats
    total_referrals = await db.referrals.count_documents({"status": "completed"})
    referral_bonus_paid = total_referrals * 5  # £5 per referral
    
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
        "referral_bonus_paid": referral_bonus_paid
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
    """Send push notifications when competition reaches 80% sold"""
    percentage = (sold_tickets / max_tickets) * 100 if max_tickets > 0 else 0
    
    # Check if we should send alert (at 80%)
    if percentage >= 80 and percentage < 85:
        # Get competition details
        comp = await db.competitions.find_one({"competition_id": competition_id})
        if not comp:
            return
        
        # Check if alert was already sent
        alert_key = f"alert_80_{competition_id}"
        existing_alert = await db.settings.find_one({"key": alert_key})
        if existing_alert:
            return
        
        # Mark alert as sent
        await db.settings.update_one(
            {"key": alert_key},
            {"$set": {"sent_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        
        # Get all subscribed users
        subscriptions = await db.push_subscriptions.find().to_list(1000)
        
        # Send notification to all subscribers
        for sub in subscriptions:
            try:
                # For now, broadcast via WebSocket (browser will show notification)
                await ws_manager.broadcast({
                    "type": "competition_alert",
                    "competition_id": competition_id,
                    "title": comp.get("title", "Competiție"),
                    "message": f"Doar {100 - int(percentage)}% bilete rămase!",
                    "percentage": int(percentage)
                })
            except Exception as e:
                logger.error(f"Failed to send push notification: {e}")
        
        logger.info(f"Competition {competition_id} reached 80% - alerts sent")

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
    await db.chat_messages.insert_one({
        "message_id": f"msg_{uuid.uuid4().hex[:12]}",
        "user_id": current_user["user_id"],
        "username": current_user.get("username", "Unknown"),
        "message": msg.message,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "type": "support",
        "response": "Mesajul tau a fost trimis echipei de suport. Vei primi un raspuns in curand pe email!",
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
async def get_pending_messages(admin: dict = Depends(get_admin_user)):
    """Get all chat messages with user info"""
    messages = await db.chat_messages.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with user info
    for msg in messages:
        user = await db.users.find_one({"user_id": msg.get("user_id")}, {"_id": 0, "email": 1, "first_name": 1, "last_name": 1})
        if user:
            msg["user_email"] = user.get("email")
            msg["user_first_name"] = user.get("first_name")
            msg["user_last_name"] = user.get("last_name")
    
    return messages

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
    
    # Broadcast to WebSocket if user is online
    await ws_manager.broadcast_all({
        "type": "chat_reply",
        "user_id": original["user_id"],
        "reply": reply.reply,
        "message_id": reply.message_id
    })
    
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
        await auto_draw_winner(active_perm["competition_id"])
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
        "image_url": "https://images.unsplash.com/photo-1621981386829-9b458a2cddde?w=800&q=80",  # Cash/money image
        "prize_description": f"{template['prize_amount']} RON în numerar",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_auto_managed": True,
        "auto_prize_amount": template["prize_amount"],
        "qualification_question": {
            "question": "Cât de mult este premiul acestei competiții?",
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
                logger.info("[PERMANENT-BOT] Permanent competition full! Drawing winner...")
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
    """Generate ultra-modern email HTML for daily digest with GDPR footer"""
    
    # Sort competitions by progress (most filled first for urgency)
    sorted_comps = sorted(competitions, key=lambda x: (x.get("sold_tickets", 0) / max(x.get("max_tickets", 1), 1)), reverse=True)
    
    # Calculate totals
    total_prizes = sum(comp.get("auto_prize_amount", 0) for comp in sorted_comps if comp.get("auto_prize_amount"))
    total_tickets_available = sum(comp.get("max_tickets", 0) - comp.get("sold_tickets", 0) for comp in sorted_comps)
    
    # Hot competitions (>60% sold)
    hot_comps = [c for c in sorted_comps if (c.get("sold_tickets", 0) / max(c.get("max_tickets", 1), 1)) > 0.6]
    
    # Generate competition cards
    comp_cards = ""
    for comp in sorted_comps[:5]:  # Max 5 competitions
        progress = int((comp.get("sold_tickets", 0) / max(comp.get("max_tickets", 1), 1)) * 100)
        remaining = comp.get("max_tickets", 0) - comp.get("sold_tickets", 0)
        prize = comp.get("prize_description", comp.get("title", "Premiu"))
        
        # Urgency color based on progress
        if progress >= 80:
            urgency_color = "#ef4444"  # Red
            urgency_text = "APROAPE PLIN!"
            border_color = "#ef444450"
        elif progress >= 60:
            urgency_color = "#f97316"  # Orange
            urgency_text = "SE UMPLE RAPID!"
            border_color = "#f9731650"
        else:
            urgency_color = "#8b5cf6"  # Violet
            urgency_text = ""
            border_color = "#8b5cf650"
        
        comp_cards += f'''
                    <tr>
                        <td style="padding: 0 0 15px 0;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #0f0a1a 0%, #1a1033 100%); border: 1px solid {border_color}; border-radius: 16px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 0;">
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="padding: 20px;">
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                                        <tr>
                                                            <td>
                                                                <h3 style="color: #ffffff; margin: 0 0 5px 0; font-size: 18px; font-weight: 700;">{comp.get("title", "Competiție")}</h3>
                                                                {f'<span style="color: {urgency_color}; font-size: 11px; font-weight: 700;">{urgency_text}</span>' if urgency_text else ''}
                                                            </td>
                                                            <td style="text-align: right; vertical-align: top;">
                                                                <span style="background: linear-gradient(135deg, #8b5cf6, #f97316); color: white; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-block;">{comp.get("ticket_price", 0):.2f} RON</span>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    <p style="color: #6b7280; margin: 10px 0 15px 0; font-size: 13px;">Premiu: <strong style="color: #fbbf24;">{prize}</strong></p>
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 12px;">
                                                        <tr>
                                                            <td style="background: #1f1f3a; border-radius: 8px; height: 10px; overflow: hidden;">
                                                                <div style="background: linear-gradient(90deg, {urgency_color}, #f97316); height: 10px; width: {progress}%; border-radius: 8px;"></div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                                        <tr>
                                                            <td style="color: #9ca3af; font-size: 12px;">
                                                                <span style="color: {urgency_color}; font-weight: 700;">{progress}%</span> ocupat • <strong style="color: #10b981;">{remaining} locuri libere</strong>
                                                            </td>
                                                            <td style="text-align: right;">
                                                                <a href="https://zektrix.uk/competitions/{comp.get('competition_id', '')}" style="color: #8b5cf6; text-decoration: none; font-size: 12px; font-weight: 600;">Vezi Detalii →</a>
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
    
    # Hot alert section (if any hot competitions)
    hot_count = len(hot_comps)
    hot_alert_html = ""
    if hot_comps:
        hot_alert_html = f'''<!-- Hot Alert -->
                    <tr>
                        <td style="padding-bottom: 20px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%); border: 1px solid #ef444450; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 15px 20px; text-align: center;">
                                        <p style="color: #fca5a5; margin: 0; font-size: 13px;">
                                            &#128293; <strong style="color: #ffffff;">{hot_count} competitii</strong> sunt aproape pline! Nu rata sansa!
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''
    
    # Recent winners (last 3)
    recent_winners = await db.winners.find({}, {"_id": 0}).sort("announced_at", -1).limit(3).to_list(3)
    winners_html = ""
    if recent_winners:
        winners_html = '''
                    <tr>
                        <td style="padding: 30px 0 20px 0;">
                            <p style="color: #fbbf24; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin: 0; font-weight: 700;">&#127942; Castigatori Recenti</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding-bottom: 30px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                <tr>'''
        for winner in recent_winners:
            winners_html += f'''
                                    <td style="width: 32%; background: linear-gradient(135deg, #1a1033, #0f0a1a); border: 1px solid #fbbf2430; border-radius: 12px; padding: 15px; text-align: center; vertical-align: top;">
                                        <div style="font-size: 24px; margin-bottom: 8px;">&#127881;</div>
                                        <p style="color: #ffffff; margin: 0 0 4px 0; font-size: 13px; font-weight: 600;">{winner.get("username", "Câștigător")}</p>
                                        <p style="color: #fbbf24; margin: 0; font-size: 11px;">#{winner.get("ticket_number", "?")}</p>
                                    </td>
                                    <td style="width: 2%;"></td>'''
        winners_html = winners_html.rstrip('<td style="width: 2%;"></td>')
        winners_html += '''
                                </tr>
                            </table>
                        </td>
                    </tr>'''
    
    email_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zektrix - Competiții Zilnice</title>
</head>
<body style="margin: 0; padding: 0; background-color: #030014; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table cellpadding="0" cellspacing="0" style="width: 100%; background-color: #030014;">
        <tr>
            <td style="padding: 40px 20px;">
                <table cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; width: 100%;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="text-align: center; padding-bottom: 30px;">
                            <h1 style="margin: 0; font-size: 36px; font-weight: 900; letter-spacing: -1px;">
                                <span style="color: #8b5cf6;">ZEKTRIX</span><span style="color: #ffffff;">.UK</span>
                            </h1>
                            <p style="color: #6b7280; margin-top: 8px; font-size: 13px;">Premii reale. Șanse reale. Câștigători reali.</p>
                        </td>
                    </tr>
                    
                    <!-- Personal Greeting -->
                    <tr>
                        <td style="padding-bottom: 25px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #1a1033 0%, #0f0a1a 100%); border: 1px solid #8b5cf650; border-radius: 20px;">
                                <tr>
                                    <td style="padding: 30px; text-align: center;">
                                        <p style="color: #9ca3af; margin: 0 0 5px 0; font-size: 14px;">Salut,</p>
                                        <h2 style="color: #ffffff; margin: 0 0 15px 0; font-size: 26px; font-weight: 800;">{user_name}!</h2>
                                        <p style="color: #9ca3af; margin: 0; font-size: 15px; line-height: 1.6;">
                                            Avem <strong style="color: #8b5cf6;">{len(sorted_comps)} competiții active</strong> cu premii totale de 
                                            <strong style="color: #fbbf24;">{total_prizes:,.0f} RON</strong>!
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Stats Bar -->
                    <tr>
                        <td style="padding-bottom: 25px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                <tr>
                                    <td style="width: 32%; background: #0f0a1a; border: 1px solid #8b5cf630; border-radius: 12px; padding: 18px; text-align: center;">
                                        <div style="font-size: 28px; margin-bottom: 8px;">&#127919;</div>
                                        <p style="color: #8b5cf6; margin: 0 0 4px 0; font-size: 22px; font-weight: 800;">{len(sorted_comps)}</p>
                                        <p style="color: #6b7280; margin: 0; font-size: 11px;">Competitii Active</p>
                                    </td>
                                    <td style="width: 2%;"></td>
                                    <td style="width: 32%; background: #0f0a1a; border: 1px solid #f9731630; border-radius: 12px; padding: 18px; text-align: center;">
                                        <div style="font-size: 28px; margin-bottom: 8px;">&#127915;</div>
                                        <p style="color: #f97316; margin: 0 0 4px 0; font-size: 22px; font-weight: 800;">{total_tickets_available}</p>
                                        <p style="color: #6b7280; margin: 0; font-size: 11px;">Locuri Disponibile</p>
                                    </td>
                                    <td style="width: 2%;"></td>
                                    <td style="width: 32%; background: #0f0a1a; border: 1px solid #10b98130; border-radius: 12px; padding: 18px; text-align: center;">
                                        <div style="font-size: 28px; margin-bottom: 8px;">&#128176;</div>
                                        <p style="color: #10b981; margin: 0 0 4px 0; font-size: 22px; font-weight: 800;">{total_prizes:,.0f}</p>
                                        <p style="color: #6b7280; margin: 0; font-size: 11px;">RON Premii</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    {hot_alert_html}
                    
                    <!-- Section Title -->
                    <tr>
                        <td style="padding-bottom: 15px;">
                            <p style="color: #a78bfa; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin: 0; font-weight: 700;">&#128203; Competitii Active</p>
                        </td>
                    </tr>
                    
                    <!-- Competition Cards -->
                    {comp_cards}
                    
                    <!-- CTA Button -->
                    <tr>
                        <td style="text-align: center; padding: 25px 0 35px 0;">
                            <a href="https://zektrix.uk/competitions" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6, #f97316); color: white; text-decoration: none; padding: 18px 50px; border-radius: 12px; font-weight: 700; font-size: 16px;">
                                PARTICIPĂ ACUM →
                            </a>
                        </td>
                    </tr>
                    
                    {winners_html}
                    
                    <!-- Features -->
                    <tr>
                        <td style="padding-bottom: 30px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #0f0a1a, #1a1033); border: 1px solid #8b5cf620; border-radius: 16px;">
                                <tr>
                                    <td style="padding: 25px;">
                                        <p style="color: #ffffff; margin: 0 0 15px 0; font-size: 15px; font-weight: 700; text-align: center;">De ce să alegi Zektrix?</p>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="width: 50%; padding: 10px;">
                                                    <p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Extrageri automate transparente</p>
                                                </td>
                                                <td style="width: 50%; padding: 10px;">
                                                    <p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Premii platite instant</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="width: 50%; padding: 10px;">
                                                    <p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Bilete de la 7.99 RON</p>
                                                </td>
                                                <td style="width: 50%; padding: 10px;">
                                                    <p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Suport 24/7 pe WhatsApp</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- GDPR Modern Footer -->
                    <tr>
                        <td style="padding-top: 40px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #0f0a1a 0%, #1a0a2e 50%, #0f0a1a 100%); border: 1px solid #8b5cf630; border-radius: 24px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 35px 30px;">
                                        <!-- Logo & Tagline -->
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 25px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <h3 style="margin: 0; font-size: 28px; font-weight: 900; letter-spacing: -1px;">
                                                        <span style="background: linear-gradient(135deg, #8b5cf6, #d946ef, #f97316); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">ZEKTRIX</span><span style="color: #ffffff;">.UK</span>
                                                    </h3>
                                                    <p style="color: #6b7280; margin: 8px 0 0 0; font-size: 12px; letter-spacing: 1px;">PREMII REALE &#8226; SANSE REALE &#8226; CASTIGATORI REALI</p>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- Social Links -->
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 25px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <a href="https://zektrix.uk" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; text-decoration: none; padding: 10px 20px; border-radius: 25px; font-size: 12px; font-weight: 600; margin: 0 5px;">&#127760; Website</a>
                                                    <a href="https://wa.me/40730268067" style="display: inline-block; background: linear-gradient(135deg, #22c55e, #16a34a); color: white; text-decoration: none; padding: 10px 20px; border-radius: 25px; font-size: 12px; font-weight: 600; margin: 0 5px;">&#128172; WhatsApp</a>
                                                    <a href="https://tiktok.com/@zektrix.uk" style="display: inline-block; background: linear-gradient(135deg, #000000, #1a1a1a); color: white; text-decoration: none; padding: 10px 20px; border-radius: 25px; font-size: 12px; font-weight: 600; margin: 0 5px; border: 1px solid #333;">&#9835; TikTok</a>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- Divider -->
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 25px;">
                                            <tr>
                                                <td style="height: 1px; background: linear-gradient(90deg, transparent, #8b5cf650, transparent);"></td>
                                            </tr>
                                        </table>
                                        
                                        <!-- GDPR Info -->
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 20px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <p style="color: #9ca3af; font-size: 11px; margin: 0 0 10px 0; line-height: 1.6;">
                                                        Ai primit acest email pentru ca esti inregistrat pe <strong style="color: #8b5cf6;">Zektrix.uk</strong>
                                                    </p>
                                                    <p style="color: #6b7280; font-size: 10px; margin: 0 0 15px 0; line-height: 1.5;">
                                                        Conform GDPR, ai dreptul sa iti gestionezi preferintele de comunicare.<br/>
                                                        Datele tale sunt in siguranta si nu sunt partajate cu terti.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- Quick Links -->
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 20px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <a href="https://zektrix.uk/faq" style="color: #8b5cf6; text-decoration: none; font-size: 11px; margin: 0 12px;">&#10067; FAQ</a>
                                                    <span style="color: #4b5563;">|</span>
                                                    <a href="https://zektrix.uk/privacy" style="color: #8b5cf6; text-decoration: none; font-size: 11px; margin: 0 12px;">&#128274; Confidentialitate</a>
                                                    <span style="color: #4b5563;">|</span>
                                                    <a href="https://zektrix.uk/terms" style="color: #8b5cf6; text-decoration: none; font-size: 11px; margin: 0 12px;">&#128196; Termeni</a>
                                                    <span style="color: #4b5563;">|</span>
                                                    <a href="https://zektrix.uk/dashboard" style="color: #8b5cf6; text-decoration: none; font-size: 11px; margin: 0 12px;">&#128100; Contul Meu</a>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- Unsubscribe Section -->
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0a0512; border-radius: 12px; margin-bottom: 20px;">
                                            <tr>
                                                <td style="padding: 20px; text-align: center;">
                                                    <p style="color: #6b7280; font-size: 11px; margin: 0 0 12px 0;">
                                                        Nu mai vrei sa primesti aceste email-uri?
                                                    </p>
                                                    <a href="https://zektrix.uk/unsubscribe/{user_id}" style="display: inline-block; background: transparent; color: #ef4444; text-decoration: none; padding: 8px 24px; border-radius: 20px; font-size: 11px; font-weight: 600; border: 1px solid #ef444450; transition: all 0.3s;">
                                                        &#128683; Dezabonare din newsletter
                                                    </a>
                                                    <p style="color: #4b5563; font-size: 10px; margin: 12px 0 0 0;">
                                                        Vei continua sa primesti email-uri importante despre contul tau.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- Copyright & Address -->
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <p style="color: #4b5563; font-size: 10px; margin: 0 0 8px 0;">
                                                        &#169; 2026 Zektrix UK Ltd. Toate drepturile rezervate.
                                                    </p>
                                                    <p style="color: #374151; font-size: 9px; margin: 0; line-height: 1.5;">
                                                        Zektrix UK Ltd &#8226; c/o Bartle House, Oxford Court &#8226; Manchester, M23 WQ &#8226; United Kingdom
                                                    </p>
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
        
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": [user["email"]],
            "subject": f"[ZEKTRIX] {len(competitions)} Competitii Active cu Premii de pana la 5000 RON!",
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

app.include_router(api_router)

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
