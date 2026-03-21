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

# ==================== REFERRAL SYSTEM ====================

@router.get("/referral/my")
async def get_my_referral(current_user: dict = Depends(get_current_user)):
    """Get my referral stats and code"""
    code = current_user.get("referral_code", "")
    
    referrals = await db.referrals.find(
        {"referrer_id": current_user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    
    total_invited = len(referrals)
    completed = [r for r in referrals if r["status"] == "completed"]
    pending = [r for r in referrals if r["status"] == "pending"]
    
    earnings_agg = await db.transactions.aggregate([
        {"$match": {"user_id": current_user["user_id"], "transaction_type": "referral_bonus"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    total_earnings = earnings_agg[0]["total"] if earnings_agg else 0
    
    invited_list = []
    for ref in referrals:
        referred_user = await db.users.find_one(
            {"user_id": ref["referred_id"]},
            {"_id": 0, "username": 1, "created_at": 1}
        )
        invited_list.append({
            "username": referred_user.get("username", "?") if referred_user else "?",
            "status": ref["status"],
            "created_at": ref["created_at"],
            "completed_at": ref.get("completed_at"),
        })
    
    return {
        "referral_code": code,
        "referral_link": f"https://zektrix.uk?ref={code}",
        "total_invited": total_invited,
        "total_completed": len(completed),
        "total_pending": len(pending),
        "total_earnings": total_earnings,
        "invited_list": invited_list
    }

class CustomCodeRequest(BaseModel):
    code: str

@router.post("/referral/customize")
async def customize_referral_code(req: CustomCodeRequest, current_user: dict = Depends(get_current_user)):
    """Customize referral code"""
    code = req.code.strip().upper().replace(" ", "")
    if len(code) < 3 or len(code) > 15:
        raise HTTPException(status_code=400, detail="Codul trebuie sa aiba intre 3 si 15 caractere")
    if not code.isalnum():
        raise HTTPException(status_code=400, detail="Codul poate contine doar litere si cifre")
    existing = await db.users.find_one({"referral_code": code, "user_id": {"$ne": current_user["user_id"]}})
    if existing:
        raise HTTPException(status_code=400, detail="Acest cod este deja folosit de altcineva")
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"referral_code": code}}
    )
    return {"referral_code": code, "referral_link": f"https://zektrix.uk?ref={code}"}

@router.get("/referral/leaderboard")
async def get_referral_leaderboard():
    """Get top referrers leaderboard"""
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": "$referrer_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    top = await db.referrals.aggregate(pipeline).to_list(20)
    leaderboard = []
    for i, entry in enumerate(top):
        user = await db.users.find_one({"user_id": entry["_id"]}, {"_id": 0, "username": 1, "referral_code": 1})
        if user:
            leaderboard.append({
                "rank": i + 1,
                "username": user.get("username", "?"),
                "referral_code": user.get("referral_code", ""),
                "referrals": entry["count"]
            })
    return leaderboard

@router.get("/admin/referral/stats")
async def get_admin_referral_stats(admin: dict = Depends(get_admin_user)):
    """Admin referral statistics"""
    total = await db.referrals.count_documents({})
    completed = await db.referrals.count_documents({"status": "completed"})
    pending = await db.referrals.count_documents({"status": "pending"})
    total_paid = await db.transactions.aggregate([
        {"$match": {"transaction_type": "referral_bonus"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    top_referrers = await db.referrals.aggregate([
        {"$match": {"status": "completed"}},
        {"$group": {"_id": "$referrer_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]).to_list(5)
    top_list = []
    for entry in top_referrers:
        user = await db.users.find_one({"user_id": entry["_id"]}, {"_id": 0, "username": 1, "email": 1})
        if user:
            top_list.append({"username": user.get("username", user.get("email", "?")), "referrals": entry["count"]})
    return {
        "total_referrals": total, "completed": completed, "pending": pending,
        "total_paid": total_paid[0]["total"] if total_paid else 0,
        "conversion_rate": round((completed / total * 100), 1) if total > 0 else 0,
        "top_referrers": top_list
    }


# ==================== REFERRAL SYSTEM ====================

def generate_referral_code(user_id: str) -> str:
    """Generate unique referral code"""
    return f"ZEK{user_id[-6:].upper()}"

@router.get("/referral/my-code")
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

@router.get("/referral/my-referrals")
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

@router.post("/referral/apply")
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

@router.get("/referral/validate/{code}")
async def validate_referral_code(code: str):
    """Validate a referral code (public endpoint for registration)"""
    referrer = await db.users.find_one({"referral_code": code.upper()}, {"_id": 0, "username": 1})
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    return {"valid": True, "referrer_username": referrer.get("username", "Unknown")}

