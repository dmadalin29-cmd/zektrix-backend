# -*- coding: utf-8 -*-
"""Shared helper functions used across route modules"""
from database import db
from config import logger
import random


# Wrap push functions to auto-inject db
async def notify_user_push(user_id, title, body, url="https://zektrix.uk"):
    try:
        from push_service import notify_user_push as _push
    except ImportError:
        from backend.push_service import notify_user_push as _push
    await _push(db, user_id, title, body, url)

async def notify_competition_participants_push(competition_id, title, body, url=None):
    try:
        from push_service import notify_competition_participants_push as _push
    except ImportError:
        from backend.push_service import notify_competition_participants_push as _push
    await _push(db, competition_id, title, body, url)

async def notify_admins_push(title, body, url=None):
    try:
        from push_service import notify_admins_push as _push
    except ImportError:
        from backend.push_service import notify_admins_push as _push
    await _push(db, title, body, url)


async def generate_random_ticket_number(competition_id: str, max_tickets: int) -> int:
    """Generate a random ticket number that hasn't been used yet for this competition"""
    existing = await db.tickets.distinct("ticket_number", {"competition_id": competition_id})
    existing_set = set(existing)
    available = [n for n in range(1, max_tickets + 1) if n not in existing_set]
    if not available:
        raise Exception("No available ticket numbers")
    return random.choice(available)
