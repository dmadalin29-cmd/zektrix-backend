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

from helpers import notify_user_push, notify_competition_participants_push
try:
    from models import CompetitionCreate, CompetitionUpdate, CompetitionResponse, UserResponse, WinnerCreate, WinnerResponse, TicketResponse
    from email_service import send_winner_notification_email, send_competition_75_percent_email
except ImportError:
    from backend.models import CompetitionCreate, CompetitionUpdate, CompetitionResponse, UserResponse, WinnerCreate, WinnerResponse, TicketResponse
    from backend.email_service import send_winner_notification_email, send_competition_75_percent_email
from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter(prefix="/api")

# ==================== WINNERS ====================

@router.get("/winners", response_model=List[WinnerResponse])
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

@router.post("/admin/generate-ai-content")
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

@router.post("/admin/competitions", response_model=CompetitionResponse)
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
    
    # Distribute tickets to active subscribers
    if not comp.is_free and (comp.ticket_price or 0) <= MAX_ENTRY_PRICE_FOR_SUBSCRIPTION:
        asyncio.create_task(distribute_to_subscribers_for_competition(competition_id))
    
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

@router.put("/admin/competitions/{competition_id}", response_model=CompetitionResponse)
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

@router.delete("/admin/competitions/{competition_id}")
async def delete_competition(competition_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.competitions.delete_one({"competition_id": competition_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Competition not found")
    return {"message": "Competition deleted"}

@router.post("/admin/competitions/{competition_id}/generate-seo")
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

@router.post("/admin/competitions/{competition_id}/end")
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

@router.post("/admin/competitions/{competition_id}/draw-winner")
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

@router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(admin: dict = Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@router.put("/admin/users/{user_id}")
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

@router.delete("/admin/users/{user_id}")
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

@router.get("/admin/tickets", response_model=List[TicketResponse])
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

@router.post("/admin/winners", response_model=WinnerResponse)
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

@router.get("/admin/stats")
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

@router.get("/stats")
async def get_public_stats(response: Response):
    """Get public statistics for homepage"""
    response.headers["Cache-Control"] = "public, max-age=30"
    winners_count = await db.winners.count_documents({})
    users_count = await db.users.count_documents({})
    tickets_count = await db.tickets.count_documents({})
    
    return {
        "winners": winners_count,
        "users": users_count,
        "tickets": tickets_count
    }

# In-memory cache for recent activity (expensive query)
_activity_cache = {"data": None, "expires": 0}

@router.get("/activity/recent")
async def get_recent_activity(response: Response):
    """Get recent activity for live ticker (purchases, winners)"""
    import time
    now = time.time()
    if _activity_cache["data"] and now < _activity_cache["expires"]:
        response.headers["Cache-Control"] = "public, max-age=30"
        return _activity_cache["data"]
    
    activities = []
    
    # Use aggregation pipeline with $lookup instead of N+1 queries
    ticket_pipeline = [
        {"$sort": {"purchased_at": -1}},
        {"$limit": 10},
        {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "user_id", "as": "user_info"}},
        {"$lookup": {"from": "competitions", "localField": "competition_id", "foreignField": "competition_id", "as": "comp_info"}},
        {"$project": {"_id": 0, "purchased_at": 1, "user_info.username": 1, "comp_info.title": 1}}
    ]
    recent_tickets = await db.tickets.aggregate(ticket_pipeline).to_list(10)
    for t in recent_tickets:
        username = t.get("user_info", [{}])[0].get("username", "Anonim")[:15] if t.get("user_info") else "Anonim"
        title = t.get("comp_info", [{}])[0].get("title", "competitie")[:25] if t.get("comp_info") else "competitie"
        activities.append({"type": "purchase", "username": username, "message": f"a rezervat loc la {title}", "time": t.get("purchased_at", "")})
    
    winner_pipeline = [
        {"$sort": {"created_at": -1}},
        {"$limit": 5},
        {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "user_id", "as": "user_info"}},
        {"$lookup": {"from": "competitions", "localField": "competition_id", "foreignField": "competition_id", "as": "comp_info"}},
        {"$project": {"_id": 0, "created_at": 1, "user_info.username": 1, "comp_info.title": 1, "comp_info.prize_description": 1}}
    ]
    recent_winners = await db.winners.aggregate(winner_pipeline).to_list(5)
    for w in recent_winners:
        username = w.get("user_info", [{}])[0].get("username", "Anonim")[:15] if w.get("user_info") else "Anonim"
        comp_info = w.get("comp_info", [{}])[0] if w.get("comp_info") else {}
        title = comp_info.get("title", "competitie")[:25]
        activities.append({"type": "winner", "username": username, "message": f"a castigat {title}!", "time": w.get("created_at", "")})
    
    activities.sort(key=lambda x: x.get("time", ""), reverse=True)
    result = activities[:15]
    
    _activity_cache["data"] = result
    _activity_cache["expires"] = now + 30  # Cache 30 seconds
    response.headers["Cache-Control"] = "public, max-age=30"
    return result

# ==================== SITE SETTINGS (TikTok LIVE, etc.) ====================

@router.get("/settings/tiktok-live")
async def get_tiktok_live_status():
    """Get TikTok LIVE status (public endpoint)"""
    settings = await db.site_settings.find_one({"setting_id": "tiktok_live"})
    if not settings:
        return {"is_live": False, "tiktok_url": "https://www.tiktok.com/@x67digital"}
    return {
        "is_live": settings.get("is_live", False),
        "tiktok_url": settings.get("tiktok_url", "https://www.tiktok.com/@x67digital")
    }

@router.post("/admin/settings/tiktok-live")
async def set_tiktok_live_status(is_live: bool, tiktok_url: Optional[str] = None, admin: dict = Depends(get_admin_user)):
    """Toggle TikTok LIVE status (admin only) - also updates live-draw for competition pages and sends push"""
    final_url = tiktok_url or "https://www.tiktok.com/@x67digital"
    update_data = {"is_live": is_live, "updated_at": datetime.now(timezone.utc).isoformat(), "tiktok_url": final_url}
    
    await db.site_settings.update_one(
        {"setting_id": "tiktok_live"},
        {"$set": update_data},
        upsert=True
    )
    
    # Also update the live-draw settings (used by competition pages)
    live_draw_value = {
        "is_live": is_live,
        "competition_id": None,
        "tiktok_live_url": final_url,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.settings.update_one(
        {"key": "live_draw"},
        {"$set": {"key": "live_draw", "value": live_draw_value}},
        upsert=True
    )
    
    # Send push notification when going live
    if is_live:
        try:
            from push_service import send_web_push
        except ImportError:
            from backend.push_service import send_web_push
        
        subs = await db.push_subscriptions.find({}, {"_id": 0}).to_list(10000)
        sent = 0
        for sub in subs:
            try:
                await send_web_push(sub, {
                    "title": "LIVE DRAW ACUM!",
                    "body": "Suntem LIVE pe TikTok! Urmărește extragerea acum!",
                    "url": final_url,
                    "tag": "live-draw",
                    "requireInteraction": True
                })
                sent += 1
            except Exception:
                pass
        logger.info(f"Live toggle notification sent to {sent} devices")
    
    return {"success": True, "is_live": is_live, "message": f"TikTok LIVE {'activat' if is_live else 'dezactivat'}"}

@router.get("/settings/featured-competition")
async def get_featured_competition():
    """Get the featured/recommended competition for homepage"""
    setting = await db.site_settings.find_one({"setting_id": "featured_competition"})
    comp_id = setting.get("competition_id") if setting else None
    if comp_id:
        comp = await db.competitions.find_one({"competition_id": comp_id, "status": "active"}, {"_id": 0})
        if comp:
            return {"competition": comp}
    return {"competition": None}

@router.post("/admin/settings/featured-competition")
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


@router.post("/admin/notifications/read")
async def mark_admin_notifications_read(admin: dict = Depends(get_admin_user)):
    """Mark all current admin notifications as read"""
    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"user_id": admin["user_id"]},
        {"$set": {"notifications_read_at": now}}
    )
    return {"success": True, "read_at": now}

@router.get("/admin/notifications")
async def get_admin_notifications(admin: dict = Depends(get_admin_user)):
    """Get real-time admin notifications"""
    now = datetime.now(timezone.utc)
    notifications = []
    read_at = admin.get("notifications_read_at")
    
    # Pending withdrawals
    pending_wd = await db.withdrawal_requests.find(
        {"status": "pending"}, {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    for wd in pending_wd:
        notifications.append({
            "id": wd["withdrawal_id"],
            "type": "withdrawal",
            "title": "Cerere de retragere",
            "message": f"{wd.get('username', wd.get('email', 'User'))} cere £{wd['amount']:.2f}",
            "action_url": "wallet",
            "created_at": wd["created_at"],
            "priority": "high"
        })
    
    # New subscriptions (last 24h)
    yesterday = (now - timedelta(hours=24)).isoformat()
    recent_subs = await db.subscriptions.find(
        {"created_at": {"$gte": yesterday}, "status": {"$in": ["active", "pending_payment"]}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    for sub in recent_subs:
        notifications.append({
            "id": sub["subscription_id"],
            "type": "subscription",
            "title": "Abonament nou",
            "message": f"{sub.get('username', sub.get('email', 'User'))} - {sub['plan_name']}",
            "action_url": "wallet",
            "created_at": sub["created_at"],
            "priority": "medium"
        })
    
    # Competitions near full (>80%)
    comps = await db.competitions.find(
        {"status": "active"}, {"_id": 0, "competition_id": 1, "title": 1, "sold_tickets": 1, "max_tickets": 1}
    ).to_list(50)
    for c in comps:
        pct = (c["sold_tickets"] / c["max_tickets"] * 100) if c["max_tickets"] > 0 else 0
        if pct >= 80:
            notifications.append({
                "id": f"comp_{c['competition_id']}",
                "type": "competition_alert",
                "title": f"Competitie {int(pct)}% vanduta",
                "message": f"{c['title'][:40]} — {c['max_tickets'] - c['sold_tickets']} locuri ramase",
                "action_url": "comps",
                "created_at": now.isoformat(),
                "priority": "high" if pct >= 95 else "medium"
            })
    
    # Unanswered chat messages (waiting for admin)
    unread_chats = await db.chat_messages.find(
        {"sender": "user", "admin_read": {"$ne": True}},
        {"_id": 0, "user_id": 1, "username": 1, "message": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(10)
    for msg in unread_chats:
        notifications.append({
            "id": f"chat_{msg.get('user_id', '')}_{msg.get('created_at', '')}",
            "type": "chat",
            "title": "Mesaj nou",
            "message": f"{msg.get('username', 'User')}: {msg.get('message', '')[:50]}",
            "action_url": "chat",
            "created_at": msg.get("created_at", now.isoformat()),
            "priority": "medium"
        })
    
    # New users (last 24h)
    recent_users = await db.users.find(
        {"created_at": {"$gte": yesterday}},
        {"_id": 0, "user_id": 1, "username": 1, "email": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(10)
    for u in recent_users:
        notifications.append({
            "id": f"user_{u['user_id']}",
            "type": "new_user",
            "title": "Utilizator nou",
            "message": u.get("username", u.get("email", "?")),
            "action_url": "users",
            "created_at": u.get("created_at", now.isoformat()),
            "priority": "low"
        })
    
    # Sort by priority then date
    priority_order = {"high": 0, "medium": 1, "low": 2}
    notifications.sort(key=lambda n: (priority_order.get(n["priority"], 2), n.get("created_at", "")), reverse=False)
    notifications.sort(key=lambda n: priority_order.get(n["priority"], 2))
    
    # Calculate unread count based on read_at timestamp
    unread_count = len(notifications)
    if read_at:
        unread_count = sum(1 for n in notifications if n.get("created_at", "") > read_at)
    
    return {"notifications": notifications, "total": len(notifications), "unread_count": unread_count, "high_priority": sum(1 for n in notifications if n["priority"] == "high")}

@router.get("/admin/analytics")
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


# ==================== FLASH SALES ====================

@router.get("/competitions/flash-sales")
async def get_flash_sales():
    """Get active flash sale competitions"""
    now = datetime.now(timezone.utc)
    
    flash_sales = await db.competitions.find({
        "flash_sale.active": True,
        "flash_sale.end_time": {"$gt": now.isoformat()},
        "status": "active"
    }, {"_id": 0}).to_list(100)
    
    return flash_sales

@router.post("/admin/flash-sale")
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

@router.delete("/admin/flash-sale/{competition_id}")
async def end_flash_sale(competition_id: str, admin: dict = Depends(get_admin_user)):
    """End a flash sale early"""
    await db.competitions.update_one(
        {"competition_id": competition_id},
        {"$unset": {"flash_sale": ""}}
    )
    return {"success": True}


# --- Special Competition Admin Routes (moved from bots) ---
@router.post("/admin/create-special-competition/{config_id}")
async def admin_create_special_competition(config_id: str, admin: dict = Depends(get_admin_user)):
    """Create a special competition (Tesla, etc.)"""
    result = await create_special_competition(config_id)
    if result:
        return {"success": True, "competition": result}
    else:
        raise HTTPException(status_code=400, detail="Competitia exista deja sau config invalid")


@router.get("/admin/special-competition-configs")
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


