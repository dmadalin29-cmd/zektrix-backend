# -*- coding: utf-8 -*-
"""Marketing routes: Bundle Deals, Push Campaigns, TikTok Live Draw"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from database import db
from dependencies import get_current_user, get_admin_user
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# ==================== BUNDLE DEALS ====================

class BundleCreate(BaseModel):
    name: str
    quantity: int
    discount_percent: float
    is_active: bool = True

class BundleUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    discount_percent: Optional[float] = None
    is_active: Optional[bool] = None

@router.get("/bundles")
async def get_bundles():
    """Public: Get active bundle deals"""
    bundles = await db.bundles.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("quantity", 1).to_list(20)
    return bundles

@router.get("/admin/bundles")
async def admin_get_bundles(admin: dict = Depends(get_admin_user)):
    """Admin: Get all bundles"""
    bundles = await db.bundles.find({}, {"_id": 0}).sort("quantity", 1).to_list(50)
    return bundles

@router.post("/admin/bundles")
async def create_bundle(data: BundleCreate, admin: dict = Depends(get_admin_user)):
    """Admin: Create a bundle deal"""
    bundle = {
        "bundle_id": f"bnd_{uuid.uuid4().hex[:12]}",
        "name": data.name,
        "quantity": data.quantity,
        "discount_percent": data.discount_percent,
        "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.bundles.insert_one(bundle)
    bundle.pop("_id", None)
    return bundle

@router.put("/admin/bundles/{bundle_id}")
async def update_bundle(bundle_id: str, data: BundleUpdate, admin: dict = Depends(get_admin_user)):
    """Admin: Update a bundle"""
    update = {k: v for k, v in data.dict().items() if v is not None}
    if not update:
        raise HTTPException(400, "Nothing to update")
    await db.bundles.update_one({"bundle_id": bundle_id}, {"$set": update})
    return {"success": True}

@router.delete("/admin/bundles/{bundle_id}")
async def delete_bundle(bundle_id: str, admin: dict = Depends(get_admin_user)):
    """Admin: Delete a bundle"""
    await db.bundles.delete_one({"bundle_id": bundle_id})
    return {"success": True}


# ==================== PUSH CAMPAIGNS ====================

class CampaignCreate(BaseModel):
    title: str
    message: str
    url: str = "https://zektrix.uk"
    audience: str = "all"  # "all", "active", "subscribers"

@router.get("/admin/campaigns")
async def get_campaigns(admin: dict = Depends(get_admin_user)):
    """Admin: Get campaign history"""
    campaigns = await db.push_campaigns.find({}, {"_id": 0}).sort("sent_at", -1).to_list(50)
    return campaigns

@router.post("/admin/campaigns/send")
async def send_campaign(data: CampaignCreate, admin: dict = Depends(get_admin_user)):
    """Admin: Send a push campaign to users"""
    try:
        from push_service import send_web_push
    except ImportError:
        from backend.push_service import send_web_push

    # Build audience query
    if data.audience == "active":
        # Users who purchased in last 30 days
        thirty_days = (datetime.now(timezone.utc).replace(day=1)).isoformat()
        active_tickets = await db.tickets.distinct("user_id", {"purchased_at": {"$gte": thirty_days}})
        user_filter = {"user_id": {"$in": active_tickets}}
    elif data.audience == "subscribers":
        active_subs = await db.subscriptions.distinct("user_id", {"status": "active"})
        user_filter = {"user_id": {"$in": active_subs}}
    else:
        user_filter = {}

    # Get all push subscriptions matching the audience
    subs = await db.push_subscriptions.find(user_filter, {"_id": 0}).to_list(10000)

    sent = 0
    failed = 0
    for sub in subs:
        try:
            await send_web_push(sub, {
                "title": data.title,
                "body": data.message,
                "url": data.url,
                "tag": "campaign",
                "requireInteraction": True
            })
            sent += 1
        except Exception:
            failed += 1
            # Clean expired subscriptions
            await db.push_subscriptions.delete_one({"endpoint": sub["endpoint"]})

    # Save campaign record
    campaign = {
        "campaign_id": f"camp_{uuid.uuid4().hex[:8]}",
        "title": data.title,
        "message": data.message,
        "url": data.url,
        "audience": data.audience,
        "sent_count": sent,
        "failed_count": failed,
        "total_targeted": len(subs),
        "sent_by": admin["user_id"],
        "sent_at": datetime.now(timezone.utc).isoformat()
    }
    await db.push_campaigns.insert_one(campaign)
    campaign.pop("_id", None)

    logger.info(f"Push campaign sent: {sent}/{len(subs)} delivered, {failed} failed")
    return {"success": True, "sent": sent, "failed": failed, "total": len(subs)}

@router.get("/admin/campaigns/audience-stats")
async def get_audience_stats(admin: dict = Depends(get_admin_user)):
    """Admin: Get audience size stats"""
    total_subs = await db.push_subscriptions.count_documents({})
    thirty_days = (datetime.now(timezone.utc).replace(day=1)).isoformat()
    active_user_ids = await db.tickets.distinct("user_id", {"purchased_at": {"$gte": thirty_days}})
    active_subs = await db.push_subscriptions.count_documents({"user_id": {"$in": active_user_ids}})
    sub_user_ids = await db.subscriptions.distinct("user_id", {"status": "active"})
    subscriber_subs = await db.push_subscriptions.count_documents({"user_id": {"$in": sub_user_ids}})

    return {
        "all": total_subs,
        "active": active_subs,
        "subscribers": subscriber_subs
    }


# ==================== TIKTOK LIVE DRAW ====================

class LiveDrawUpdate(BaseModel):
    competition_id: str
    is_live: bool
    tiktok_live_url: Optional[str] = None

@router.get("/live-draw")
async def get_live_draw():
    """Public: Check if there's an active live draw"""
    draw = await db.settings.find_one({"key": "live_draw"}, {"_id": 0})
    if not draw or not draw.get("value", {}).get("is_live"):
        return {"is_live": False}
    return draw.get("value", {"is_live": False})

