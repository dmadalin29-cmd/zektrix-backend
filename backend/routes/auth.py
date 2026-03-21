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


try:
    from email_service import send_welcome_email, send_password_reset_email
except ImportError:
    from backend.email_service import send_welcome_email, send_password_reset_email

router = APIRouter(prefix="/api")

# ==================== AUTH ROUTES ====================

@router.post("/auth/register", response_model=dict)
async def register(user: UserCreate, referral_code: Optional[str] = None):
    existing = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_referral_code = f"ZEK{user_id[-6:].upper()}"
    
    user_doc = {
        "user_id": user_id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "password_hash": hash_password(user.password),
        "balance": 0.0,
        "role": "user",
        "picture": None,
        "referral_code": user_referral_code,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Handle referral if code provided
    if referral_code:
        referrer = await db.users.find_one({"referral_code": referral_code.upper()}, {"_id": 0})
        if referrer and referrer["user_id"] != user_id:
            await db.referrals.insert_one({
                "referral_id": f"ref_{uuid.uuid4().hex[:12]}",
                "referrer_id": referrer["user_id"],
                "referred_id": user_id,
                "status": "pending",
                "bonus_amount": 5.0,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Send welcome email (non-blocking)
    asyncio.create_task(send_welcome_email(user.email, user.username, user_referral_code))
    
    token = create_access_token(user_id, "user")
    return {"token": token, "user": {k: v for k, v in user_doc.items() if k != "password_hash" and k != "_id"}}

@router.post("/auth/login", response_model=dict)
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email}, {"_id": 0})
    if not db_user or not verify_password(user.password, db_user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(db_user["user_id"], db_user["role"])
    return {"token": token, "user": {k: v for k, v in db_user.items() if k != "password_hash"}}

@router.get("/auth/session")
async def process_session(session_id: str, response: Response):
    """Process Google OAuth session_id and return user data"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        data = resp.json()
        email = data.get("email")
        name = data.get("name")
        picture = data.get("picture")
        session_token = data.get("session_token")
        
        # Find or create user
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        if existing_user:
            user_id = existing_user["user_id"]
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"picture": picture, "name": name}}
            )
        else:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            username = email.split("@")[0] + "_" + uuid.uuid4().hex[:4]
            await db.users.insert_one({
                "user_id": user_id,
                "username": username,
                "email": email,
                "name": name,
                "picture": picture,
                "balance": 0.0,
                "role": "user",
                "password_hash": "",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Store session
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.user_sessions.update_one(
            {"user_id": user_id},
            {"$set": {
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7*24*60*60
        )
        
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
        return {"user": user, "token": session_token}

@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {k: v for k, v in current_user.items() if k != "password_hash"}

@router.put("/auth/profile")
async def update_profile(update: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update user's own profile"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    # Check username uniqueness if changing
    if "username" in update_data:
        existing = await db.users.find_one({"username": update_data["username"], "user_id": {"$ne": current_user["user_id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Username deja utilizat")
    
    await db.users.update_one({"user_id": current_user["user_id"]}, {"$set": update_data})
    updated_user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0, "password_hash": 0})
    return updated_user

@router.post("/auth/logout")
async def logout(response: Response, current_user: dict = Depends(get_current_user)):
    await db.user_sessions.delete_one({"user_id": current_user["user_id"]})
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

# ==================== PASSWORD RESET ====================

@router.post("/auth/request-password-reset")
async def request_password_reset(request: PasswordResetRequest):
    """Request a password reset email"""
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "Dacă emailul există, vei primi un link de resetare"}
    
    # Generate reset token (valid for 1 hour)
    reset_token = f"reset_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token
    await db.password_resets.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "token": reset_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    # Send email
    await send_password_reset_email(user["email"], user.get("username", "Utilizator"), reset_token)
    
    return {"message": "Dacă emailul există, vei primi un link de resetare"}

@router.post("/auth/reset-password")
async def reset_password(request: PasswordResetConfirm):
    """Reset password using token"""
    # Find reset request
    reset_request = await db.password_resets.find_one({"token": request.token}, {"_id": 0})
    
    if not reset_request:
        raise HTTPException(status_code=400, detail="Link de resetare invalid sau expirat")
    
    # Check expiration
    expires_at = reset_request.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        await db.password_resets.delete_one({"token": request.token})
        raise HTTPException(status_code=400, detail="Link de resetare expirat. Te rugăm să ceri unul nou.")
    
    # Validate password
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Parola trebuie să aibă minim 6 caractere")
    
    # Update password
    await db.users.update_one(
        {"user_id": reset_request["user_id"]},
        {"$set": {"password_hash": hash_password(request.new_password)}}
    )
    
    # Delete reset token
    await db.password_resets.delete_one({"token": request.token})
    
    # Invalidate existing sessions
    await db.user_sessions.delete_many({"user_id": reset_request["user_id"]})
    
    return {"message": "Parola a fost resetată cu succes! Te poți autentifica acum."}

