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

router = APIRouter(prefix="/api")

# ==================== SUBSCRIPTIONS ====================

SUBSCRIPTION_PLANS = [
    {"plan_id": "sub_25", "name": "Abonament 25", "price": 25.0, "entries_per_competition": 2, "duration_days": 30},
    {"plan_id": "sub_50", "name": "Abonament 50", "price": 50.0, "entries_per_competition": 5, "duration_days": 30},
    {"plan_id": "sub_100", "name": "Abonament 100", "price": 100.0, "entries_per_competition": 12, "duration_days": 30},
]

MAX_ENTRY_PRICE_FOR_SUBSCRIPTION = 3.99

class SubscriptionPurchase(BaseModel):
    plan_id: str
    payment_method: str = "wallet"  # "wallet" or "viva"

@router.get("/subscriptions/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return SUBSCRIPTION_PLANS

@router.get("/subscriptions/my")
async def get_my_subscription(current_user: dict = Depends(get_current_user)):
    """Get user's active subscription"""
    sub = await db.subscriptions.find_one(
        {"user_id": current_user["user_id"], "status": "active"},
        {"_id": 0}
    )
    if sub and sub.get("expires_at"):
        if datetime.fromisoformat(sub["expires_at"]) < datetime.now(timezone.utc):
            await db.subscriptions.update_one(
                {"subscription_id": sub["subscription_id"]},
                {"$set": {"status": "expired"}}
            )
            sub["status"] = "expired"
    return {"subscription": sub}

@router.get("/subscriptions/my/tickets")
async def get_subscription_tickets(current_user: dict = Depends(get_current_user)):
    """Get tickets received via subscription"""
    tickets = await db.tickets.find(
        {"user_id": current_user["user_id"], "source": "subscription"},
        {"_id": 0}
    ).sort("purchased_at", -1).to_list(200)
    return tickets

@router.post("/subscriptions/purchase")
async def purchase_subscription(purchase: SubscriptionPurchase, current_user: dict = Depends(get_current_user)):
    """Purchase a subscription"""
    plan = next((p for p in SUBSCRIPTION_PLANS if p["plan_id"] == purchase.plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check if user already has active subscription
    existing = await db.subscriptions.find_one(
        {"user_id": current_user["user_id"], "status": "active"},
        {"_id": 0}
    )
    if existing:
        if datetime.fromisoformat(existing["expires_at"]) > datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Already have an active subscription")
    
    subscription_id = f"sub_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=plan["duration_days"])
    
    if purchase.payment_method == "wallet":
        balance = current_user.get("balance", 0)
        if balance < plan["price"]:
            raise HTTPException(status_code=400, detail=f"Insufficient wallet balance. Need £{plan['price']:.2f}, have £{balance:.2f}")
        
        # Deduct from wallet
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$inc": {"balance": -plan["price"]}}
        )
        
        # Create subscription
        sub_doc = {
            "subscription_id": subscription_id,
            "user_id": current_user["user_id"],
            "username": current_user.get("username", ""),
            "email": current_user.get("email", ""),
            "plan_id": plan["plan_id"],
            "plan_name": plan["name"],
            "price": plan["price"],
            "entries_per_competition": plan["entries_per_competition"],
            "status": "active",
            "auto_renew": True,
            "payment_method": "wallet",
            "started_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "created_at": now.isoformat(),
            "tickets_distributed": 0
        }
        await db.subscriptions.insert_one(sub_doc)
        
        # Record transaction
        await db.transactions.insert_one({
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "user_id": current_user["user_id"],
            "transaction_type": "subscription",
            "amount": -plan["price"],
            "status": "completed",
            "description": f"{plan['name']} - {plan['entries_per_competition']} bilete/competitie, 30 zile",
            "subscription_id": subscription_id,
            "created_at": now.isoformat()
        })
        
        # Distribute tickets to all eligible active competitions
        asyncio.create_task(distribute_subscription_tickets(
            current_user["user_id"], subscription_id, plan["entries_per_competition"]
        ))
        
        return {"subscription_id": subscription_id, "status": "active", "expires_at": expires_at.isoformat(), "payment": "wallet"}
    
    else:  # Viva payment
        access_token = await get_viva_access_token()
        if not access_token:
            raise HTTPException(status_code=500, detail="Payment service unavailable")
        
        transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
        amount_cents = int(plan["price"] * 100)
        
        async with httpx.AsyncClient() as http_client:
            order_data = {
                "amount": amount_cents,
                "customerTrns": f"Subscription {plan['name']} - £{plan['price']:.2f}",
                "merchantTrns": transaction_id,
                "sourceCode": VIVA_SOURCE_CODE,
                "paymentTimeout": 1800,
                "currencyCode": "826",
                "successUrl": "https://zektrix.uk/subscriptions?payment=success",
                "failureUrl": "https://zektrix.uk/subscriptions?payment=failed",
                "cancelUrl": "https://zektrix.uk/subscriptions?payment=cancel"
            }
            
            resp = await http_client.post(
                f"{VIVA_API_URL}/checkout/v2/orders",
                json=order_data,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0
            )
            
            if resp.status_code != 200:
                logger.error(f"Viva subscription order error: {resp.text}")
                raise HTTPException(status_code=500, detail="Failed to create payment order")
            
            order_code = str(resp.json().get("orderCode", ""))
        
        # Store pending subscription
        pending_sub = {
            "subscription_id": subscription_id,
            "user_id": current_user["user_id"],
            "username": current_user.get("username", ""),
            "email": current_user.get("email", ""),
            "plan_id": plan["plan_id"],
            "plan_name": plan["name"],
            "price": plan["price"],
            "entries_per_competition": plan["entries_per_competition"],
            "status": "pending_payment",
            "auto_renew": True,
            "payment_method": "viva",
            "viva_order_code": order_code,
            "started_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "created_at": now.isoformat(),
            "tickets_distributed": 0
        }
        await db.subscriptions.insert_one(pending_sub)
        
        await db.transactions.insert_one({
            "transaction_id": transaction_id,
            "user_id": current_user["user_id"],
            "transaction_type": "subscription",
            "amount": -plan["price"],
            "status": "pending",
            "description": f"{plan['name']} - {plan['entries_per_competition']} bilete/competitie",
            "subscription_id": subscription_id,
            "viva_order_code": order_code,
            "created_at": now.isoformat()
        })
        
        checkout_url = f"{VIVA_CHECKOUT_URL}?ref={order_code}"
        return {"checkout_url": checkout_url, "order_code": order_code, "subscription_id": subscription_id}

@router.post("/subscriptions/cancel")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    """Cancel auto-renewal of subscription"""
    sub = await db.subscriptions.find_one(
        {"user_id": current_user["user_id"], "status": "active"},
        {"_id": 0}
    )
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    await db.subscriptions.update_one(
        {"subscription_id": sub["subscription_id"]},
        {"$set": {"auto_renew": False}}
    )
    return {"message": "Auto-renewal cancelled. Subscription remains active until expiry.", "expires_at": sub["expires_at"]}

async def distribute_subscription_tickets(user_id: str, subscription_id: str, entries_per_comp: int):
    """Distribute subscription tickets to all eligible active competitions"""
    try:
        comps = await db.competitions.find(
            {"status": "active", "ticket_price": {"$lte": MAX_ENTRY_PRICE_FOR_SUBSCRIPTION}},
            {"_id": 0}
        ).to_list(100)
        
        total_distributed = 0
        for comp in comps:
            if comp.get("is_free"):
                continue
            
            available = comp["max_tickets"] - comp["sold_tickets"]
            qty = min(entries_per_comp, available)
            if qty <= 0:
                continue
            
            # Check if already distributed for this sub + comp
            existing = await db.tickets.count_documents({
                "user_id": user_id,
                "competition_id": comp["competition_id"],
                "source": "subscription",
                "subscription_id": subscription_id
            })
            if existing >= entries_per_comp:
                continue
            
            qty = min(qty, entries_per_comp - existing)
            if qty <= 0:
                continue
            
            # Get available ticket numbers
            sold = await db.tickets.find(
                {"competition_id": comp["competition_id"]},
                {"ticket_number": 1, "_id": 0}
            ).to_list(100000)
            sold_nums = {t["ticket_number"] for t in sold}
            avail_nums = list(set(range(1, comp["max_tickets"] + 1)) - sold_nums)
            
            if len(avail_nums) < qty:
                qty = len(avail_nums)
            if qty <= 0:
                continue
            
            selected = random.sample(avail_nums, qty)
            for num in selected:
                await db.tickets.insert_one({
                    "ticket_id": f"ticket_{uuid.uuid4().hex[:12]}",
                    "user_id": user_id,
                    "competition_id": comp["competition_id"],
                    "ticket_number": num,
                    "purchased_at": datetime.now(timezone.utc).isoformat(),
                    "competition_title": comp["title"],
                    "source": "subscription",
                    "subscription_id": subscription_id
                })
            
            # Update sold count
            await db.competitions.update_one(
                {"competition_id": comp["competition_id"]},
                {"$inc": {"sold_tickets": qty}}
            )
            total_distributed += qty
            
            # Check instant prizes
            new_sold = comp["sold_tickets"] + qty
            await check_instant_prizes(comp["competition_id"], new_sold, comp["max_tickets"])
        
        # Update subscription ticket count
        await db.subscriptions.update_one(
            {"subscription_id": subscription_id},
            {"$inc": {"tickets_distributed": total_distributed}}
        )
        
        if total_distributed > 0:
            await notify_user_push(
                user_id,
                "Bilete Abonament Distribuite!",
                f"Ai primit {total_distributed} bilete la competitiile active!",
                "https://zektrix.uk/subscriptions"
            )
        
        logger.info(f"[SUBSCRIPTION] Distributed {total_distributed} tickets for user {user_id}, sub {subscription_id}")
    except Exception as e:
        logger.error(f"[SUBSCRIPTION] Error distributing tickets: {e}")

async def distribute_to_subscribers_for_competition(competition_id: str):
    """When a new competition is created, distribute tickets to all active subscribers"""
    try:
        comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
        if not comp or comp["status"] != "active":
            return
        if comp.get("ticket_price", 0) > MAX_ENTRY_PRICE_FOR_SUBSCRIPTION:
            return
        if comp.get("is_free"):
            return
        
        now = datetime.now(timezone.utc)
        active_subs = await db.subscriptions.find(
            {"status": "active"},
            {"_id": 0}
        ).to_list(1000)
        
        total = 0
        for sub in active_subs:
            if datetime.fromisoformat(sub["expires_at"]) < now:
                await db.subscriptions.update_one(
                    {"subscription_id": sub["subscription_id"]},
                    {"$set": {"status": "expired"}}
                )
                continue
            
            qty = sub["entries_per_competition"]
            available = comp["max_tickets"] - comp["sold_tickets"] - total
            qty = min(qty, available)
            if qty <= 0:
                continue
            
            sold = await db.tickets.find(
                {"competition_id": competition_id},
                {"ticket_number": 1, "_id": 0}
            ).to_list(100000)
            sold_nums = {t["ticket_number"] for t in sold}
            avail_nums = list(set(range(1, comp["max_tickets"] + 1)) - sold_nums)
            
            if len(avail_nums) < qty:
                qty = len(avail_nums)
            if qty <= 0:
                continue
            
            selected = random.sample(avail_nums, qty)
            for num in selected:
                await db.tickets.insert_one({
                    "ticket_id": f"ticket_{uuid.uuid4().hex[:12]}",
                    "user_id": sub["user_id"],
                    "competition_id": competition_id,
                    "ticket_number": num,
                    "purchased_at": now.isoformat(),
                    "competition_title": comp["title"],
                    "source": "subscription",
                    "subscription_id": sub["subscription_id"]
                })
            
            await db.competitions.update_one(
                {"competition_id": competition_id},
                {"$inc": {"sold_tickets": qty}}
            )
            
            await db.subscriptions.update_one(
                {"subscription_id": sub["subscription_id"]},
                {"$inc": {"tickets_distributed": qty}}
            )
            
            total += qty
            
            await notify_user_push(
                sub["user_id"],
                f"Bilete noi: {comp['title']}",
                f"Ai primit {qty} bilete gratis din abonament!",
                f"https://zektrix.uk/competitions/{competition_id}"
            )
        
        logger.info(f"[SUBSCRIPTION] Distributed {total} tickets to {len(active_subs)} subscribers for {comp['title']}")
    except Exception as e:
        logger.error(f"[SUBSCRIPTION] Error distributing to subscribers: {e}")

# Admin subscription endpoints
@router.get("/admin/subscriptions")
async def get_all_subscriptions(admin: dict = Depends(get_admin_user)):
    """Get all subscriptions"""
    subs = await db.subscriptions.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return subs

@router.get("/admin/subscriptions/stats")
async def get_subscription_stats(admin: dict = Depends(get_admin_user)):
    """Get subscription statistics"""
    now = datetime.now(timezone.utc).isoformat()
    active = await db.subscriptions.count_documents({"status": "active", "expires_at": {"$gt": now}})
    total = await db.subscriptions.count_documents({})
    revenue = await db.subscriptions.aggregate([
        {"$match": {"status": {"$in": ["active", "expired"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$price"}}}
    ]).to_list(1)
    tickets = await db.subscriptions.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$tickets_distributed"}}}
    ]).to_list(1)
    
    return {
        "active_subscriptions": active,
        "total_subscriptions": total,
        "total_revenue": revenue[0]["total"] if revenue else 0,
        "total_tickets_distributed": tickets[0]["total"] if tickets else 0
    }

