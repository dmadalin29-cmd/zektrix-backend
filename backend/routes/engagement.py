# -*- coding: utf-8 -*-
"""Engagement features: Loyalty Points, In-App Notifications, Reviews, Wheel of Fortune, Exit Intent"""
from fastapi import APIRouter, HTTPException, Depends, Response
from database import db
from dependencies import get_current_user, get_admin_user
from config import *
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid, random, logging

try:
    from models import *
except ImportError:
    from backend.models import *

logger = logging.getLogger("server")
router = APIRouter(prefix="/api")


# ==================== LOYALTY POINTS ====================

POINTS_PER_POUND = 10  # 10 points per £1 spent
POINTS_REDEEM_RATE = 100  # 100 points = £1 credit

@router.get("/loyalty/my")
async def get_loyalty_info(user: dict = Depends(get_current_user)):
    """Get user's loyalty points info"""
    points = user.get("loyalty_points", 0)
    total_earned = user.get("loyalty_total_earned", 0)
    redeemable_value = (points // POINTS_REDEEM_RATE) * 1
    return {
        "points": points,
        "total_earned": total_earned,
        "redeemable_value": redeemable_value,
        "points_per_pound": POINTS_PER_POUND,
        "redeem_rate": POINTS_REDEEM_RATE,
        "tier": get_loyalty_tier(total_earned)
    }

def get_loyalty_tier(total_earned):
    if total_earned >= 5000: return {"name": "Diamond", "icon": "diamond", "color": "#b9f2ff", "min_points": 5000, "bonus_multiplier": 2.0}
    if total_earned >= 2000: return {"name": "Gold", "icon": "crown", "color": "#fbbf24", "min_points": 2000, "bonus_multiplier": 1.5}
    if total_earned >= 500: return {"name": "Silver", "icon": "medal", "color": "#c0c0c0", "min_points": 500, "bonus_multiplier": 1.2}
    return {"name": "Bronze", "icon": "star", "color": "#cd7f32", "min_points": 0, "bonus_multiplier": 1.0}

class RedeemRequest(BaseModel):
    points: int = Field(ge=100)

@router.post("/loyalty/redeem")
async def redeem_loyalty_points(req: RedeemRequest, user: dict = Depends(get_current_user)):
    """Redeem loyalty points for wallet credit"""
    current_points = user.get("loyalty_points", 0)
    if req.points > current_points:
        raise HTTPException(400, "Puncte insuficiente")
    if req.points % POINTS_REDEEM_RATE != 0:
        raise HTTPException(400, f"Punctele trebuie sa fie multiplu de {POINTS_REDEEM_RATE}")
    
    credit = req.points // POINTS_REDEEM_RATE
    
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"loyalty_points": -req.points, "balance": credit}}
    )
    
    await db.transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "amount": credit,
        "transaction_type": "loyalty_redeem",
        "status": "completed",
        "description": f"Rascumparare {req.points} puncte fidelitate",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "credited": credit, "remaining_points": current_points - req.points}


async def award_loyalty_points(user_id: str, amount_spent: float):
    """Award loyalty points after a purchase. Called from ticket purchase flow."""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "loyalty_total_earned": 1})
    tier = get_loyalty_tier(user.get("loyalty_total_earned", 0) if user else 0)
    points = int(amount_spent * POINTS_PER_POUND * tier["bonus_multiplier"])
    if points > 0:
        await db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"loyalty_points": points, "loyalty_total_earned": points}}
        )
        # Create notification
        await create_user_notification(user_id, "loyalty", f"+{points} puncte fidelitate!", f"Ai castigat {points} puncte pentru achizitia ta.")
    return points


# ==================== IN-APP NOTIFICATIONS ====================

async def create_user_notification(user_id: str, notif_type: str, title: str, message: str, url: str = None):
    """Create an in-app notification for a user"""
    await db.user_notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": notif_type,
        "title": title,
        "message": message,
        "url": url,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

@router.get("/notifications/my")
async def get_user_notifications(user: dict = Depends(get_current_user)):
    """Get user's in-app notifications"""
    notifs = await db.user_notifications.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    unread = sum(1 for n in notifs if not n.get("read"))
    return {"notifications": notifs, "unread_count": unread}

