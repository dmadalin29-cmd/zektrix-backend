# -*- coding: utf-8 -*-
"""Background tasks / bots"""
from database import db
from config import *
from helpers import notify_user_push, notify_competition_participants_push, generate_random_ticket_number
from datetime import datetime, timezone, timedelta
import asyncio, random, os, httpx, logging

logger = logging.getLogger("server")

try:
    from email_service import send_winner_notification_email
except ImportError:
    from backend.email_service import send_winner_notification_email


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
        await draw_competition_winner(active_perm["competition_id"])
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
        "image_url": f"https://images.unsplash.com/photo-1621981386829-9b458a2cddde?w=800&q=80",  # Cash/money image
        "prize_description": f"{template['prize_amount']} RON în numerar",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_auto_managed": True,
        "auto_prize_amount": template["prize_amount"],
        "qualification_question": {
            "question": f"Cât de mult este premiul acestei competiții?",
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
# Admin endpoint to list available special configs
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
    
    # Push notification to winner
    await notify_user_push(
        winner_ticket["user_id"],
        "Felicitări! Ai câștigat!",
        f"Ai câștigat la {comp['title']}! Locul #{winner_ticket['ticket_number']} este câștigător!",
        f"https://zektrix.uk/competitions/{competition_id}"
    )
    
    # Push notification to all other participants
    await notify_competition_participants_push(
        competition_id,
        f"{comp['title']} - Câștigător extras!",
        f"Câștigătorul a fost extras! Verifică rezultatele.",
        "https://zektrix.uk/winners"
    )
    
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
                logger.info(f"[PERMANENT-BOT] Permanent competition full! Drawing winner...")
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

async def subscription_renewal_bot():
    """Background task to auto-renew expired subscriptions"""
    logger.info("[SUB-BOT] Starting Subscription Renewal Bot...")
    await asyncio.sleep(30)
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            # Find subscriptions that expired and have auto_renew enabled
            expired_subs = await db.subscriptions.find({
                "status": "active",
                "auto_renew": True,
                "expires_at": {"$lt": now.isoformat()}
            }, {"_id": 0}).to_list(100)
            
            for sub in expired_subs:
                plan = next((p for p in SUBSCRIPTION_PLANS if p["plan_id"] == sub["plan_id"]), None)
                if not plan:
                    await db.subscriptions.update_one(
                        {"subscription_id": sub["subscription_id"]},
                        {"$set": {"status": "expired"}}
                    )
                    continue
                
                user = await db.users.find_one({"user_id": sub["user_id"]}, {"_id": 0})
                if not user:
                    continue
                
                balance = user.get("balance", 0)
                
                if balance >= plan["price"]:
                    # Renew from wallet
                    new_sub_id = f"sub_{uuid.uuid4().hex[:12]}"
                    new_expires = now + timedelta(days=plan["duration_days"])
                    
                    await db.users.update_one(
                        {"user_id": sub["user_id"]},
                        {"$inc": {"balance": -plan["price"]}}
                    )
                    
                    # Expire old, create new
                    await db.subscriptions.update_one(
                        {"subscription_id": sub["subscription_id"]},
                        {"$set": {"status": "renewed"}}
                    )
                    
                    await db.subscriptions.insert_one({
                        "subscription_id": new_sub_id,
                        "user_id": sub["user_id"],
                        "username": sub.get("username", ""),
                        "email": sub.get("email", ""),
                        "plan_id": plan["plan_id"],
                        "plan_name": plan["name"],
                        "price": plan["price"],
                        "entries_per_competition": plan["entries_per_competition"],
                        "status": "active",
                        "auto_renew": True,
                        "payment_method": "wallet",
                        "started_at": now.isoformat(),
                        "expires_at": new_expires.isoformat(),
                        "created_at": now.isoformat(),
                        "tickets_distributed": 0,
                        "renewed_from": sub["subscription_id"]
                    })
                    
                    await db.transactions.insert_one({
                        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
                        "user_id": sub["user_id"],
                        "transaction_type": "subscription_renewal",
                        "amount": -plan["price"],
                        "status": "completed",
                        "description": f"Auto-reinnoire {plan['name']}",
                        "subscription_id": new_sub_id,
                        "created_at": now.isoformat()
                    })
                    
                    asyncio.create_task(distribute_subscription_tickets(
                        sub["user_id"], new_sub_id, plan["entries_per_competition"]
                    ))
                    
                    await notify_user_push(
                        sub["user_id"],
                        "Abonament Reinnoit!",
                        f"{plan['name']} a fost reinnoit automat din wallet (£{plan['price']:.2f}).",
                        "https://zektrix.uk/subscriptions"
                    )
                    
                    logger.info(f"[SUB-BOT] Auto-renewed subscription for {sub['user_id']} from wallet")
                else:
                    # Insufficient wallet balance - try creating Viva payment
                    # For now, just expire and notify user to top up
                    await db.subscriptions.update_one(
                        {"subscription_id": sub["subscription_id"]},
                        {"$set": {"status": "expired"}}
                    )
                    
                    await notify_user_push(
                        sub["user_id"],
                        "Abonament Expirat",
                        f"Fonduri insuficiente pentru reinnoire ({plan['name']} - £{plan['price']:.2f}). Alimenteaza wallet-ul!",
                        "https://zektrix.uk/wallet"
                    )
                    
                    logger.info(f"[SUB-BOT] Subscription expired for {sub['user_id']} - insufficient funds")
            
            # Also expire subscriptions without auto_renew
            no_renew = await db.subscriptions.find({
                "status": "active",
                "auto_renew": False,
                "expires_at": {"$lt": now.isoformat()}
            }, {"_id": 0}).to_list(100)
            
            for sub in no_renew:
                await db.subscriptions.update_one(
                    {"subscription_id": sub["subscription_id"]},
                    {"$set": {"status": "expired"}}
                )
        
        except Exception as e:
            logger.error(f"[SUB-BOT] Error: {e}")
        
        # Check every 5 minutes
        await asyncio.sleep(300)

# ==================== DAILY EMAIL BOT ====================
# Sends daily email to all users with competition updates

async def generate_daily_email_html(competitions: list, user_name: str, user_id: str = "") -> str:
    """Generate modern premium email HTML for daily digest"""
    
    sorted_comps = sorted(competitions, key=lambda x: (x.get("sold_tickets", 0) / max(x.get("max_tickets", 1), 1)), reverse=True)
    
    # Calculate total prizes as ticket_price × max_tickets (realistic prize pool)
    total_prize_pool = 0
    for comp in sorted_comps:
        price = comp.get("ticket_price", 0) or 0
        max_t = comp.get("max_tickets", 0) or 0
        if price > 0:
            total_prize_pool += price * max_t
        elif comp.get("auto_prize_amount"):
            total_prize_pool += comp["auto_prize_amount"]
    
    total_tickets_available = sum(comp.get("max_tickets", 0) - comp.get("sold_tickets", 0) for comp in sorted_comps)
    hot_comps = [c for c in sorted_comps if (c.get("sold_tickets", 0) / max(c.get("max_tickets", 1), 1)) > 0.6]
    
    # Build competition cards with images
    comp_cards = ""
    for comp in sorted_comps[:6]:
        progress = int((comp.get("sold_tickets", 0) / max(comp.get("max_tickets", 1), 1)) * 100)
        remaining = comp.get("max_tickets", 0) - comp.get("sold_tickets", 0)
        prize = comp.get("prize_description") or comp.get("title", "Premiu")
        image_url = comp.get("image_url", "")
        comp_link = f"https://zektrix.uk/competitions/{comp.get('competition_id', '')}"
        price = comp.get("ticket_price", 0) or 0
        max_t = comp.get("max_tickets", 0) or 0
        comp_prize_pool = price * max_t if price > 0 else (comp.get("auto_prize_amount") or 0)
        is_free = price == 0
        
        if progress >= 80:
            urgency_color = "#ef4444"
            urgency_text = "APROAPE SOLD OUT!"
            badge_bg = "linear-gradient(135deg, #ef4444, #dc2626)"
        elif progress >= 60:
            urgency_color = "#f97316"
            urgency_text = "SE VINDE RAPID!"
            badge_bg = "linear-gradient(135deg, #f97316, #ea580c)"
        elif is_free:
            urgency_color = "#10b981"
            urgency_text = "GRATUIT!"
            badge_bg = "linear-gradient(135deg, #10b981, #059669)"
        else:
            urgency_color = "#8b5cf6"
            urgency_text = ""
            badge_bg = ""
        
        price_display = "GRATUIT" if is_free else f"£{price:.2f}"
        
        image_section = ""
        if image_url:
            image_section = f'''
                                                <a href="{comp_link}" style="text-decoration: none; display: block;">
                                                    <img src="{image_url}" alt="{comp.get('title', '')}" style="width: 100%; height: 200px; object-fit: cover; display: block; border-radius: 12px 12px 0 0;" />
                                                </a>'''
        
        urgency_badge = ""
        if urgency_text:
            urgency_badge = f'<span style="display: inline-block; background: {badge_bg}; color: white; padding: 3px 10px; border-radius: 20px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;">{urgency_text}</span>'
        
        comp_cards += f'''
                    <tr>
                        <td style="padding: 0 0 16px 0;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0d0b1a; border: 1px solid #1e1b3a; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 0;">
                                        {image_section}
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="padding: 16px 18px;">
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                                        <tr>
                                                            <td>
                                                                <a href="{comp_link}" style="text-decoration: none; color: #ffffff; font-size: 17px; font-weight: 700; display: block; margin-bottom: 6px;">{comp.get("title", "")}</a>
                                                                {urgency_badge}
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%; margin-top: 12px;">
                                                        <tr>
                                                            <td style="width: 50%;">
                                                                <p style="color: #6b7280; margin: 0; font-size: 11px;">Premiu</p>
                                                                <p style="color: #fbbf24; margin: 2px 0 0 0; font-size: 14px; font-weight: 700;">{prize[:40]}</p>
                                                            </td>
                                                            <td style="width: 50%; text-align: right;">
                                                                <p style="color: #6b7280; margin: 0; font-size: 11px;">Pret loc</p>
                                                                <p style="color: #10b981; margin: 2px 0 0 0; font-size: 14px; font-weight: 700;">{price_display}</p>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%; margin-top: 12px;">
                                                        <tr>
                                                            <td style="background: #1a1730; border-radius: 6px; height: 8px; overflow: hidden;">
                                                                <div style="background: linear-gradient(90deg, {urgency_color}, #a855f7); height: 8px; width: {max(progress, 2)}%; border-radius: 6px;"></div>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    <table cellpadding="0" cellspacing="0" style="width: 100%; margin-top: 8px;">
                                                        <tr>
                                                            <td>
                                                                <span style="color: #6b7280; font-size: 11px;"><span style="color: {urgency_color}; font-weight: 700;">{progress}%</span> ocupat</span>
                                                                <span style="color: #6b7280; font-size: 11px; margin-left: 8px;"><span style="color: #10b981; font-weight: 600;">{remaining:,}</span> locuri</span>
                                                            </td>
                                                            <td style="text-align: right;">
                                                                <a href="{comp_link}" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; text-decoration: none; padding: 7px 18px; border-radius: 20px; font-size: 12px; font-weight: 600;">Participa</a>
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
    
    # Hot alert
    hot_alert_html = ""
    if hot_comps:
        hot_alert_html = f'''<tr>
                        <td style="padding-bottom: 20px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #451a03 0%, #7c2d12 100%); border: 1px solid #f9731640; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 14px 20px; text-align: center;">
                                        <p style="color: #fed7aa; margin: 0; font-size: 13px; font-weight: 600;">
                                            &#128293; <strong style="color: #ffffff;">{len(hot_comps)} competitii</strong> se vand rapid! Nu rata sansa!
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>'''
    
    # Recent winners
    recent_winners = await db.winners.find({}, {"_id": 0}).sort("announced_at", -1).limit(3).to_list(3)
    winners_html = ""
    if recent_winners:
        winner_items = ""
        for w in recent_winners:
            winner_items += f'''
                                <tr>
                                    <td style="padding: 10px 16px; border-bottom: 1px solid #1e1b3a;">
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="width: 36px; vertical-align: middle;">
                                                    <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #fbbf24, #f59e0b); border-radius: 50%; text-align: center; line-height: 32px; font-size: 14px;">&#127942;</div>
                                                </td>
                                                <td style="vertical-align: middle;">
                                                    <p style="color: #ffffff; margin: 0; font-size: 13px; font-weight: 600;">{w.get("username", "Castigator")}</p>
                                                    <p style="color: #6b7280; margin: 0; font-size: 11px;">Loc #{w.get("ticket_number", "?")}</p>
                                                </td>
                                                <td style="text-align: right; vertical-align: middle;">
                                                    <p style="color: #fbbf24; margin: 0; font-size: 11px; font-weight: 600;">{w.get("competition_title", "")[:25]}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>'''
        winners_html = f'''
                    <tr>
                        <td style="padding: 25px 0 15px 0;">
                            <p style="color: #fbbf24; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin: 0; font-weight: 700;">&#127942; CASTIGATORI RECENTI</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding-bottom: 25px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0d0b1a; border: 1px solid #1e1b3a; border-radius: 12px; overflow: hidden;">
                                {winner_items}
                            </table>
                        </td>
                    </tr>'''
    
    # Format prize pool display
    if total_prize_pool >= 1000:
        prize_display = f"£{total_prize_pool:,.0f}"
    else:
        prize_display = f"£{total_prize_pool:.0f}"
    
    email_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zektrix - Competitii Active</title>
</head>
<body style="margin: 0; padding: 0; background-color: #030014; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table cellpadding="0" cellspacing="0" style="width: 100%; background-color: #030014;">
        <tr>
            <td style="padding: 30px 16px;">
                <table cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; width: 100%;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="text-align: center; padding-bottom: 24px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #0d0b1a 0%, #1a0a2e 50%, #0d0b1a 100%); border: 1px solid #8b5cf630; border-radius: 16px;">
                                <tr>
                                    <td style="padding: 28px 20px;">
                                        <h1 style="margin: 0 0 4px 0; font-size: 32px; font-weight: 900; letter-spacing: -1px; text-align: center;">
                                            <span style="color: #8b5cf6;">ZEKTRIX</span><span style="color: #ffffff;">.UK</span>
                                        </h1>
                                        <p style="color: #6b7280; margin: 0; font-size: 12px; text-align: center; letter-spacing: 1px;">PREMII REALE &bull; SANSE REALE &bull; CASTIGATORI REALI</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Greeting + Stats -->
                    <tr>
                        <td style="padding-bottom: 20px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: linear-gradient(135deg, #0d0b1a 0%, #130d24 100%); border: 1px solid #1e1b3a; border-radius: 16px;">
                                <tr>
                                    <td style="padding: 24px;">
                                        <p style="color: #9ca3af; margin: 0 0 4px 0; font-size: 14px;">Salut, <strong style="color: #ffffff;">{user_name}</strong>!</p>
                                        <p style="color: #6b7280; margin: 0 0 20px 0; font-size: 13px; line-height: 1.5;">
                                            Avem <strong style="color: #8b5cf6;">{len(sorted_comps)} competitii active</strong> cu premii in valoare totala de
                                        </p>
                                        <p style="text-align: center; margin: 0 0 20px 0;">
                                            <span style="font-size: 36px; font-weight: 900; color: #fbbf24; letter-spacing: -1px;">{prize_display}</span>
                                        </p>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="width: 33%; text-align: center; padding: 12px 4px; background: #0a0818; border-radius: 10px;">
                                                    <p style="color: #8b5cf6; margin: 0; font-size: 20px; font-weight: 800;">{len(sorted_comps)}</p>
                                                    <p style="color: #6b7280; margin: 2px 0 0 0; font-size: 10px;">Competitii</p>
                                                </td>
                                                <td style="width: 1%;"></td>
                                                <td style="width: 33%; text-align: center; padding: 12px 4px; background: #0a0818; border-radius: 10px;">
                                                    <p style="color: #f97316; margin: 0; font-size: 20px; font-weight: 800;">{total_tickets_available:,}</p>
                                                    <p style="color: #6b7280; margin: 2px 0 0 0; font-size: 10px;">Locuri Libere</p>
                                                </td>
                                                <td style="width: 1%;"></td>
                                                <td style="width: 33%; text-align: center; padding: 12px 4px; background: #0a0818; border-radius: 10px;">
                                                    <p style="color: #10b981; margin: 0; font-size: 20px; font-weight: 800;">{prize_display}</p>
                                                    <p style="color: #6b7280; margin: 2px 0 0 0; font-size: 10px;">Premii Totale</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    {hot_alert_html}
                    
                    <!-- Section Title -->
                    <tr>
                        <td style="padding-bottom: 12px;">
                            <p style="color: #a78bfa; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin: 0; font-weight: 700;">COMPETITII DISPONIBILE</p>
                        </td>
                    </tr>
                    
                    {comp_cards}
                    
                    <!-- CTA -->
                    <tr>
                        <td style="text-align: center; padding: 20px 0 30px 0;">
                            <a href="https://zektrix.uk/competitions" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; text-decoration: none; padding: 16px 48px; border-radius: 50px; font-weight: 700; font-size: 15px; letter-spacing: 0.5px;">
                                VEZI TOATE COMPETITIILE &#8594;
                            </a>
                        </td>
                    </tr>
                    
                    {winners_html}
                    
                    <!-- Why Zektrix -->
                    <tr>
                        <td style="padding-bottom: 25px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0d0b1a; border: 1px solid #1e1b3a; border-radius: 12px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #ffffff; margin: 0 0 14px 0; font-size: 14px; font-weight: 700; text-align: center;">De ce Zektrix?</p>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="padding: 6px 8px; width: 50%;"><p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Extrageri transparente</p></td>
                                                <td style="padding: 6px 8px; width: 50%;"><p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Premii platite instant</p></td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 8px;"><p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Locuri de la £0.99</p></td>
                                                <td style="padding: 6px 8px;"><p style="color: #9ca3af; margin: 0; font-size: 12px;"><span style="color: #10b981;">&#10003;</span> Suport 24/7 WhatsApp</p></td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding-top: 10px;">
                            <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0d0b1a; border: 1px solid #1e1b3a; border-radius: 16px; overflow: hidden;">
                                <tr>
                                    <td style="padding: 28px 24px;">
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 20px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <h3 style="margin: 0; font-size: 22px; font-weight: 900;">
                                                        <span style="color: #8b5cf6;">ZEKTRIX</span><span style="color: #ffffff;">.UK</span>
                                                    </h3>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 20px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <a href="https://zektrix.uk" style="display: inline-block; background: #1a1730; color: #8b5cf6; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-size: 11px; font-weight: 600; margin: 0 3px;">&#127760; Website</a>
                                                    <a href="https://wa.me/40730268067" style="display: inline-block; background: #1a1730; color: #22c55e; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-size: 11px; font-weight: 600; margin: 0 3px;">&#128172; WhatsApp</a>
                                                    <a href="https://tiktok.com/@zektrix.uk" style="display: inline-block; background: #1a1730; color: #ffffff; text-decoration: none; padding: 8px 16px; border-radius: 20px; font-size: 11px; font-weight: 600; margin: 0 3px;">&#9835; TikTok</a>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 16px;">
                                            <tr><td style="height: 1px; background: linear-gradient(90deg, transparent, #1e1b3a, transparent);"></td></tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 16px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <p style="color: #6b7280; font-size: 10px; margin: 0 0 8px 0; line-height: 1.5;">
                                                        Ai primit acest email pentru ca esti inregistrat pe <strong style="color: #8b5cf6;">Zektrix.uk</strong>.<br/>
                                                        Conform GDPR, datele tale sunt in siguranta si nu sunt partajate cu terti.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; margin-bottom: 16px;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <a href="https://zektrix.uk/faq" style="color: #6b7280; text-decoration: none; font-size: 10px; margin: 0 8px;">FAQ</a>
                                                    <span style="color: #374151;">|</span>
                                                    <a href="https://zektrix.uk/privacy" style="color: #6b7280; text-decoration: none; font-size: 10px; margin: 0 8px;">Confidentialitate</a>
                                                    <span style="color: #374151;">|</span>
                                                    <a href="https://zektrix.uk/terms" style="color: #6b7280; text-decoration: none; font-size: 10px; margin: 0 8px;">Termeni</a>
                                                    <span style="color: #374151;">|</span>
                                                    <a href="https://zektrix.uk/dashboard" style="color: #6b7280; text-decoration: none; font-size: 10px; margin: 0 8px;">Contul Meu</a>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%; background: #0a0818; border-radius: 10px; margin-bottom: 16px;">
                                            <tr>
                                                <td style="padding: 14px; text-align: center;">
                                                    <p style="color: #4b5563; font-size: 10px; margin: 0 0 8px 0;">Nu mai vrei aceste email-uri?</p>
                                                    <a href="https://zektrix.uk/unsubscribe/{user_id}" style="color: #ef4444; text-decoration: none; font-size: 11px; font-weight: 600;">Dezabonare</a>
                                                </td>
                                            </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" style="width: 100%;">
                                            <tr>
                                                <td style="text-align: center;">
                                                    <p style="color: #374151; font-size: 9px; margin: 0;">&#169; 2026 Zektrix UK Ltd. Toate drepturile rezervate.</p>
                                                    <p style="color: #2d3748; font-size: 8px; margin: 4px 0 0 0;">Zektrix UK Ltd &bull; c/o Bartle House, Oxford Court &bull; Manchester, M23 WQ &bull; United Kingdom</p>
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
        
        # Calculate total prize pool for subject line
        total_pool = 0
        for c in competitions:
            p = c.get("ticket_price", 0) or 0
            m = c.get("max_tickets", 0) or 0
            total_pool += p * m if p > 0 else (c.get("auto_prize_amount") or 0)
        
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": [user["email"]],
            "subject": f"[ZEKTRIX] {len(competitions)} Competitii Active - Premii de £{total_pool:,.0f}!",
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

# ==================== RE-ENGAGEMENT EMAIL BOT ====================
async def reengagement_email_bot():
    """Send re-engagement emails to users inactive for 7+ days"""
    while True:
        try:
            await asyncio.sleep(3600 * 6)  # Check every 6 hours
            
            seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            
            # Find users who have purchased before but not in the last 7 days
            active_comps = await db.competitions.find({"status": "active"}, {"_id": 0}).to_list(100)
            if not active_comps:
                continue
            
            # Get users with at least 1 ticket
            users_with_tickets = await db.tickets.distinct("user_id")
            
            for uid in users_with_tickets:
                user = await db.users.find_one({"user_id": uid, "is_blocked": {"$ne": True}}, {"_id": 0})
                if not user or user.get("role") == "admin":
                    continue
                
                # Check last purchase date
                last_ticket = await db.tickets.find_one(
                    {"user_id": uid},
                    sort=[("purchased_at", -1)]
                )
                if not last_ticket:
                    continue
                
                last_purchase = last_ticket.get("purchased_at", "")
                if isinstance(last_purchase, str) and last_purchase > seven_days_ago:
                    continue  # Purchased recently, skip
                
                # Check if re-engagement email already sent recently
                last_reengagement = await db.reengagement_emails.find_one(
                    {"user_id": uid, "sent_at": {"$gt": (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()}}
                )
                if last_reengagement:
                    continue  # Already sent within 14 days
                
                # Build email with top 3 active competitions
                top_comps = sorted(active_comps, key=lambda x: x.get("sold_tickets", 0) / max(x.get("max_tickets", 1), 1), reverse=True)[:3]
                
                comps_html = ""
                for comp in top_comps:
                    pct = round((comp.get("sold_tickets", 0) / max(comp.get("max_tickets", 1), 1)) * 100)
                    img = comp.get("image_url", "")
                    comps_html += f"""
                    <div style="background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.2);border-radius:16px;padding:16px;margin-bottom:12px;">
                        <div style="font-weight:700;color:#ffffff;font-size:16px;margin-bottom:8px;">{comp.get('title','')}</div>
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="color:#a78bfa;font-size:13px;">{pct}% vandut</span>
                            <span style="color:#10b981;font-weight:700;font-size:14px;">{comp.get('ticket_price','?')} £/loc</span>
                        </div>
                        <div style="background:rgba(255,255,255,0.1);border-radius:8px;height:6px;margin-top:8px;overflow:hidden;">
                            <div style="background:linear-gradient(90deg,#8b5cf6,#ff5e00);height:100%;width:{pct}%;border-radius:8px;"></div>
                        </div>
                    </div>"""
                
                email_html = f"""
                <div style="font-family:'Outfit',Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0614;color:#fff;border-radius:20px;overflow:hidden;">
                    <div style="background:linear-gradient(135deg,#8b5cf6,#ff5e00);padding:40px 30px;text-align:center;">
                        <h1 style="margin:0;font-size:28px;font-weight:900;color:#fff;">Ne e dor de tine! 💜</h1>
                        <p style="margin:10px 0 0;color:rgba(255,255,255,0.9);font-size:15px;">Au aparut competitii noi care te asteapta</p>
                    </div>
                    <div style="padding:30px;">
                        <p style="color:#a0a0b0;font-size:14px;line-height:1.6;margin-bottom:20px;">
                            Salut <strong style="color:#fff;">{user.get('first_name', user.get('username', 'Prietene'))}</strong>!<br/>
                            Nu te-am mai vazut de ceva timp pe Zektrix. Intre timp, avem competitii incredibile care se vand rapid:
                        </p>
                        {comps_html}
                        <div style="text-align:center;margin-top:25px;">
                            <a href="https://zektrix.uk" style="display:inline-block;background:linear-gradient(135deg,#8b5cf6,#a666ff);color:#fff;text-decoration:none;padding:14px 40px;border-radius:50px;font-weight:700;font-size:15px;">VEZI COMPETITIILE</a>
                        </div>
                        <p style="color:#6e6987;font-size:11px;text-align:center;margin-top:25px;">
                            Nu vrei sa mai primesti aceste emailuri? Trimite un email la contact@x67digital.com
                        </p>
                    </div>
                </div>"""
                
                try:
                    resend_key = os.environ.get("RESEND_API_KEY")
                    if resend_key:
                        import httpx
                        async with httpx.AsyncClient() as client_http:
                            await client_http.post(
                                "https://api.resend.com/emails",
                                headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                                json={
                                    "from": "Zektrix UK <noreply@zektrix.uk>",
                                    "to": [user["email"]],
                                    "subject": "Ne e dor de tine! Competitii noi te asteapta 🎯",
                                    "html": email_html
                                }
                            )
                        
                        await db.reengagement_emails.insert_one({
                            "user_id": uid,
                            "email": user["email"],
                            "sent_at": datetime.now(timezone.utc).isoformat(),
                            "comps_included": [c.get("competition_id") for c in top_comps]
                        })
                        logger.info(f"Re-engagement email sent to {user['email']}")
                except Exception as e:
                    logger.error(f"Failed to send re-engagement email to {uid}: {e}")
                
                await asyncio.sleep(2)  # Rate limit
                
        except Exception as e:
            logger.error(f"Re-engagement bot error: {e}")
            await asyncio.sleep(3600)

