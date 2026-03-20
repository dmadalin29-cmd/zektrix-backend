# -*- coding: utf-8 -*-
"""Push notification service for Zektrix UK"""
import os
import json
import logging

logger = logging.getLogger(__name__)
VAPID_MAILTO = os.environ.get('VAPID_MAILTO', 'mailto:support@zektrix.uk')


async def send_web_push(subscription: dict, data: dict) -> bool:
    """Send web push notification using pywebpush"""
    from pywebpush import webpush, WebPushException
    vapid_pem_path = os.path.join(os.path.dirname(__file__), "vapid_private.pem")
    try:
        webpush(
            subscription_info={"endpoint": subscription["endpoint"], "keys": subscription["keys"]},
            data=json.dumps(data),
            vapid_private_key=vapid_pem_path,
            vapid_claims={"sub": VAPID_MAILTO}
        )
        return True
    except WebPushException as e:
        status_code = e.response.status_code if e.response is not None else 0
        if status_code in (404, 410):
            raise Exception(f"{status_code} push subscription expired")
        raise Exception(f"Push failed: {status_code} {str(e)[:200]}")


async def notify_user_push(db, user_id: str, title: str, body: str, url: str = "https://zektrix.uk"):
    """Send push notification to a specific user"""
    subs = await db.push_subscriptions.find({"user_id": user_id}, {"_id": 0}).to_list(5)
    for sub in subs:
        try:
            await send_web_push(sub, {"title": title, "body": body, "url": url})
        except Exception as e:
            logger.error(f"Push to user {user_id} failed: {e}")
            if "410" in str(e) or "404" in str(e):
                await db.push_subscriptions.delete_one({"endpoint": sub["endpoint"]})


async def notify_competition_participants_push(db, competition_id: str, title: str, body: str, url: str = None):
    """Send push notification to all participants of a competition"""
    tickets = await db.tickets.find({"competition_id": competition_id}, {"_id": 0, "user_id": 1}).to_list(10000)
    user_ids = list(set(t["user_id"] for t in tickets))
    if not url:
        url = f"https://zektrix.uk/competitions/{competition_id}"
    subs = await db.push_subscriptions.find({"user_id": {"$in": user_ids}}, {"_id": 0}).to_list(1000)
    for sub in subs:
        try:
            await send_web_push(sub, {"title": title, "body": body, "url": url})
        except Exception as e:
            if "410" in str(e) or "404" in str(e):
                await db.push_subscriptions.delete_one({"endpoint": sub["endpoint"]})


async def notify_admins_push(db, title: str, body: str, url: str = "https://zektrix.uk/admin"):
    """Send push notification to all admin users"""
    subs = await db.push_subscriptions.find({"role": "admin"}, {"_id": 0}).to_list(50)
    if not subs:
        subs = await db.push_subscriptions.find({}, {"_id": 0}).to_list(50)
    for sub in subs:
        try:
            await send_web_push(sub, {"title": title, "body": body, "url": url})
        except Exception as e:
            if "410" in str(e) or "404" in str(e):
                await db.push_subscriptions.delete_one({"endpoint": sub["endpoint"]})