@router.post("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(get_current_user)):
    """Mark all user notifications as read"""
    await db.user_notifications.update_many(
        {"user_id": user["user_id"], "read": False},
        {"$set": {"read": True}}
    )
    return {"success": True}

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    """Mark a single notification as read"""
    await db.user_notifications.update_one(
        {"notification_id": notification_id, "user_id": user["user_id"]},
        {"$set": {"read": True}}
    )
    return {"success": True}


# ==================== REVIEWS / TESTIMONIALS ====================

class ReviewCreate(BaseModel):
    competition_id: str
    rating: int = Field(ge=1, le=5)
    text: str = Field(max_length=500)

@router.post("/reviews")
async def create_review(review: ReviewCreate, user: dict = Depends(get_current_user)):
    """Create a review (only winners can review)"""
    # Verify user won this competition
    winner = await db.winners.find_one({"user_id": user["user_id"], "competition_id": review.competition_id})
    if not winner:
        raise HTTPException(403, "Doar castigatorii pot lasa recenzii")
    
    # Check if already reviewed
    existing = await db.reviews.find_one({"user_id": user["user_id"], "competition_id": review.competition_id})
    if existing:
        raise HTTPException(400, "Ai lasat deja o recenzie pentru aceasta competitie")
    
    comp = await db.competitions.find_one({"competition_id": review.competition_id}, {"_id": 0, "title": 1, "prize_description": 1})
    
    review_doc = {
        "review_id": f"rev_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "username": user.get("username", "Anonim"),
        "picture": user.get("picture"),
        "competition_id": review.competition_id,
        "competition_title": comp.get("title", "") if comp else "",
        "prize_description": comp.get("prize_description", "") if comp else "",
        "rating": review.rating,
        "text": review.text,
        "approved": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reviews.insert_one(review_doc)
    del review_doc["_id"]
    return review_doc

@router.get("/reviews")
async def get_reviews(response: Response, limit: int = 10):
    """Get approved reviews for public display"""
    response.headers["Cache-Control"] = "public, max-age=60"
    reviews = await db.reviews.find(
        {"approved": True},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return reviews

@router.get("/reviews/pending")
async def get_pending_reviews(admin: dict = Depends(get_admin_user)):
    """Get pending reviews for admin approval"""
    reviews = await db.reviews.find({"approved": False}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return reviews

@router.post("/reviews/{review_id}/approve")
async def approve_review(review_id: str, admin: dict = Depends(get_admin_user)):
    """Approve a review"""
    result = await db.reviews.update_one({"review_id": review_id}, {"$set": {"approved": True}})
    if result.modified_count == 0:
        raise HTTPException(404, "Review not found")
    return {"success": True}

@router.delete("/reviews/{review_id}")
async def delete_review(review_id: str, admin: dict = Depends(get_admin_user)):
    """Delete a review"""
    await db.reviews.delete_one({"review_id": review_id})
    return {"success": True}


# ==================== WHEEL OF FORTUNE ====================

WHEEL_PRIZES = [
    {"id": "10off", "label": "10% Reducere", "type": "discount", "value": 10, "probability": 0.25, "color": "#8b5cf6"},
    {"id": "15off", "label": "15% Reducere", "type": "discount", "value": 15, "probability": 0.15, "color": "#f59e0b"},
    {"id": "25off", "label": "25% Reducere", "type": "discount", "value": 25, "probability": 0.05, "color": "#ef4444"},
    {"id": "1credit", "label": "£1 Credit", "type": "credit", "value": 1, "probability": 0.20, "color": "#10b981"},
    {"id": "2credit", "label": "£2 Credit", "type": "credit", "value": 2, "probability": 0.10, "color": "#06b6d4"},
    {"id": "50points", "label": "50 Puncte", "type": "points", "value": 50, "probability": 0.15, "color": "#f97316"},
    {"id": "noroc", "label": "Mai incearca!", "type": "nothing", "value": 0, "probability": 0.05, "color": "#6b7280"},
    {"id": "5credit", "label": "£5 Credit", "type": "credit", "value": 5, "probability": 0.05, "color": "#ec4899"},
]

@router.get("/wheel/prizes")
async def get_wheel_prizes():
    """Get wheel prize definitions (without probabilities)"""
    return [{"id": p["id"], "label": p["label"], "color": p["color"]} for p in WHEEL_PRIZES]

@router.post("/wheel/spin")
async def spin_wheel(user: dict = Depends(get_current_user)):
    """Spin the wheel of fortune (once per user)"""
    # Check if user already spun
    existing = await db.wheel_spins.find_one({"user_id": user["user_id"]})
    if existing:
        raise HTTPException(400, "Ai folosit deja roata norocului!")
    
    # Weighted random pick
    rand = random.random()
    cumulative = 0
    won_prize = WHEEL_PRIZES[-1]  # default: "noroc"
    for prize in WHEEL_PRIZES:
        cumulative += prize["probability"]
        if rand <= cumulative:
            won_prize = prize
            break
    
    # Apply prize
    if won_prize["type"] == "credit":
        await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"balance": won_prize["value"]}})
        await db.transactions.insert_one({
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "user_id": user["user_id"],
            "amount": won_prize["value"],
            "transaction_type": "wheel_bonus",
            "status": "completed",
            "description": f"Roata Norocului: {won_prize['label']}",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        await create_user_notification(user["user_id"], "wheel", "Ai castigat!", f"Felicitari! Ai castigat {won_prize['label']} la Roata Norocului!")
    
    elif won_prize["type"] == "points":
        await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"loyalty_points": won_prize["value"], "loyalty_total_earned": won_prize["value"]}})
        await create_user_notification(user["user_id"], "wheel", "Ai castigat!", f"Felicitari! +{won_prize['value']} puncte fidelitate!")
    
    elif won_prize["type"] == "discount":
        expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        await db.user_discounts.insert_one({
            "discount_id": f"disc_{uuid.uuid4().hex[:8]}",
            "user_id": user["user_id"],
            "percent": won_prize["value"],
            "expires_at": expires,
            "used": False,
            "source": "wheel",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        await create_user_notification(user["user_id"], "wheel", "Ai castigat!", f"Felicitari! {won_prize['label']} valabil 7 zile!")
    
    # Record spin
    await db.wheel_spins.insert_one({
        "user_id": user["user_id"],
        "prize_id": won_prize["id"],
        "prize_label": won_prize["label"],
        "prize_type": won_prize["type"],
        "prize_value": won_prize["value"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "prize_id": won_prize["id"],
        "prize_label": won_prize["label"],
        "prize_type": won_prize["type"],
        "prize_value": won_prize["value"],
        "prize_color": won_prize["color"]
    }

@router.get("/wheel/status")
async def get_wheel_status(user: dict = Depends(get_current_user)):
    """Check if user can spin"""
    existing = await db.wheel_spins.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"can_spin": existing is None, "previous_spin": existing}


# ==================== EXIT INTENT DISCOUNT ====================

@router.post("/exit-intent/claim")
async def claim_exit_discount(user: dict = Depends(get_current_user)):
    """Claim exit intent discount (15% off, once per user)"""
    existing = await db.user_discounts.find_one({"user_id": user["user_id"], "source": "exit_intent"})
    if existing:
        raise HTTPException(400, "Ai folosit deja aceasta oferta!")
    
    expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    discount_doc = {
        "discount_id": f"disc_{uuid.uuid4().hex[:8]}",
        "user_id": user["user_id"],
        "percent": 15,
        "expires_at": expires,
        "used": False,
        "source": "exit_intent",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_discounts.insert_one(discount_doc)
    
    await create_user_notification(user["user_id"], "discount", "15% Reducere!", "Ai primit 15% reducere valabil 24h!")
    
    return {"success": True, "discount_percent": 15, "expires_at": expires}

@router.get("/discounts/my")
async def get_my_discounts(user: dict = Depends(get_current_user)):
    """Get user's active discounts"""
    now = datetime.now(timezone.utc).isoformat()
    discounts = await db.user_discounts.find(
        {"user_id": user["user_id"], "used": False, "expires_at": {"$gt": now}},
        {"_id": 0}
    ).to_list(20)
    return discounts
