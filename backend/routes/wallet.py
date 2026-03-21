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

from helpers import notify_user_push, notify_admins_push

router = APIRouter(prefix="/api")

@router.get("/wallet/balance")
async def get_wallet_balance(current_user: dict = Depends(get_current_user)):
    return {"balance": current_user["balance"]}

@router.get("/wallet/transactions")
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

@router.post("/wallet/deposit")
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

@router.post("/wallet/withdraw")
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

@router.get("/wallet/withdrawals")
async def get_my_withdrawals(current_user: dict = Depends(get_current_user)):
    """Get user's withdrawal requests"""
    withdrawals = await db.withdrawal_requests.find(
        {"user_id": current_user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return withdrawals

@router.get("/wallet/bonus-info")
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

@router.get("/admin/wallet/withdrawals")
async def get_all_withdrawals(status: Optional[str] = None, admin: dict = Depends(get_admin_user)):
    """Get all withdrawal requests (admin)"""
    query = {}
    if status:
        query["status"] = status
    withdrawals = await db.withdrawal_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return withdrawals

@router.post("/admin/wallet/withdrawal/{withdrawal_id}/approve")
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

@router.post("/admin/wallet/withdrawal/{withdrawal_id}/reject")
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

@router.post("/admin/wallet/adjust")
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

@router.get("/admin/wallet/bonus-settings")
async def get_bonus_settings(admin: dict = Depends(get_admin_user)):
    """Get deposit bonus configuration"""
    settings = await db.site_settings.find_one({"setting_id": "deposit_bonus"}, {"_id": 0})
    if not settings:
        return {"active": False, "bonus_percent": 10, "bonus_max": 20}
    return {"active": settings.get("active", False), "bonus_percent": settings.get("bonus_percent", 10), "bonus_max": settings.get("bonus_max", 20)}

@router.put("/admin/wallet/bonus-settings")
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

@router.get("/admin/wallet/stats")
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

@router.post("/wallet/webhook")
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
            
            # Handle subscription payment via Viva
            if transaction["transaction_type"] == "subscription":
                sub_id = transaction.get("subscription_id")
                if sub_id:
                    sub = await db.subscriptions.find_one({"subscription_id": sub_id})
                    if sub and sub["status"] == "pending_payment":
                        await db.subscriptions.update_one(
                            {"subscription_id": sub_id},
                            {"$set": {"status": "active"}}
                        )
                        asyncio.create_task(distribute_subscription_tickets(
                            sub["user_id"], sub_id, sub["entries_per_competition"]
                        ))
                    
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

@router.get("/wallet/payment-status/{order_code}")
async def check_payment_status(order_code: str, current_user: dict = Depends(get_current_user)):
    transaction = await db.transactions.find_one(
        {"viva_order_code": order_code, "user_id": current_user["user_id"]},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

