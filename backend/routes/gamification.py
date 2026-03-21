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


router = APIRouter(prefix="/api")

# ==================== GAMIFICATION BADGES ====================
BADGE_DEFINITIONS = [
    {"id": "first_ticket", "name": "Primul Bilet", "description": "Ai cumparat primul bilet!", "icon": "ticket", "condition": "tickets >= 1"},
    {"id": "five_tickets", "name": "Colectionar", "description": "5 bilete cumparate!", "icon": "collection", "condition": "tickets >= 5"},
    {"id": "twenty_tickets", "name": "Pasionat", "description": "20 de bilete! Esti un veteran!", "icon": "fire", "condition": "tickets >= 20"},
    {"id": "fifty_tickets", "name": "Legenda", "description": "50 de bilete! Nimic nu te opreste!", "icon": "crown", "condition": "tickets >= 50"},
    {"id": "first_win", "name": "Castigator", "description": "Ai castigat prima competitie!", "icon": "trophy", "condition": "wins >= 1"},
    {"id": "referral_starter", "name": "Ambasador", "description": "Ai invitat primul prieten!", "icon": "users", "condition": "referrals >= 1"},
    {"id": "referral_king", "name": "Referral King", "description": "5 prieteni invitati cu succes!", "icon": "crown_gold", "condition": "referrals >= 5"},
    {"id": "big_spender", "name": "High Roller", "description": "Ai cheltuit peste £100!", "icon": "diamond", "condition": "spent >= 100"},
    {"id": "multi_comp", "name": "Explorer", "description": "Participi la 3+ competitii diferite!", "icon": "compass", "condition": "unique_comps >= 3"},
    {"id": "early_bird", "name": "Early Bird", "description": "Ai fost printre primii 10% cumparatori!", "icon": "star", "condition": "early_buyer"},
]

async def check_and_award_badges(user_id: str):
    """Check all badge conditions and award new ones"""
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        return []
    
    existing_badges = user.get("badges", [])
    existing_ids = {b["id"] for b in existing_badges}
    new_badges = []
    
    # Get user stats
    ticket_count = await db.tickets.count_documents({"user_id": user_id})
    win_count = await db.winners.count_documents({"user_id": user_id})
    referral_count = await db.referrals.count_documents({"referrer_id": user_id, "status": "completed"})
    
    # Calculate total spent
    pipeline = [{"$match": {"user_id": user_id, "transaction_type": {"$in": ["ticket_purchase", "cart_purchase"]}, "status": "completed"}}, {"$group": {"_id": None, "total": {"$sum": {"$abs": "$amount"}}}}]
    spent_result = await db.transactions.aggregate(pipeline).to_list(1)
    total_spent = spent_result[0]["total"] if spent_result else 0
    
    # Count unique competitions
    unique_comps = len(await db.tickets.distinct("competition_id", {"user_id": user_id}))
    
    now = datetime.now(timezone.utc).isoformat()
    
    for badge_def in BADGE_DEFINITIONS:
        if badge_def["id"] in existing_ids:
            continue
        
        awarded = False
        cond = badge_def["condition"]
        
        if cond == "tickets >= 1" and ticket_count >= 1: awarded = True
        elif cond == "tickets >= 5" and ticket_count >= 5: awarded = True
        elif cond == "tickets >= 20" and ticket_count >= 20: awarded = True
        elif cond == "tickets >= 50" and ticket_count >= 50: awarded = True
        elif cond == "wins >= 1" and win_count >= 1: awarded = True
        elif cond == "referrals >= 1" and referral_count >= 1: awarded = True
        elif cond == "referrals >= 5" and referral_count >= 5: awarded = True
        elif cond == "spent >= 100" and total_spent >= 100: awarded = True
        elif cond == "unique_comps >= 3" and unique_comps >= 3: awarded = True
        
        if awarded:
            new_badge = {"id": badge_def["id"], "name": badge_def["name"], "description": badge_def["description"], "icon": badge_def["icon"], "awarded_at": now}
            new_badges.append(new_badge)
    
    if new_badges:
        await db.users.update_one(
            {"user_id": user_id},
            {"$push": {"badges": {"$each": new_badges}}}
        )
    
    return new_badges

@router.get("/user/badges")
async def get_user_badges(user: dict = Depends(get_current_user)):
    """Get current user's badges and available badge definitions"""
    user_badges = user.get("badges", [])
    earned_ids = {b["id"] for b in user_badges}
    
    all_badges = []
    for bd in BADGE_DEFINITIONS:
        badge_info = {
            "id": bd["id"],
            "name": bd["name"],
            "description": bd["description"],
            "icon": bd["icon"],
            "earned": bd["id"] in earned_ids,
            "awarded_at": next((b["awarded_at"] for b in user_badges if b["id"] == bd["id"]), None)
        }
        all_badges.append(badge_info)
    
    return {"badges": all_badges, "total_earned": len(earned_ids), "total_available": len(BADGE_DEFINITIONS)}