@router.put("/admin/live-draw")
async def update_live_draw(data: LiveDrawUpdate, admin: dict = Depends(get_admin_user)):
    """Admin: Set/unset live draw"""
    value = {
        "is_live": data.is_live,
        "competition_id": data.competition_id,
        "tiktok_live_url": data.tiktok_live_url,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.settings.update_one(
        {"key": "live_draw"},
        {"$set": {"key": "live_draw", "value": value}},
        upsert=True
    )

    # If going live, send push to all users
    if data.is_live:
        try:
            from push_service import send_web_push
        except ImportError:
            from backend.push_service import send_web_push

        comp = await db.competitions.find_one({"competition_id": data.competition_id}, {"_id": 0, "title": 1})
        title = comp["title"] if comp else "Competition"

        subs = await db.push_subscriptions.find({}, {"_id": 0}).to_list(10000)
        sent = 0
        for sub in subs:
            try:
                await send_web_push(sub, {
                    "title": "LIVE DRAW ACUM!",
                    "body": f"Extragerea pentru {title} este LIVE! Urmareste acum!",
                    "url": data.tiktok_live_url or "https://zektrix.uk",
                    "tag": "live-draw",
                    "requireInteraction": True
                })
                sent += 1
            except Exception:
                pass
        logger.info(f"Live draw notification sent to {sent} devices")

    return {"success": True}


# ==================== TIKTOK VIDEO GALLERY ====================

class TikTokVideoAdd(BaseModel):
    url: str
    title: Optional[str] = ""

@router.get("/tiktok-videos")
async def get_tiktok_videos():
    """Public: Get TikTok video gallery"""
    videos = await db.tiktok_videos.find({"is_active": True}, {"_id": 0}).sort("created_at", -1).to_list(20)
    return videos

@router.post("/admin/tiktok-videos")
async def add_tiktok_video(data: TikTokVideoAdd, admin: dict = Depends(get_admin_user)):
    """Admin: Add a TikTok video to gallery"""
    import re
    match = re.search(r'/video/(\d+)', data.url)
    if not match:
        match = re.search(r'tiktok\.com/.*?/(\d{15,})', data.url)
    video_id = match.group(1) if match else None
    if not video_id:
        raise HTTPException(400, "URL TikTok invalid. Format: https://www.tiktok.com/@user/video/123456789")
    
    video = {
        "video_uid": f"tv_{uuid.uuid4().hex[:12]}",
        "url": data.url,
        "video_id": video_id,
        "embed_url": f"https://www.tiktok.com/embed/v2/{video_id}",
        "title": data.title or "",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tiktok_videos.insert_one(video)
    video.pop("_id", None)
    return video

@router.delete("/admin/tiktok-videos/{video_uid}")
async def delete_tiktok_video(video_uid: str, admin: dict = Depends(get_admin_user)):
    """Admin: Remove a TikTok video"""
    result = await db.tiktok_videos.delete_one({"video_uid": video_uid})
    if result.deleted_count == 0:
        raise HTTPException(404, "Video not found")
    return {"success": True}


# ==================== ADVANCED ANALYTICS ====================

@router.get("/admin/analytics/advanced")
async def get_advanced_analytics(admin: dict = Depends(get_admin_user)):
    """Admin: Advanced analytics - conversion, AOV, retention, revenue breakdown"""

    thirty_days = (datetime.now(timezone.utc).replace(day=1)).isoformat()
    seven_days = (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0) 
                  .__class__(datetime.now(timezone.utc).year, datetime.now(timezone.utc).month, 
                             max(1, datetime.now(timezone.utc).day - 7))).isoformat()

    # Parallel queries
    total_users_task = db.users.count_documents({})
    buyers_task = db.tickets.distinct("user_id")
    
    # Revenue by type
    revenue_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$transaction_type",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    revenue_type_task = db.transactions.aggregate(revenue_pipeline).to_list(20)

    # Orders (purchases) with amounts
    orders_pipeline = [
        {"$match": {"status": "completed", "amount": {"$gt": 0}}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$amount"},
            "order_count": {"$sum": 1},
            "avg_order": {"$avg": "$amount"}
        }}
    ]
    orders_task = db.transactions.aggregate(orders_pipeline).to_list(1)

    # Weekly revenue
    weekly_pipeline = [
        {"$match": {"status": "completed", "amount": {"$gt": 0}, "created_at": {"$gte": thirty_days}}},
        {"$addFields": {"day": {"$substr": ["$created_at", 0, 10]}}},
        {"$group": {"_id": "$day", "revenue": {"$sum": "$amount"}, "orders": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    weekly_task = db.transactions.aggregate(weekly_pipeline).to_list(31)

    # Retention: users who purchased more than once
    repeat_pipeline = [
        {"$group": {"_id": "$user_id", "purchase_count": {"$sum": 1}}},
        {"$group": {
            "_id": None,
            "total_buyers": {"$sum": 1},
            "repeat_buyers": {"$sum": {"$cond": [{"$gte": ["$purchase_count", 2]}, 1, 0]}},
            "loyal_buyers": {"$sum": {"$cond": [{"$gte": ["$purchase_count", 5]}, 1, 0]}}
        }}
    ]
    retention_task = db.tickets.aggregate(repeat_pipeline).to_list(1)

    # Top spenders
    top_spenders_pipeline = [
        {"$match": {"status": "completed", "amount": {"$gt": 0}}},
        {"$group": {"_id": "$user_id", "total_spent": {"$sum": "$amount"}, "orders": {"$sum": 1}}},
        {"$sort": {"total_spent": -1}},
        {"$limit": 10}
    ]
    top_spenders_task = db.transactions.aggregate(top_spenders_pipeline).to_list(10)

    # Subscription stats
    sub_stats_task = asyncio.gather(
        db.subscriptions.count_documents({"status": "active"}),
        db.subscriptions.count_documents({})
    )

    # Await all
    (total_users, buyers, revenue_by_type, orders_result, 
     weekly_result, retention_result, top_spenders, sub_stats) = await asyncio.gather(
        total_users_task, buyers_task, revenue_type_task, orders_task,
        weekly_task, retention_task, top_spenders_task, sub_stats_task
    )

    # Process results
    unique_buyers = len(buyers)
    conversion_rate = round((unique_buyers / total_users * 100), 1) if total_users > 0 else 0
    
    orders_data = orders_result[0] if orders_result else {"total_revenue": 0, "order_count": 0, "avg_order": 0}
    aov = round(orders_data.get("avg_order", 0), 2)

    retention_data = retention_result[0] if retention_result else {"total_buyers": 0, "repeat_buyers": 0, "loyal_buyers": 0}
    repeat_rate = round((retention_data["repeat_buyers"] / retention_data["total_buyers"] * 100), 1) if retention_data["total_buyers"] > 0 else 0

    # Enrich top spenders with usernames
    spender_ids = [s["_id"] for s in top_spenders]
    spender_users = await db.users.find({"user_id": {"$in": spender_ids}}, {"_id": 0, "user_id": 1, "username": 1}).to_list(10)
    username_map = {u["user_id"]: u["username"] for u in spender_users}

    revenue_breakdown = {r["_id"]: {"total": round(r["total"], 2), "count": r["count"]} for r in revenue_by_type}

    return {
        "conversion_rate": conversion_rate,
        "total_users": total_users,
        "unique_buyers": unique_buyers,
        "aov": aov,
        "total_revenue": round(orders_data.get("total_revenue", 0), 2),
        "total_orders": orders_data.get("order_count", 0),
        "repeat_rate": repeat_rate,
        "repeat_buyers": retention_data.get("repeat_buyers", 0),
        "loyal_buyers": retention_data.get("loyal_buyers", 0),
        "revenue_by_day": [{"date": r["_id"], "revenue": round(r["revenue"], 2), "orders": r["orders"]} for r in weekly_result],
        "revenue_breakdown": revenue_breakdown,
        "top_spenders": [
            {"username": username_map.get(s["_id"], "Unknown"), "total_spent": round(s["total_spent"], 2), "orders": s["orders"]}
            for s in top_spenders
        ],
        "active_subscriptions": sub_stats[0],
        "total_subscriptions": sub_stats[1]
    }
