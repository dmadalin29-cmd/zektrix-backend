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

from helpers import generate_random_ticket_number, notify_user_push

router = APIRouter(prefix="/api")

# ==================== VIVA WEBHOOK ====================

@router.get("/webhooks/viva")
async def viva_webhook_verification():
    """Handle Viva Webhook URL verification - must return Key in JSON format"""
    return {"Key": "475FFE73819D67134BBB2D6690A9023714C14E2E"}

@router.post("/webhooks/viva")
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

@router.post("/admin/process-pending-payment/{order_code}")
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

@router.get("/admin/pending-payments")
async def admin_get_pending_payments(admin: dict = Depends(get_admin_user)):
    """Get all pending payments that haven't been processed"""
    pending = await db.pending_purchases.find(
        {"status": {"$ne": "completed"}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return pending

@router.post("/admin/sync-sold-tickets")
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

@router.get("/payments/verify")
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

@router.post("/admin/send-daily-digest")
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

@router.post("/admin/notify-75-percent/{competition_id}")
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

