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

from fastapi.staticfiles import StaticFiles

router = APIRouter(prefix="/api")

# ==================== PUBLIC ROUTES ====================


@router.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    modules = {}
    for mod_name in ["pywebpush", "py_vapid", "emergentintegrations"]:
        try:
            __import__(mod_name)
            modules[mod_name] = "installed"
        except ImportError:
            modules[mod_name] = "MISSING"
    return {"status": "healthy", "service": "zektrix-backend", "modules": modules}

@router.get("/")
async def root():
    return {"message": "Zektrix UK Competition Platform API", "version": "2.0.0"}

# ==================== LIVE STATUS ====================

class LiveStatusUpdate(BaseModel):
    isLive: bool
    message: Optional[str] = ""

@router.get("/settings/live-status")
async def get_live_status():
    """Get current live streaming status"""
    settings = await db.settings.find_one({"key": "live_status"})
    if settings:
        return {"isLive": settings.get("isLive", False), "message": settings.get("message", "")}
    return {"isLive": False, "message": ""}

@router.put("/admin/live-status")
async def update_live_status(status: LiveStatusUpdate, current_user: dict = Depends(get_current_user)):
    """Admin: Update live streaming status"""
    if current_user.get("role") != "admin" and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.settings.update_one(
        {"key": "live_status"},
        {"$set": {"isLive": status.isLive, "message": status.message, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    # Broadcast to WebSocket clients
    await ws_manager.broadcast({"type": "live_status", "isLive": status.isLive, "message": status.message})
    
    return {"success": True, "isLive": status.isLive, "message": status.message}


@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...), current_user: dict = Depends(get_admin_user)):
    """Upload image for competitions (admin only)"""
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/heic", "image/heif"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Only JPEG, PNG, WebP, GIF and HEIC images allowed")
    
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 10MB)")
    
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    
    # Convert HEIC/HEIF to JPEG
    if ext in ("heic", "heif") or file.content_type in ("image/heic", "image/heif"):
        try:
            from PIL import Image
            import pillow_heif
            pillow_heif.register_heif_opener()
            import io
            img = Image.open(io.BytesIO(content))
            img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            content = buf.getvalue()
            ext = "jpg"
        except Exception as e:
            logger.error(f"HEIC conversion failed: {e}")
            raise HTTPException(400, "Failed to convert HEIC image. Please upload JPEG or PNG.")
    
    # Auto-optimize large images (resize if > 1920px wide, compress)
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(content))
        max_width = 1920
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        # Convert PNG to WebP for better compression (except for transparent PNGs)
        if ext == "png" and img.mode != "RGBA":
            buf = io.BytesIO()
            img.save(buf, format="WEBP", quality=85)
            content = buf.getvalue()
            ext = "webp"
        elif ext in ("jpg", "jpeg"):
            buf = io.BytesIO()
            img = img.convert("RGB") if img.mode != "RGB" else img
            img.save(buf, format="JPEG", quality=85, optimize=True)
            content = buf.getvalue()
        elif ext == "png":
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            content = buf.getvalue()
    except Exception as e:
        logger.warning(f"Image optimization skipped: {e}")
    
    if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
        ext = "jpg"
    
    import uuid
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Return the public URL
    backend_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    if backend_url:
        image_url = f"https://{backend_url}/api/uploads/{filename}"
    else:
        image_url = f"/api/uploads/{filename}"
    
    return {"url": image_url, "filename": filename}

@router.post("/admin/trigger-daily-digest")
async def trigger_daily_digest(admin: dict = Depends(get_admin_user)):
    """Manually trigger daily digest email to all users"""
    competitions = await db.competitions.find({"status": "active"}, {"_id": 0}).to_list(100)
    users = await db.users.find(
        {"email": {"$exists": True, "$ne": None}},
        {"_id": 0, "user_id": 1, "email": 1, "first_name": 1, "username": 1}
    ).to_list(10000)
    
    sent_count = 0
    for user in users:
        success = await send_daily_digest_to_user(user, competitions)
        if success:
            sent_count += 1
        await asyncio.sleep(0.3)
    
    return {"message": f"Daily digest sent to {sent_count} users", "total_users": len(users)}

# Endpoint to send test email (admin only)
@router.post("/admin/test-daily-email")
async def test_daily_email(email: str = "d.madalin29@gmail.com", admin: dict = Depends(get_admin_user)):
    """Send test daily digest email to specific address"""
    competitions = await db.competitions.find({"status": "active"}, {"_id": 0}).to_list(100)
    
    test_user = {"email": email, "first_name": "Test User", "username": "testuser"}
    success = await send_daily_digest_to_user(test_user, competitions)
    
    if success:
        return {"message": f"Test email sent to {email}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email")

# Email Unsubscribe endpoint (no auth required - uses user_id from link)
@router.post("/email/unsubscribe/{user_id}")
async def unsubscribe_from_emails(user_id: str):
    """Unsubscribe user from marketing emails"""
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negasit")
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"email_unsubscribed": True, "unsubscribed_at": datetime.now(timezone.utc)}}
    )
    
    return {
        "success": True,
        "message": "Te-ai dezabonat cu succes de la email-urile promotionale.",
        "email": user.get("email", "")[:3] + "***"  # Partial email for confirmation
    }

# Email Resubscribe endpoint
@router.post("/email/resubscribe/{user_id}")
async def resubscribe_to_emails(user_id: str):
    """Resubscribe user to marketing emails"""
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negasit")
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"email_unsubscribed": False}, "$unset": {"unsubscribed_at": ""}}
    )
    
    return {
        "success": True,
        "message": "Te-ai reabonat cu succes la email-urile promotionale!",
        "email": user.get("email", "")[:3] + "***"
    }

# Check subscription status
@router.get("/email/status/{user_id}")
async def get_email_subscription_status(user_id: str):
    """Get user's email subscription status"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "email_unsubscribed": 1, "email": 1})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negasit")
    
    return {
        "subscribed": not user.get("email_unsubscribed", False),
        "email": user.get("email", "")[:3] + "***"
    }

