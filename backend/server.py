# -*- coding: utf-8 -*-
"""
Zektrix UK Competition Platform - Main Server (Refactored)
Routes are organized in /routes/*.py, services in /services/*.py
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from typing import Dict, List
import asyncio
import logging
import os

# Shared modules
from database import db, client
from config import UPLOAD_DIR, logger

# Route modules
from routes.auth import router as auth_router
from routes.competitions import router as competitions_router
from routes.referral import router as referral_router
from routes.wallet import router as wallet_router
from routes.subscriptions import router as subscriptions_router
from routes.admin import router as admin_router
from routes.chat import router as chat_router
from routes.webhooks import router as webhooks_router
from routes.public import router as public_router
from routes.gamification import router as gamification_router

# Background services
from services.bots import (
    competition_auto_bot, daily_email_bot,
    subscription_renewal_bot, reengagement_email_bot
)

# ==================== WEBSOCKET MANAGER ====================
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str = "general"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str = "general"):
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
    
    async def broadcast(self, message: dict, channel: str = "general"):
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass
    
    async def broadcast_all(self, message: dict):
        for channel in self.active_connections:
            await self.broadcast(message, channel)

ws_manager = ConnectionManager()

# ==================== APP CREATION ====================
app = FastAPI(title="Zektrix UK Competition Platform")

# Include all route modules
app.include_router(auth_router)
app.include_router(competitions_router)
app.include_router(referral_router)
app.include_router(wallet_router)
app.include_router(subscriptions_router)
app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(webhooks_router)
app.include_router(public_router)
app.include_router(gamification_router)

# Make ws_manager available to route modules that need it
import routes.competitions as _comp_mod
import routes.chat as _chat_mod
_comp_mod.ws_manager = ws_manager
_chat_mod.ws_manager = ws_manager

# ==================== WEBSOCKET ENDPOINTS ====================
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket, "general")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "general")

@app.websocket("/api/ws/competition/{competition_id}")
async def competition_websocket(websocket: WebSocket, competition_id: str):
    channel = f"comp_{competition_id}"
    await ws_manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)

# Chat WebSocket routes (imported from chat module)
from routes.chat import ws_chat_user, ws_chat_admin
app.websocket("/api/ws/chat/user")(ws_chat_user)
app.websocket("/api/ws/chat/admin")(ws_chat_admin)

# ==================== STATIC FILES ====================
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ==================== CORS ====================
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== STARTUP / SHUTDOWN ====================
@app.on_event("startup")
async def startup_db():
    # Create indexes
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.users.create_index("referral_code", unique=True, sparse=True)
    await db.competitions.create_index("competition_id", unique=True)
    await db.tickets.create_index("ticket_id", unique=True)
    await db.tickets.create_index([("competition_id", 1), ("ticket_number", 1)], unique=True)
    await db.transactions.create_index("transaction_id", unique=True)
    await db.transactions.create_index("viva_order_code")
    await db.winners.create_index("winner_id", unique=True)
    await db.user_sessions.create_index("user_id", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.referrals.create_index("referral_id", unique=True)
    await db.referrals.create_index("referrer_id")
    await db.referrals.create_index("referred_id", unique=True, sparse=True)
    await db.password_resets.create_index("token", unique=True)
    await db.password_resets.create_index("user_id")
    await db.reengagement_emails.create_index("user_id")
    await db.reengagement_emails.create_index("sent_at")
    logger.info("Database indexes created")
    
    # Start background bots
    asyncio.create_task(competition_auto_bot())
    logger.info("Competition Auto-Bot started")
    
    asyncio.create_task(daily_email_bot())
    logger.info("Daily Email Bot started")
    
    asyncio.create_task(subscription_renewal_bot())
    logger.info("Subscription Renewal Bot started")
    
    asyncio.create_task(reengagement_email_bot())
    logger.info("Re-engagement Email Bot started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
