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

from helpers import generate_random_ticket_number, notify_user_push, notify_competition_participants_push
try:
    from models import TicketResponse, TicketSearchResult
except ImportError:
    from backend.models import TicketResponse, TicketSearchResult

router = APIRouter(prefix="/api")

# ==================== COMPETITION ROUTES ====================

@router.get("/competitions")
async def get_competitions(response: Response, status: Optional[str] = None, competition_type: Optional[str] = None):
    response.headers["Cache-Control"] = "public, max-age=15"
    query = {}
    if status:
        query["status"] = status
    if competition_type:
        query["competition_type"] = competition_type
    
    competitions = await db.competitions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    for c in competitions:
        c.setdefault("is_free", False)
    return competitions

@router.get("/competitions/{competition_id}")
async def get_competition(competition_id: str, response: Response):
    response.headers["Cache-Control"] = "public, max-age=10"
    comp = await db.competitions.find_one({"competition_id": competition_id}, {"_id": 0})
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    comp.setdefault("is_free", False)
    return comp

@router.get("/competitions/{competition_id}/tickets", response_model=List[TicketResponse])
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

@router.post("/tickets/purchase", response_model=List[TicketResponse])
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
        # Give bonus to both users (£3 referrer, £2 referred)
        await db.users.update_one(
            {"user_id": pending_referral["referrer_id"]},
            {"$inc": {"balance": 3.0}}
        )
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$inc": {"balance": 2.0}}
        )
        # Record bonus transactions
        for uid, amount, desc in [
            (pending_referral["referrer_id"], 3.0, f"Referral bonus - {current_user.get('username', 'prieten')} a cumparat primul bilet"),
            (current_user["user_id"], 2.0, "Bonus bun venit - prima achizitie cu cod referral")
        ]:
            await db.transactions.insert_one({
                "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
                "user_id": uid,
                "transaction_type": "referral_bonus",
                "amount": amount,
                "status": "completed",
                "description": desc,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Notify referrer
        asyncio.create_task(notify_user_push(
            pending_referral["referrer_id"],
            "Ai primit £3 bonus referral!",
            f"Prietenul tau {current_user.get('username', '')} a cumparat primul bilet. £3 adaugati in wallet!",
            "https://zektrix.uk/dashboard/referral"
        ))
    
    # Broadcast ticket purchase via WebSocket
    await ws_manager.broadcast({
        "type": "ticket_purchased",
        "competition_id": purchase.competition_id,
        "sold_tickets": new_sold,
        "max_tickets": comp["max_tickets"]
    }, f"competition_{purchase.competition_id}")
    
    # Check and send alerts if competition is nearly sold out
    await check_and_send_competition_alerts(purchase.competition_id, new_sold, comp["max_tickets"])
    
    # Check and award gamification badges
    asyncio.create_task(check_and_award_badges(current_user["user_id"]))
    
    return purchased_tickets

# ==================== CART SYSTEM ====================

@router.post("/cart/purchase")
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

@router.get("/tickets/my", response_model=List[TicketResponse])
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

@router.get("/tickets/search", response_model=TicketSearchResult)
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

@router.post("/tickets/purchase-viva")
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

@router.post("/tickets/enter-free")
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

