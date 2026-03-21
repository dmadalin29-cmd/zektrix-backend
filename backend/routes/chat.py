# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, Request, Response, Query, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials
from database import db
from dependencies import get_current_user, get_admin_user, create_access_token, verify_password, hash_password, pwd_context, security
from config import *
try:
    from models import *
except ImportError:
    from backend.models import *
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import uuid, random, json, os, asyncio, httpx, logging

logger = logging.getLogger("server")

from helpers import notify_user_push
from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter(prefix="/api")
chat_sessions = {}

# ==================== SOCIAL SHARING ====================

@router.get("/share/competition/{competition_id}")
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

@router.get("/share/winner/{winner_id}")
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

@router.post("/notifications/subscribe")
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

@router.delete("/notifications/unsubscribe")
async def unsubscribe_push_notifications(current_user: dict = Depends(get_current_user)):
    """Unsubscribe user from push notifications"""
    user_id = current_user["user_id"]
    
    await db.push_subscriptions.delete_one({"user_id": user_id})
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"push_notifications_enabled": False}}
    )
    
    return {"success": True, "message": "Unsubscribed from push notifications"}

@router.get("/notifications/status")
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

# WebSocket: exported to server.py
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

# WebSocket: exported to server.py
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

@router.post("/chat/ai")
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

@router.get("/push/vapid-key")
async def get_vapid_key():
    """Return VAPID public key for push notification subscription"""
    return {"public_key": VAPID_PUBLIC_KEY}

@router.post("/push/subscribe")
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

@router.get("/push/status")
async def push_status(current_user: dict = Depends(get_current_user)):
    """Check if user has an active push subscription"""
    sub = await db.push_subscriptions.find_one({"user_id": current_user["user_id"]}, {"_id": 0, "endpoint": 1})
    return {"subscribed": bool(sub)}

@router.post("/push/unsubscribe")
async def push_unsubscribe(current_user: dict = Depends(get_current_user)):
    """Unsubscribe from push notifications"""
    await db.push_subscriptions.delete_one({"user_id": current_user["user_id"]})
    return {"message": "Unsubscribed"}

@router.post("/push/test")
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

@router.post("/chat/escalate")
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

@router.get("/chat/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    """Get user's chat history"""
    messages = await db.chat_messages.find(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    ).sort("created_at", 1).to_list(50)
    return messages

@router.post("/chat/message")
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

@router.get("/chat/faq")
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

@router.get("/admin/chat/messages")
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

@router.put("/admin/chat/{message_id}/status")
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

@router.delete("/admin/chat/{message_id}")
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

@router.post("/admin/chat/reply-email")
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

@router.post("/admin/chat/reply")
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

